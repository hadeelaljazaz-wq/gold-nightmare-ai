from fastapi import FastAPI, APIRouter, HTTPException, Request, File, UploadFile
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path
import os
import sys
import logging
import asyncio
from datetime import datetime
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import uuid
import base64
import io
from PIL import Image

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Import gold analysis components (no more telegram)
from gold_bot.gold_price import get_current_gold_price, get_price_manager
from gold_bot.forex_price import forex_manager
from gold_bot.ai_manager import get_ai_manager
from gold_bot.image_processor import chart_processor
from gold_bot.models import (
    AnalysisType, UserTier, UserStatus, 
    UserRegistrationRequest, UserLoginRequest, UserAuthResponse
)
from gold_bot.database import get_database
from gold_bot.admin_manager import get_admin_manager
from gold_bot.auth_manager import get_auth_manager

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'gold_nightmare_bot')]

# Initialize FastAPI
app = FastAPI(title="Gold Nightmare Analysis API", version="1.0.0")
api_router = APIRouter(prefix="/api")

# Component managers
price_manager = None
ai_manager = None
db_manager = None
admin_manager = None

@app.on_event("startup")
async def startup_event():
    """Initialize components on startup"""
    global price_manager, ai_manager, db_manager, admin_manager
    try:
        # Initialize managers
        price_manager = await get_price_manager()
        ai_manager = await get_ai_manager()
        db_manager = await get_database()
        admin_manager = await get_admin_manager()
        
        logging.info("🚀 Gold Analysis API started successfully!")
        
    except Exception as e:
        logging.error(f"❌ Failed to start API: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    client.close()

# Pydantic models for API
class AnalysisRequest(BaseModel):
    analysis_type: str
    user_question: Optional[str] = None
    additional_context: Optional[str] = None

class AnalysisResponse(BaseModel):
    success: bool
    analysis: Optional[str] = None
    gold_price: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    processing_time: Optional[float] = None

class ForexAnalysisRequest(BaseModel):
    pair: str = Field(..., description="Currency pair (e.g., EUR/USD)")
    analysis_type: Optional[str] = "detailed"
    additional_context: Optional[str] = ""

class ForexAnalysisResponse(BaseModel):
    success: bool
    analysis: Optional[str] = None
    forex_price: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    processing_time: Optional[float] = None

class ChartAnalysisRequest(BaseModel):
    image_data: str  # base64 encoded image
    currency_pair: Optional[str] = "XAU/USD"
    timeframe: Optional[str] = "H1"
    analysis_notes: Optional[str] = ""

class ChartAnalysisResponse(BaseModel):
    success: bool
    analysis: Optional[str] = None
    image_info: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    processing_time: Optional[float] = None

class GoldPriceResponse(BaseModel):
    success: bool
    price_data: Optional[Dict[str, Any]] = None
    formatted_text: Optional[str] = None
    error: Optional[str] = None

# API endpoints
@api_router.get("/")
async def root():
    return {"message": "Gold Nightmare Analysis API", "status": "running"}

@api_router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "api_running": True,
        "timestamp": datetime.utcnow().isoformat()
    }

@api_router.get("/gold-price", response_model=GoldPriceResponse)
async def get_gold_price():
    """Get current gold price"""
    try:
        if not price_manager:
            raise HTTPException(status_code=503, detail="Price manager not initialized")
        
        gold_price = await price_manager.get_current_price(use_cache=True)
        
        if not gold_price:
            return GoldPriceResponse(
                success=False,
                error="فشل في جلب أسعار الذهب من المصادر المتاحة"
            )
        
        # Convert to dict for response
        price_data = {
            "price_usd": gold_price.price_usd,
            "price_change": gold_price.price_change,
            "price_change_pct": gold_price.price_change_pct,
            "ask": gold_price.ask,
            "bid": gold_price.bid,
            "high_24h": gold_price.high_24h,
            "low_24h": gold_price.low_24h,
            "source": gold_price.source,
            "timestamp": gold_price.timestamp.isoformat()
        }
        
        # Generate formatted Arabic text
        formatted_text = gold_price.to_arabic_text()
        
        return GoldPriceResponse(
            success=True,
            price_data=price_data,
            formatted_text=formatted_text
        )
        
    except Exception as e:
        logging.error(f"❌ Gold price error: {e}")
        return GoldPriceResponse(
            success=False,
            error=f"خطأ في جلب أسعار الذهب: {str(e)}"
        )

