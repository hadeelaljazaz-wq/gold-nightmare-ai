"""
Al Kabous AI - Forex Price Manager
إدارة أسعار العملات الأجنبية باستخدام yfinance
"""

import yfinance as yf
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from dataclasses import dataclass
import pandas as pd

logger = logging.getLogger(__name__)

@dataclass
class ForexPrice:
    """نموذج بيانات سعر العملة"""
    pair: str
    price_usd: float
    price_change: float
    price_change_pct: float
    ask: float
    bid: float
    high_24h: float
    low_24h: float
    source: str
    timestamp: datetime
    
    def __post_init__(self):
        """تحقق من صحة البيانات"""
        if self.price_usd <= 0:
            raise ValueError(f"Invalid price for {self.pair}: {self.price_usd}")

class ForexPriceManager:
    """مدير أسعار العملات الأجنبية"""
    
    # خريطة العملات المدعومة مع رموز Yahoo Finance
    CURRENCY_PAIRS = {
        "EUR/USD": "EURUSD=X",
        "GBP/USD": "GBPUSD=X", 
        "USD/JPY": "USDJPY=X",
        "AUD/USD": "AUDUSD=X",
        "USD/CAD": "USDCAD=X",
        "USD/CHF": "USDCHF=X",
        "NZD/USD": "NZDUSD=X"
    }
    
    CURRENCY_NAMES_AR = {
        "EUR/USD": "اليورو/دولار",
        "GBP/USD": "الباوند/دولار",
        "USD/JPY": "الدولار/ين",
        "AUD/USD": "الأسترالي/دولار", 
        "USD/CAD": "الدولار/كندي",
        "USD/CHF": "الدولار/فرنك",
        "NZD/USD": "النيوزلندي/دولار"
    }
    
    def __init__(self):
        self.cache = {}  # كاش بسيط للأسعار
        self.cache_duration = timedelta(minutes=5)  # مدة الكاش 5 دقائق
    
    def _is_cache_valid(self, pair: str) -> bool:
        """فحص صحة الكاش"""
        if pair not in self.cache:
            return False
        
        cached_time = self.cache[pair].timestamp
        return datetime.utcnow() - cached_time < self.cache_duration
    
    async def get_forex_price(self, pair: str, use_cache: bool = True) -> Optional[ForexPrice]:
        """جلب سعر زوج العملة"""
        try:
            # تحقق من الكاش أولاً
            if use_cache and self._is_cache_valid(pair):
                logger.info(f"💰 Returning cached price for {pair}")
                return self.cache[pair]
            
            # تحقق من أن الزوج مدعوم
            if pair not in self.CURRENCY_PAIRS:
                logger.error(f"❌ Unsupported currency pair: {pair}")
                return None
            
            yahoo_symbol = self.CURRENCY_PAIRS[pair]
            logger.info(f"📊 Fetching price for {pair} ({yahoo_symbol}) from yfinance")
            
            # جلب البيانات من yfinance في thread منفصل
            forex_data = await asyncio.get_event_loop().run_in_executor(
                None, self._fetch_yfinance_data, yahoo_symbol
            )
            
            if not forex_data:
                logger.error(f"❌ No data returned for {pair}")
                return None
            
            # إنشاء كائن ForexPrice
            forex_price = ForexPrice(
                pair=pair,
                price_usd=forex_data["current_price"],
                price_change=forex_data["change"],
                price_change_pct=forex_data["change_percent"],
                ask=forex_data.get("ask", forex_data["current_price"]),
                bid=forex_data.get("bid", forex_data["current_price"]),
                high_24h=forex_data["high"],
                low_24h=forex_data["low"],
                source="yfinance",
                timestamp=datetime.utcnow()
            )
            
            # حفظ في الكاش
            self.cache[pair] = forex_price
            
            logger.info(f"✅ Successfully fetched {pair}: ${forex_price.price_usd:.4f}")
            return forex_price
            
        except Exception as e:
            logger.error(f"❌ Error fetching forex price for {pair}: {e}")
            return self._get_demo_price(pair)
    
    def _fetch_yfinance_data(self, symbol: str) -> Optional[Dict[str, float]]:
        """جلب البيانات من yfinance (يعمل في thread منفصل)"""
        try:
            # إنشاء كائن Ticker
            ticker = yf.Ticker(symbol)
            
            # جلب معلومات السعر الحالي
            info = ticker.info
            
            # جلب البيانات التاريخية لآخر 5 أيام
            hist = ticker.history(period="5d")
            
            if hist.empty or not info:
                logger.warning(f"⚠️ No data available for {symbol}")
                return None
            
            # آخر سعر
            current_price = hist['Close'].iloc[-1]
            
            # حساب التغيير
            if len(hist) > 1:
                prev_close = hist['Close'].iloc[-2]
                change = current_price - prev_close
                change_percent = (change / prev_close) * 100
            else:
                change = 0
                change_percent = 0
            
            # أعلى وأقل سعر في آخر يوم
            high_24h = hist['High'].iloc[-1]
            low_24h = hist['Low'].iloc[-1]
            
            return {
                "current_price": float(current_price),
                "change": float(change),
                "change_percent": float(change_percent),
                "high": float(high_24h),
                "low": float(low_24h),
                "ask": info.get("ask", float(current_price)),
                "bid": info.get("bid", float(current_price))
            }
            
        except Exception as e:
            logger.error(f"❌ yfinance error for {symbol}: {e}")
            return None
    
    def _get_demo_price(self, pair: str) -> ForexPrice:
        """أسعار تجريبية في حال فشل yfinance"""
        demo_prices = {
            "EUR/USD": {"price": 1.0856, "change": 0.0012, "high": 1.0875, "low": 1.0834},
            "GBP/USD": {"price": 1.2645, "change": -0.0023, "high": 1.2678, "low": 1.2612},
            "USD/JPY": {"price": 154.32, "change": 0.45, "high": 154.89, "low": 153.76},
            "AUD/USD": {"price": 0.6789, "change": 0.0034, "high": 0.6812, "low": 0.6745},
            "USD/CAD": {"price": 1.3456, "change": -0.0012, "high": 1.3478, "low": 1.3423},
            "USD/CHF": {"price": 0.8923, "change": 0.0008, "high": 0.8945, "low": 0.8901},
            "NZD/USD": {"price": 0.6234, "change": -0.0015, "high": 0.6256, "low": 0.6212}
        }
        
        demo_data = demo_prices.get(pair, demo_prices["EUR/USD"])
        change_pct = (demo_data["change"] / demo_data["price"]) * 100
        
        return ForexPrice(
            pair=pair,
            price_usd=demo_data["price"],
            price_change=demo_data["change"],
            price_change_pct=change_pct,
            ask=demo_data["price"] + 0.0001,
            bid=demo_data["price"] - 0.0001,
            high_24h=demo_data["high"],
            low_24h=demo_data["low"],
            source="demo_data",
            timestamp=datetime.utcnow()
        )
    
    async def get_all_forex_prices(self) -> Dict[str, ForexPrice]:
        """جلب أسعار جميع العملات المدعومة"""
        results = {}
        
        # جلب جميع الأسعار بشكل متوازي
        tasks = [
            self.get_forex_price(pair) 
            for pair in self.CURRENCY_PAIRS.keys()
        ]
        
        prices = await asyncio.gather(*tasks, return_exceptions=True)
        
        for pair, price in zip(self.CURRENCY_PAIRS.keys(), prices):
            if isinstance(price, ForexPrice):
                results[pair] = price
            else:
                logger.error(f"❌ Failed to get price for {pair}: {price}")
                results[pair] = self._get_demo_price(pair)
        
        return results
    
    def get_formatted_text(self, forex_price: ForexPrice) -> str:
        """تنسيق النص العربي لعرض السعر"""
        pair_name_ar = self.CURRENCY_NAMES_AR.get(forex_price.pair, forex_price.pair)
        
        change_emoji = "📈" if forex_price.price_change >= 0 else "📉"
        change_sign = "+" if forex_price.price_change >= 0 else ""
        
        formatted_text = f"""
💱 **{pair_name_ar} ({forex_price.pair})**

💰 **السعر الحالي**: {forex_price.price_usd:.4f}
{change_emoji} **التغيير**: {change_sign}{forex_price.price_change:.4f} ({forex_price.price_change_pct:+.2f}%)

📊 **أعلى سعر**: {forex_price.high_24h:.4f}
📊 **أقل سعر**: {forex_price.low_24h:.4f}

🔄 **المصدر**: {forex_price.source.upper()}
⏰ **التحديث**: {forex_price.timestamp.strftime('%H:%M:%S')}
        """.strip()
        
        return formatted_text

# إنشاء مثيل مشترك
forex_manager = ForexPriceManager()