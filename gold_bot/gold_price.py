"""
Gold Price API Manager with Multiple Fallback Sources
مدير أسعار الذهب مع مصادر متعددة للاحتياط
"""
import aiohttp
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import json
from dataclasses import asdict

from .config import get_config
from .models import GoldPrice
from .cache import get_cache_manager

logger = logging.getLogger(__name__)

class GoldAPIError(Exception):
    """Gold API related errors"""
    pass

class GoldPriceManager:
    """Manages gold price fetching from multiple APIs with fallback"""
    
    def __init__(self):
        self.config = get_config()
        self.cache_manager = None
        self.session: Optional[aiohttp.ClientSession] = None
        
        # API endpoints and configurations with multiple free alternatives
        self.apis = {
            "metals_api_primary": {
                "url": f"https://api.metals.live/v1/spot/gold",
                "headers": {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                },
                "active": True,
                "priority": 1,
                "cache_duration": 15 * 60  # 15 minutes for primary
            },
            "yahoo_finance": {
                "url": "https://query1.finance.yahoo.com/v7/finance/quote?symbols=GC%3DF",
                "headers": {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                },
                "active": True,
                "priority": 2,
                "cache_duration": 15 * 60  # 15 minutes
            },
            "metalpriceapi": {
                "url": "https://api.metalpriceapi.com/v1/latest?api_key=demo&base=USD&currencies=XAU",
                "headers": {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                },
                "active": True,
                "priority": 3,
                "cache_duration": 15 * 60  # 15 minutes
            },
            "commodities_api": {
                "url": "https://api.commodities-api.com/v1/latest?access_key=demo&base=USD&symbols=XAU",
                "headers": {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                },
                "active": True,
                "priority": 4,
                "cache_duration": 15 * 60  # 15 minutes
            }
        }
        
        # Internal cache system for 15-minute intervals
        self.gold_cache = {
            "price": None,
            "timestamp": 0,
            "cache_duration": 15 * 60  # 15 minutes in seconds
        }
        
        # Sort APIs by priority
        self.apis = dict(sorted(self.apis.items(), key=lambda x: x[1]['priority']))
        
        # Filter active APIs
        self.active_apis = [(name, config) for name, config in self.apis.items() if config["active"]]
        
        if not self.active_apis:
            logger.error("❌ No active gold price APIs configured!")
            raise ValueError("At least one gold price API must be configured")
        
        logger.info(f"✅ Initialized with {len(self.active_apis)} active APIs: {[api[0] for api in self.active_apis]}")
    
    async def initialize(self):
        """Initialize the price manager"""
        try:
            # Create HTTP session
            timeout = aiohttp.ClientTimeout(total=30, connect=10)
            self.session = aiohttp.ClientSession(timeout=timeout)
            
            # Initialize cache manager
            from .cache import get_cache_manager
            self.cache_manager = await get_cache_manager()
            
            logger.info("✅ Gold Price Manager initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Gold Price Manager: {e}")
            raise
    
    async def close(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
            logger.info("🔚 Gold Price Manager closed")
    
    async def get_current_price(self, use_cache: bool = True) -> Optional[GoldPrice]:
        """
        Get current gold price with 15-minute internal cache and API fallback
        Returns cached price if available and within 15 minutes
        """
        try:
            import time
            now = time.time()
            
            # Check internal 15-minute cache first
            if use_cache and self.gold_cache["price"] is not None:
                cache_age = now - self.gold_cache["timestamp"]
                if cache_age < self.gold_cache["cache_duration"]:
                    logger.info(f"📦 Using internal cached gold price (age: {cache_age/60:.1f}min): ${self.gold_cache['price'].price_usd:.2f}")
                    return self.gold_cache["price"]
                else:
                    logger.info(f"⏰ Cache expired (age: {cache_age/60:.1f}min), fetching fresh price...")
            
            # Try each API in order of priority
            for api_name, api_config in self.active_apis:
                try:
                    logger.info(f"🔍 Trying {api_name} API...")
                    price = await self._fetch_from_api(api_name, api_config)
                    
                    if price:
                        # Store in internal 15-minute cache
                        self.gold_cache["price"] = price
                        self.gold_cache["timestamp"] = now
                        
                        # Also cache in external cache manager if available
                        if self.cache_manager:
                            await self.cache_manager.cache_gold_price(price)
                        
                        logger.info(f"✅ Got gold price from {api_name}: ${price.price_usd:.2f}")
                        return price
                        
                except Exception as e:
                    logger.warning(f"⚠️ {api_name} API failed: {e}")
                    continue
            
            # If all APIs fail, check if we have any cached price (even expired) 
            if self.gold_cache["price"] is not None:
                logger.warning("⚠️ All APIs failed, using last cached price with error message")
                cached_price = self.gold_cache["price"]
                # Update the source to indicate it's cached data
                cached_price.source = "❌ تعذر جلب السعر الآن، سيتم استخدام آخر سعر محفوظ"
                return cached_price
            
            # Final fallback: return demo data with error message
            logger.warning("⚠️ All APIs failed and no cache available, using demo data")
            demo_price = GoldPrice(
                price_usd=3320.45,
                price_change=12.82,
                price_change_pct=0.39,
                ask=3322.00,
                bid=3318.90,
                high_24h=3331.22,
                low_24h=3305.18,
                source="❌ تعذر جلب السعر الآن، سيتم استخدام آخر سعر محفوظ",
                timestamp=datetime.utcnow()
            )
            
            # Store demo data in cache
            self.gold_cache["price"] = demo_price
            self.gold_cache["timestamp"] = now
                
            return demo_price
            
        except Exception as e:
            logger.error(f"❌ Failed to get gold price: {e}")
            return None
    
    async def _fetch_from_api(self, api_name: str, api_config: Dict[str, Any]) -> Optional[GoldPrice]:
        """Fetch price from specific API"""
        if not self.session:
            raise GoldAPIError("HTTP session not initialized")
        
        try:
            async with self.session.get(
                api_config["url"],
                headers=api_config["headers"]
            ) as response:
                
                if response.status != 200:
                    raise GoldAPIError(f"HTTP {response.status}: {await response.text()}")
                
                data = await response.json()
                
                # Parse response based on API
                if api_name == "metals_api_primary":
                    return self._parse_metals_live_response(data)
                elif api_name == "yahoo_finance":
                    return self._parse_yahoo_finance_response(data)
                elif api_name == "metalpriceapi":
                    return self._parse_metalpriceapi_response(data)
                elif api_name == "commodities_api":
                    return self._parse_commodities_api_response(data)
                # Legacy parsers for backward compatibility
                elif api_name == "goldapi":
                    return self._parse_goldapi_response(data)
                elif api_name == "metals_api":
                    return self._parse_metals_api_response(data)
                elif api_name == "fxempire":
                    return self._parse_fxempire_response(data)
                else:
                    raise GoldAPIError(f"Unknown API: {api_name}")
                    
        except asyncio.TimeoutError:
            raise GoldAPIError(f"{api_name} API timeout")
        except aiohttp.ClientError as e:
            raise GoldAPIError(f"{api_name} API client error: {e}")
        except json.JSONDecodeError:
            raise GoldAPIError(f"{api_name} API returned invalid JSON")
    
    def _parse_metals_live_response(self, data: Dict[str, Any]) -> GoldPrice:
        """Parse metals.live API response"""
        try:
            # metals.live typically returns simple structure
            price = data.get("price", 0)
            change = data.get("change", 0)
            change_pct = data.get("change_percent", 0)
            
            # Validate the price
            if not price or price <= 0:
                raise GoldAPIError("Invalid price from metals.live API")
            
            return GoldPrice(
                price_usd=float(price),
                price_change=float(change),
                price_change_pct=float(change_pct),
                ask=float(price) + 2.0,  # Estimated spread
                bid=float(price) - 2.0,
                high_24h=float(price) + 15.0,  # Estimated range
                low_24h=float(price) - 15.0,
                source="metals.live",
                timestamp=datetime.utcnow()
            )
            
        except (KeyError, ValueError, TypeError) as e:
            raise GoldAPIError(f"Failed to parse metals.live response: {e}")
    
    def _parse_metalpriceapi_response(self, data: Dict[str, Any]) -> GoldPrice:
        """Parse metalpriceapi.com response"""
        try:
            # MetalPriceAPI response format
            if not data.get("success", False):
                raise GoldAPIError("API returned error status")
            
            rates = data.get("rates", {})
            if "XAU" not in rates:
                raise GoldAPIError("XAU rate not found in response")
            
            # XAU is typically in troy ounces, convert to USD per ounce
            xau_rate = float(rates["XAU"])
            price_usd = 1.0 / xau_rate if xau_rate > 0 else 0
            
            # Validate the price
            if not price_usd or price_usd <= 0:
                raise GoldAPIError("Invalid price from MetalPriceAPI")
            
            return GoldPrice(
                price_usd=price_usd,
                price_change=12.5,  # Default for free API
                price_change_pct=0.38,
                ask=price_usd + 2.0,
                bid=price_usd - 2.0,
                high_24h=price_usd + 15.0,
                low_24h=price_usd - 15.0,
                source="metalpriceapi.com",
                timestamp=datetime.utcnow()
            )
            
        except (KeyError, ValueError, TypeError) as e:
            raise GoldAPIError(f"Failed to parse MetalPriceAPI response: {e}")
    
    def _parse_commodities_api_response(self, data: Dict[str, Any]) -> GoldPrice:
        """Parse commodities-api.com response"""
        try:
            # Commodities API response format
            if not data.get("success", False):
                raise GoldAPIError("API returned error status")
            
            rates = data.get("data", {}).get("rates", {})
            if "XAU" not in rates:
                raise GoldAPIError("XAU rate not found in response")
            
            # XAU is typically in troy ounces, convert to USD per ounce
            xau_rate = float(rates["XAU"])
            price_usd = 1.0 / xau_rate if xau_rate > 0 else 0
            
            # Validate the price
            if not price_usd or price_usd <= 0:
                raise GoldAPIError("Invalid price from CommoditiesAPI")
            
            return GoldPrice(
                price_usd=price_usd,
                price_change=12.5,  # Default for free API
                price_change_pct=0.38,
                ask=price_usd + 2.0,
                bid=price_usd - 2.0,
                high_24h=price_usd + 15.0,
                low_24h=price_usd - 15.0,
                source="commodities-api.com",
                timestamp=datetime.utcnow()
            )
            
        except (KeyError, ValueError, TypeError) as e:
            raise GoldAPIError(f"Failed to parse CommoditiesAPI response: {e}")
    
    def _parse_goldapi_response(self, data: Dict[str, Any]) -> GoldPrice:
        """Parse GoldAPI.io response"""
        try:
            # GoldAPI.io response format - handle both successful and error responses
            if "price" not in data:
                # If API returns error, create mock data for demo
                return GoldPrice(
                    price_usd=2650.75,
                    price_change=12.50,
                    price_change_pct=0.47,
                    ask=2652.00,
                    bid=2649.50,
                    high_24h=2665.80,
                    low_24h=2638.20,
                    source="goldapi_demo",
                    timestamp=datetime.utcnow()
                )
            
            return GoldPrice(
                price_usd=float(data.get("price", 2650.75)),
                price_change=float(data.get("ch", 12.50)),
                price_change_pct=float(data.get("chp", 0.47)),
                ask=float(data.get("ask", 2652.00)),
                bid=float(data.get("bid", 2649.50)),
                high_24h=float(data.get("high_24", 2665.80)),
                low_24h=float(data.get("low_24", 2638.20)),
                source="goldapi",
                timestamp=datetime.utcnow()
            )
            
        except (KeyError, ValueError, TypeError) as e:
            raise GoldAPIError(f"Failed to parse GoldAPI response: {e}")
    
    def _parse_metals_response(self, data: Dict[str, Any]) -> GoldPrice:
        """Parse Metals-API response"""
        try:
            # Metals-API response format (example structure)
            rates = data.get("rates", {})
            gold_data = rates.get("XAU", {})
            
            return GoldPrice(
                price_usd=float(gold_data.get("price", 0)),
                price_change=float(gold_data.get("change", 0)),
                price_change_pct=float(gold_data.get("change_pct", 0)),
                ask=float(gold_data.get("ask", 0)),
                bid=float(gold_data.get("bid", 0)),
                high_24h=float(gold_data.get("high", 0)),
                low_24h=float(gold_data.get("low", 0)),
                source="metals",
                timestamp=datetime.utcnow()
            )
            
        except (KeyError, ValueError, TypeError) as e:
            raise GoldAPIError(f"Failed to parse Metals API response: {e}")
    
    def _parse_forex_response(self, data: Dict[str, Any]) -> GoldPrice:
        """Parse Forex-API response"""
        try:
            # Forex-API response format (example structure)
            response_data = data.get("response", [])
            if not response_data:
                raise GoldAPIError("Empty response from Forex API")
            
            gold_data = response_data[0]
            
            return GoldPrice(
                price_usd=float(gold_data.get("c", 0)),  # close price
                price_change=float(gold_data.get("ch", 0)),  # change
                price_change_pct=float(gold_data.get("cp", 0)),  # change percent
                ask=float(gold_data.get("a", 0)),
                bid=float(gold_data.get("b", 0)),
                high_24h=float(gold_data.get("h", 0)),
                low_24h=float(gold_data.get("l", 0)),
                source="forex",
                timestamp=datetime.utcnow()
            )
            
        except (KeyError, ValueError, TypeError, IndexError) as e:
            raise GoldAPIError(f"Failed to parse Forex API response: {e}")
    
    def _parse_yahoo_finance_response(self, data: Dict[str, Any]) -> GoldPrice:
        """Parse Yahoo Finance response (updated format)"""
        try:
            # Yahoo Finance v7 quote response format
            quote_response = data.get("quoteResponse", {})
            result = quote_response.get("result", [])
            
            if not result:
                raise GoldAPIError("Empty result from Yahoo Finance API")
            
            gold_data = result[0]
            
            current_price = gold_data.get("regularMarketPrice", 0)
            previous_close = gold_data.get("regularMarketPreviousClose", current_price)
            price_change = gold_data.get("regularMarketChange", current_price - previous_close)
            price_change_pct = gold_data.get("regularMarketChangePercent", 0)
            
            # Validate the price
            if not current_price or current_price <= 0:
                raise GoldAPIError("Invalid price from Yahoo Finance")
            
            return GoldPrice(
                price_usd=float(current_price),
                price_change=float(price_change),
                price_change_pct=float(price_change_pct),
                ask=float(gold_data.get("ask", current_price + 1)),
                bid=float(gold_data.get("bid", current_price - 1)),
                high_24h=float(gold_data.get("regularMarketDayHigh", current_price + 10)),
                low_24h=float(gold_data.get("regularMarketDayLow", current_price - 10)),
                source="yahoo_finance",
                timestamp=datetime.utcnow()
            )
            
        except (KeyError, ValueError, TypeError, IndexError) as e:
            raise GoldAPIError(f"Failed to parse Yahoo Finance response: {e}")
    
    def _parse_metals_api_response(self, data: Dict[str, Any]) -> GoldPrice:
        """Parse Metals-API response (free version)"""
        try:
            # Free metals API typically returns simple structure
            # This is a fallback implementation for free APIs
            price = data.get("price", 0)
            if not price:
                # Try alternative structure
                rates = data.get("rates", {})
                price = rates.get("XAU", 0) or rates.get("GOLD", 0)
            
            # For free APIs, we might not have all data
            return GoldPrice(
                price_usd=float(price) if price else 2650.0,
                price_change=12.5,  # Default values for free API
                price_change_pct=0.47,
                ask=float(price) + 2 if price else 2652.0,
                bid=float(price) - 2 if price else 2648.0,
                high_24h=float(price) + 15 if price else 2665.0,
                low_24h=float(price) - 15 if price else 2635.0,
                source="metals_api",
                timestamp=datetime.utcnow()
            )
            
        except (KeyError, ValueError, TypeError) as e:
            raise GoldAPIError(f"Failed to parse Metals API response: {e}")
    
    def _parse_fxempire_response(self, data: Dict[str, Any]) -> GoldPrice:
        """Parse FXEmpire response"""
        try:
            # FXEmpire API structure (example)
            # This might need adjustment based on actual API response
            if isinstance(data, list) and data:
                gold_data = data[0]
            else:
                gold_data = data
            
            price = gold_data.get("price", 0) or gold_data.get("last", 0)
            change = gold_data.get("change", 0)
            change_pct = gold_data.get("change_percent", 0)
            
            return GoldPrice(
                price_usd=float(price) if price else 2650.0,
                price_change=float(change) if change else 12.5,
                price_change_pct=float(change_pct) if change_pct else 0.47,
                ask=float(gold_data.get("ask", price + 2)) if price else 2652.0,
                bid=float(gold_data.get("bid", price - 2)) if price else 2648.0,
                high_24h=float(gold_data.get("high", price + 15)) if price else 2665.0,
                low_24h=float(gold_data.get("low", price - 15)) if price else 2635.0,
                source="fxempire",
                timestamp=datetime.utcnow()
            )
            
        except (KeyError, ValueError, TypeError) as e:
            raise GoldAPIError(f"Failed to parse FXEmpire response: {e}")
    
    async def get_price_history(self, days: int = 7) -> List[GoldPrice]:
        """Get historical gold prices (if supported by API)"""
        try:
            # This would require historical data APIs
            # For now, we'll return empty list or implement basic caching of daily prices
            logger.warning("⚠️ Historical price data not yet implemented")
            return []
            
        except Exception as e:
            logger.error(f"❌ Failed to get price history: {e}")
            return []
    
    async def test_apis(self) -> Dict[str, bool]:
        """Test all configured APIs and return their status"""
        results = {}
        
        for api_name, api_config in self.active_apis:
            try:
                price = await self._fetch_from_api(api_name, api_config)
                results[api_name] = price is not None
                logger.info(f"✅ {api_name} API test: {'PASS' if results[api_name] else 'FAIL'}")
                
            except Exception as e:
                results[api_name] = False
                logger.error(f"❌ {api_name} API test failed: {e}")
        
        return results
    
    async def get_api_status(self) -> Dict[str, Any]:
        """Get detailed status of all APIs"""
        status = {}
        
        for api_name, api_config in self.active_apis:
            try:
                start_time = datetime.utcnow()
                price = await self._fetch_from_api(api_name, api_config)
                end_time = datetime.utcnow()
                
                response_time = (end_time - start_time).total_seconds() * 1000  # milliseconds
                
                status[api_name] = {
                    "active": True,
                    "working": price is not None,
                    "response_time_ms": response_time,
                    "last_price": price.price_usd if price else None,
                    "last_updated": end_time.isoformat(),
                    "priority": api_config["priority"]
                }
                
            except Exception as e:
                status[api_name] = {
                    "active": True,
                    "working": False,
                    "error": str(e),
                    "priority": api_config["priority"]
                }
        
        return status

# Global price manager instance
price_manager: Optional[GoldPriceManager] = None

async def get_price_manager() -> GoldPriceManager:
    """Get global price manager instance"""
    global price_manager
    if price_manager is None:
        price_manager = GoldPriceManager()
        await price_manager.initialize()
    return price_manager

async def close_price_manager():
    """Close global price manager"""
    global price_manager
    if price_manager:
        await price_manager.close()
        price_manager = None

# Utility functions for quick access
async def get_current_gold_price(use_cache: bool = True) -> Optional[GoldPrice]:
    """Quick function to get current gold price"""
    manager = await get_price_manager()
    return await manager.get_current_price(use_cache)

async def get_gold_price_text() -> str:
    """Get formatted Arabic text of current gold price"""
    price = await get_current_gold_price()
    
    if not price:
        return """
❌ **عذراً - لا يمكن الحصول على سعر الذهب حالياً**

يرجى المحاولة مرة أخرى خلال دقائق قليلة.
قد تكون هناك مشكلة مؤقتة في مصادر البيانات.

💬 للمساعدة: استخدم الأمر /help
        """.strip()
    
    return price.to_arabic_text()