@api_router.get("/forex-price/{pair}")
async def get_forex_price(pair: str):
    """Get current forex price for a currency pair"""
    try:
        # Get forex price
        forex_price = await forex_manager.get_forex_price(pair, use_cache=True)
        
        if not forex_price:
            raise HTTPException(status_code=404, detail=f"Currency pair {pair} not found")
        
        return {
            "success": True,
            "price_data": {
                "pair": forex_price.pair,
                "price_usd": forex_price.price_usd,
                "price_change": forex_price.price_change,
                "price_change_pct": forex_price.price_change_pct,
                "ask": forex_price.ask,
                "bid": forex_price.bid,
                "high_24h": forex_price.high_24h,
                "low_24h": forex_price.low_24h,
                "source": forex_price.source,
                "timestamp": forex_price.timestamp.isoformat()
            },
            "formatted_text": forex_manager.get_formatted_text(forex_price)
        }
        
    except Exception as e:
        logging.error(f"❌ Forex price error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/forex-pairs")
async def get_supported_forex_pairs():
    """Get list of supported forex pairs"""
    return {
        "success": True,
        "pairs": list(forex_manager.CURRENCY_PAIRS.keys()),
        "pair_names": forex_manager.CURRENCY_NAMES_AR
    }

@api_router.post("/analyze-forex", response_model=ForexAnalysisResponse)
async def analyze_forex(request: ForexAnalysisRequest):
    """Analyze forex pair with AI"""
    try:
        if not ai_manager:
            raise HTTPException(status_code=503, detail="Analysis service not initialized")
        
        start_time = datetime.utcnow()
        
        # Get current forex price
        forex_price = await forex_manager.get_forex_price(request.pair, use_cache=True)
        
        if not forex_price:
            return ForexAnalysisResponse(
                success=False,
                error=f"لا يمكن الحصول على سعر {request.pair}"
            )
        
        # Get Arabic name for the pair
        pair_name_ar = forex_manager.CURRENCY_NAMES_AR.get(request.pair, request.pair)
        
        # Create analysis context specific for forex
        forex_context = f"""
معلومات السوق الحالية:
- زوج العملة: {pair_name_ar} ({request.pair})
- السعر الحالي: {forex_price.price_usd:.4f}
- التغيير 24 ساعة: {forex_price.price_change:.4f} ({forex_price.price_change_pct:.2f}%)
- أعلى 24 ساعة: {forex_price.high_24h:.4f}
- أدنى 24 ساعة: {forex_price.low_24h:.4f}
- الوقت: {forex_price.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
- المصدر: {forex_price.source}

{request.additional_context}
"""
        
        # Generate analysis using the AI manager
        # We'll adapt the gold analysis to work with forex
        analysis_type = AnalysisType.DETAILED if request.analysis_type == "detailed" else AnalysisType.QUICK
        
        # Create a modified prompt for forex
        forex_prompt = f"""أنت محلل عملات محترف من مدرسة الكابوس الذهبية بخبرة 20+ سنة في أسواق العملات الأجنبية.

قم بتحليل زوج العملة {pair_name_ar} ({request.pair}) بناءً على المعلومات التالية:

{forex_context}

قدم تحليلاً شاملاً يتضمن:

📊 **التحليل الفني المفصل:**
• الاتجاه العام للزوج
• النماذج الفنية المتكونة
• مستويات الدعم والمقاومة المهمة
• تحليل الحجم والزخم

📈 **العوامل الاقتصادية المؤثرة:**
• السياسة النقدية للبنوك المركزية
• المؤشرات الاقتصادية المهمة
• الأحداث الجيوسياسية
• معنويات السوق

💰 **التوصيات التداولية:**
• نقاط الدخول المحتملة
• الأهداف (TP1, TP2, TP3)
• وقف الخسارة المناسب
• نسبة المخاطرة/العائد

⚡ **السيناريوهات المحتملة:**
• السيناريو الصاعد: الشروط والأهداف
• السيناريو الهابط: الشروط والأهداف
• المستويات الحرجة للمراقبة

⚠️ **إدارة المخاطر:**
• نصائح مهمة للحماية من التقلبات
• متى يجب تحريك وقف الخسارة
• متى يجب أخذ أرباح جزئية

التوقيع: 🏆 Gold Nightmare - عدي"""
        
        # Use the AI manager to generate analysis
        analysis = await ai_manager.generate_analysis(
            user_id=1,  # Default user for web app
            analysis_type=analysis_type,
            gold_price=None,  # We pass None since this is forex, not gold
            additional_context=forex_prompt
        )
        
        if not analysis:
            return ForexAnalysisResponse(
                success=False,
                error="فشل في إجراء تحليل العملة. يرجى المحاولة مرة أخرى."
            )
        
        end_time = datetime.utcnow()
        processing_time = (end_time - start_time).total_seconds()
        
        return ForexAnalysisResponse(
            success=True,
            analysis=analysis.content,
            forex_price={
                "pair": forex_price.pair,
                "price_usd": forex_price.price_usd,
                "price_change": forex_price.price_change,
                "price_change_pct": forex_price.price_change_pct,
                "high_24h": forex_price.high_24h,
                "low_24h": forex_price.low_24h,
                "source": forex_price.source
            },
            processing_time=processing_time
        )
        
    except Exception as e:
        logging.error(f"❌ Forex analysis error: {e}")
        return ForexAnalysisResponse(
            success=False,
            error=f"خطأ في تحليل العملة: {str(e)}"
        )

@api_router.post("/analyze-chart", response_model=ChartAnalysisResponse)
async def analyze_chart(request: ChartAnalysisRequest):
    """Analyze trading chart image with advanced AI and OCR"""
    try:
        if not ai_manager or not price_manager:
            raise HTTPException(status_code=503, detail="Analysis services not initialized")
        
        start_time = datetime.utcnow()
        
        # Validate and process base64 image
        try:
            # Remove data URL prefix if present
            if request.image_data.startswith('data:image'):
                request.image_data = request.image_data.split(',')[1]
            
            # Decode base64 image
            image_bytes = base64.b64decode(request.image_data)
            
            # Advanced image processing with OCR
            logger.info("🔍 Starting advanced chart analysis with OCR...")
            chart_analysis = await chart_processor.process_chart_image(image_bytes)
            
            if "error" in chart_analysis:
                return ChartAnalysisResponse(
                    success=False,
                    error=f"فشل في معالجة الصورة: {chart_analysis['error']}"
                )
                
        except Exception as e:
            return ChartAnalysisResponse(
                success=False,
                error=f"فشل في معالجة الصورة: {str(e)}"
            )
        
        # Get current gold price for context
        gold_price = await price_manager.get_current_price(use_cache=True)
        
        # Build comprehensive analysis context from extracted data
        extracted_context = _build_chart_analysis_context(
            chart_analysis, request.currency_pair, request.timeframe, request.analysis_notes
        )
        
        # Generate analysis using Claude AI with extracted information
        analysis = await ai_manager.generate_analysis(
            user_id=1,  # Default user for web app
            analysis_type=AnalysisType.CHART,
            gold_price=gold_price,
            additional_context=extracted_context
        )
        
        if not analysis:
            return ChartAnalysisResponse(
                success=False,
                error="فشل في إجراء تحليل الشارت. يرجى المحاولة مرة أخرى."
            )
        
        end_time = datetime.utcnow()
        processing_time = (end_time - start_time).total_seconds()
        
        return ChartAnalysisResponse(
            success=True,
            analysis=analysis.content,
            image_info={
                "width": chart_analysis.get("image_info", {}).get("width", 0),
                "height": chart_analysis.get("image_info", {}).get("height", 0),
                "format": chart_analysis.get("image_info", {}).get("format", "unknown"),
                "size_kb": len(image_bytes) / 1024,
                "extracted_data": chart_analysis.get("trading_context", {}),
                "ocr_confidence": chart_analysis.get("trading_context", {}).get("confidence_score", 0.0),
                "detected_prices": chart_analysis.get("price_analysis", {}).get("detected_prices", []),
                "visual_signals": chart_analysis.get("trading_context", {}).get("trading_signals", [])
            },
            processing_time=processing_time
        )
        
    except Exception as e:
        logging.error(f"❌ Chart analysis error: {e}")
        return ChartAnalysisResponse(
            success=False,
            error=f"خطأ في تحليل الشارت: {str(e)}"
        )

def _build_chart_analysis_context(chart_analysis: Dict[str, Any], currency_pair: str, timeframe: str, notes: str) -> str:
    """Build comprehensive analysis context from extracted chart data"""
    
    # Extract key information
    extracted_data = chart_analysis.get("trading_context", {})
    price_analysis = chart_analysis.get("price_analysis", {})
    text_extraction = chart_analysis.get("text_extraction", {})
    visual_analysis = chart_analysis.get("visual_analysis", {})
    
    context_parts = [
        f"""أنت محلل فني محترف من مدرسة الكابوس الذهبية. تم استخراج المعلومات التالية من صورة الشارت باستخدام الذكاء الاصطناعي وOCR:

📊 **معلومات الشارت الأساسية:**
- زوج العملة: {currency_pair}
- الإطار الزمني: {timeframe}
- ملاحظات المستخدم: {notes or 'لا توجد'}"""
    ]
    
    # Add extracted prices if available
    if price_analysis.get("detected_prices"):
        prices = price_analysis["detected_prices"][:5]  # أول 5 أسعار
        prices_text = ", ".join([f"${p:.2f}" for p in prices])
        context_parts.append(f"""
🔢 **الأسعار المستخرجة من الشارت:**
- الأسعار المكتشفة: {prices_text}
- السعر المقدر الحالي: ${price_analysis.get('current_price_estimate', 'غير محدد')}""")
        
        if price_analysis.get("high_low_estimates"):
            hle = price_analysis["high_low_estimates"]
            context_parts.append(f"""- أعلى سعر مكتشف: ${hle.get('highest', 'غير محدد')}
- أقل سعر مكتشف: ${hle.get('lowest', 'غير محدد')}
- المدى السعري: ${hle.get('range', 'غير محدد')}""")
    
    # Add detected text information
    if text_extraction.get("currency_pairs") or text_extraction.get("timeframes") or text_extraction.get("indicators"):
        context_parts.append(f"""
📝 **النصوص المستخرجة من الشارت:**""")
        
        if text_extraction.get("currency_pairs"):
            pairs = [p["pair"] for p in text_extraction["currency_pairs"][:3]]
            context_parts.append(f"- أزواج العملات المكتشفة: {', '.join(pairs)}")
            
        if text_extraction.get("timeframes"):
            timeframes = [t["timeframe"] for t in text_extraction["timeframes"][:3]]
            context_parts.append(f"- الإطارات الزمنية المكتشفة: {', '.join(timeframes)}")
            
        if text_extraction.get("indicators"):
            indicators = [i["indicator"] for i in text_extraction["indicators"][:5]]
            context_parts.append(f"- المؤشرات الفنية المكتشفة: {', '.join(indicators)}")
    
    # Add visual analysis
    if visual_analysis.get("colors", {}).get("candlestick_analysis"):
        candle_analysis = visual_analysis["colors"]["candlestick_analysis"]
        context_parts.append(f"""
🎨 **التحليل البصري للألوان:**
- النسبة الخضراء (صعود): {candle_analysis.get('green_percentage', 0):.1f}%
- النسبة الحمراء (هبوط): {candle_analysis.get('red_percentage', 0):.1f}%
- إشارة الاتجاه: {candle_analysis.get('trend_indication', 'غير محدد')}""")
    
    # Add pattern analysis
    if visual_analysis.get("patterns", {}).get("trend_lines"):
        trend_lines = visual_analysis["patterns"]["trend_lines"]
        context_parts.append(f"""
📈 **تحليل خطوط الاتجاه:**
- خطوط أفقية: {trend_lines.get('horizontal', 0)}
- خطوط صاعدة: {trend_lines.get('ascending', 0)}
- خطوط هابطة: {trend_lines.get('descending', 0)}
- اتجاه الترند: {trend_lines.get('trend_direction', 'غير محدد')}""")
    
    # Add trading signals
    if extracted_data.get("trading_signals"):
        context_parts.append(f"""
🚨 **إشارات التداول المكتشفة:**""")
        for signal in extracted_data["trading_signals"][:3]:
            context_parts.append(f"- {signal}")
    
    # Add confidence score
    confidence = extracted_data.get("confidence_score", 0.0)
    context_parts.append(f"""
🎯 **مستوى الثقة في البيانات المستخرجة:** {confidence:.1f}/1.0

بناءً على هذه المعلومات المستخرجة من الشارت، قم بتحليل فني شامل ودقيق يتضمن:

1. 📊 **تحليل الأسعار المكتشفة** وعلاقتها بالحركة الحالية
2. 🎨 **تفسير الإشارات البصرية** من الألوان وخطوط الاتجاه
3. 📈 **ربط المؤشرات المكتشفة** بتوقعات الحركة
4. 💡 **توصيات تداولية مبنية على البيانات المستخرجة**
5. ⚠️ **تحذيرات** مبنية على مستوى الثقة في البيانات

التوقيع: 🏆 Gold Nightmare - عدي""")
    
    return "\n".join(context_parts)

@api_router.post("/analyze", response_model=AnalysisResponse)
async def analyze_gold(request: AnalysisRequest):
    """Generate AI analysis of gold market"""
    try:
        if not ai_manager or not price_manager:
            raise HTTPException(status_code=503, detail="Analysis services not initialized")
        
        # Validate analysis type
        try:
            analysis_type = AnalysisType(request.analysis_type)
        except ValueError:
            return AnalysisResponse(
                success=False,
                error="نوع التحليل غير صحيح. الأنواع المتاحة: quick, detailed, chart, news, forecast"
            )
        
        start_time = datetime.utcnow()
        
        # Get current gold price
        gold_price = await price_manager.get_current_price(use_cache=True)
        
        # Generate analysis
        analysis = await ai_manager.generate_analysis(
            user_id=1,  # Default user for web app
            analysis_type=analysis_type,
            gold_price=gold_price,
            additional_context=request.additional_context or request.user_question or ""
        )
        
        end_time = datetime.utcnow()
        processing_time = (end_time - start_time).total_seconds()
        
        # Log the analysis request
        if admin_manager:
            await admin_manager.log_analysis(
                user_id=1,  # Default web user
                analysis_type=analysis_type,
                success=analysis is not None,
                processing_time=processing_time,
                error_message=None if analysis else "Analysis generation failed",
                gold_price=gold_price.price_usd if gold_price else None,
                user_tier=UserTier.BASIC
            )
        
        if not analysis:
            return AnalysisResponse(
                success=False,
                error="فشل في إجراء التحليل. يرجى المحاولة مرة أخرى."
            )
        
        end_time = datetime.utcnow()
        processing_time = (end_time - start_time).total_seconds()
        
        end_time = datetime.utcnow()
        processing_time = (end_time - start_time).total_seconds()
        
        # Convert gold price to dict if available
        gold_price_data = None
        if gold_price:
            gold_price_data = {
                "price_usd": gold_price.price_usd,
                "price_change": gold_price.price_change,
                "price_change_pct": gold_price.price_change_pct,
                "source": gold_price.source
            }
        
        return AnalysisResponse(
            success=True,
            analysis=analysis.content,
            gold_price=gold_price_data,
            processing_time=processing_time
        )
        
    except Exception as e:
        logging.error(f"❌ Analysis error: {e}")
        return AnalysisResponse(
            success=False,
            error=f"خطأ في إجراء التحليل: {str(e)}"
        )

@api_router.get("/analysis-types")
async def get_analysis_types():
    """Get available analysis types"""
    return {
        "types": [
            {
                "id": "quick",
                "name": "تحليل سريع",
                "description": "تحليل مختصر وسريع للوضع الحالي",
                "icon": "⚡"
            },
            {
                "id": "detailed", 
                "name": "تحليل مفصل",
                "description": "تحليل شامل ومفصل للسوق",
                "icon": "📊"
            },
            {
                "id": "chart",
                "name": "تحليل فني",
                "description": "تحليل المخططات والمؤشرات الفنية",
                "icon": "📈"
            },
            {
                "id": "news",
                "name": "تحليل الأخبار",
                "description": "تحليل تأثير الأخبار على السوق",
                "icon": "📰"
            },
            {
                "id": "forecast",
                "name": "التوقعات",
                "description": "توقعات مستقبلية للسوق",
                "icon": "🔮"
            }
        ]
    }

@api_router.get("/api-status")
async def get_api_status():
    """Get status of external APIs"""
    try:
        status = {}
        
        # Test Gold Price APIs
        if price_manager:
            price_status = await price_manager.get_api_status()
            status["gold_apis"] = price_status
        
        # Test Claude AI
        if ai_manager:
            ai_stats = await ai_manager.get_ai_stats()
            status["claude_ai"] = ai_stats
        
        return {
            "success": True,
            "status": status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@api_router.get("/quick-questions")
async def get_quick_questions():
    """Get predefined quick questions for analysis"""
    return {
        "questions": [
            "تحليل الذهب الحالي",
            "ما هي توقعات الذهب للأسبوع القادم؟", 
            "هل الوقت مناسب لشراء الذهب؟",
            "تحليل فني للذهب",
            "تأثير التضخم على أسعار الذهب"
        ]
    }

# ==========================================
# ADMIN PANEL ENDPOINTS
# ==========================================

class AdminLoginRequest(BaseModel):
    username: str
    password: str

class AdminToggleUserRequest(BaseModel):
    user_id: int
    admin_id: str = "admin"

class AdminUpdateTierRequest(BaseModel):
    user_id: int
    new_tier: str
    admin_id: str = "admin"

@api_router.post("/admin/login")
async def admin_login(request: AdminLoginRequest):
    """Simple admin authentication (for MVP)"""
    try:
        # Simple hardcoded authentication for MVP
        # In production, this should use proper authentication
        if request.username == "admin" and request.password == "GOLD_NIGHTMARE_205":
            return {
                "success": True,
                "token": "admin_token_placeholder",
                "admin_info": {
                    "username": "admin",
                    "permissions": ["manage_users", "view_analytics", "modify_settings"]
                }
            }
        else:
            return {"success": False, "error": "Invalid credentials"}
            
    except Exception as e:
        logger.error(f"❌ Admin login error: {e}")
        return {"success": False, "error": str(e)}

@api_router.get("/admin/dashboard")
async def get_admin_dashboard():
    """Get admin dashboard statistics"""
    try:
        if not admin_manager:
            raise HTTPException(status_code=503, detail="Admin service not initialized")
        
        stats = await admin_manager.get_dashboard_stats()
        return {"success": True, "data": stats}
        
    except Exception as e:
        logger.error(f"❌ Admin dashboard error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/admin/users")
async def get_admin_users(page: int = 1, per_page: int = 50):
    """Get all users for admin panel"""
    try:
        if not admin_manager:
            raise HTTPException(status_code=503, detail="Admin service not initialized")
        
        users_data = await admin_manager.get_all_users(page=page, per_page=per_page)
        return {"success": True, "data": users_data}
        
    except Exception as e:
        logger.error(f"❌ Admin get users error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/admin/users/{user_id}")
async def get_admin_user_details(user_id: int):
    """Get detailed user information"""
    try:
        if not admin_manager:
            raise HTTPException(status_code=503, detail="Admin service not initialized")
        
        user_details = await admin_manager.get_user_details(user_id)
        if not user_details:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {"success": True, "data": user_details}
        
    except Exception as e:
        logger.error(f"❌ Admin get user details error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/admin/users/toggle-status")
async def admin_toggle_user_status(request: AdminToggleUserRequest):
    """Toggle user active/inactive status"""
    try:
        if not admin_manager:
            raise HTTPException(status_code=503, detail="Admin service not initialized")
        
        result = await admin_manager.toggle_user_status(request.user_id, request.admin_id)
        
        if result["success"]:
            return {"success": True, "data": result}
        else:
            return {"success": False, "error": result["error"]}
        
    except Exception as e:
        logger.error(f"❌ Admin toggle user status error: {e}")
        return {"success": False, "error": str(e)}

@api_router.post("/admin/users/update-tier")
async def admin_update_user_tier(request: AdminUpdateTierRequest):
    """Update user subscription tier"""
    try:
        if not admin_manager:
            raise HTTPException(status_code=503, detail="Admin service not initialized")
        
        result = await admin_manager.update_user_tier(request.user_id, request.new_tier, request.admin_id)
        
        if result["success"]:
            return {"success": True, "data": result}
        else:
            return {"success": False, "error": result["error"]}
        
    except Exception as e:
        logger.error(f"❌ Admin update tier error: {e}")
        return {"success": False, "error": str(e)}

@api_router.get("/admin/analysis-logs")
async def get_admin_analysis_logs(page: int = 1, per_page: int = 100, user_id: Optional[int] = None):
    """Get analysis logs for admin panel"""
    try:
        if not admin_manager:
            raise HTTPException(status_code=503, detail="Admin service not initialized")
        
        # Get logs with optional user filtering
        skip = (page - 1) * per_page
        
        # Build query
        query = {}
        if user_id:
            query["user_id"] = user_id
        
        # Get logs from database
        logs_cursor = admin_manager.analysis_logs_collection.find(query).sort("timestamp", -1).skip(skip).limit(per_page)
        logs = await logs_cursor.to_list(length=per_page)
        
        # Get total count
        total_logs = await admin_manager.analysis_logs_collection.count_documents(query)
        
        # Format logs
        formatted_logs = []
        for log in logs:
            formatted_logs.append({
                "id": log.get("id"),
                "user_id": log.get("user_id"),
                "analysis_type": log.get("analysis_type"),
                "success": log.get("success", False),
                "processing_time": log.get("processing_time", 0),
                "error_message": log.get("error_message"),
                "user_tier": log.get("user_tier", "basic"),
                "gold_price_at_request": log.get("gold_price_at_request"),
                "tokens_used": log.get("tokens_used"),
                "timestamp": log.get("timestamp", datetime.utcnow()).isoformat()
            })
        
        return {
            "success": True,
            "data": {
                "logs": formatted_logs,
                "total": total_logs,
                "page": page,
                "per_page": per_page,
                "total_pages": (total_logs + per_page - 1) // per_page
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Admin get logs error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/admin/system-status")
async def get_admin_system_status():
    """Get system status for admin panel"""
    try:
        status = {}
        
        # Test Gold Price APIs
        if price_manager:
            price_status = await price_manager.get_api_status()
            status["gold_apis"] = price_status
        
        # Test Claude AI
        if ai_manager:
            ai_stats = await ai_manager.get_ai_stats()
            status["claude_ai"] = ai_stats
        
        # Database status
        if db_manager:
            try:
                await db_manager.get_database()
                status["database"] = {"status": "connected", "type": "MongoDB"}
            except Exception as e:
                status["database"] = {"status": "error", "error": str(e)}
        
        # Admin manager status
        status["admin_manager"] = {"status": "initialized" if admin_manager else "not_initialized"}
        
        return {
            "success": True,
            "status": status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# Include API router
app.include_router(api_router)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/supervisor/gold_analysis.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Error handling
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "حدث خطأ داخلي في الخادم"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8001, reload=True)