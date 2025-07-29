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
from gold_bot.models import AnalysisType
from gold_bot.database import get_database

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

@app.on_event("startup")
async def startup_event():
    """Initialize components on startup"""
    global price_manager, ai_manager, db_manager
    try:
        # Initialize managers
        price_manager = await get_price_manager()
        ai_manager = await get_ai_manager()
        db_manager = await get_database()
        
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
    """Analyze trading chart image with AI"""
    try:
        if not ai_manager or not price_manager:
            raise HTTPException(status_code=503, detail="Analysis services not initialized")
        
        start_time = datetime.utcnow()
        
        # Validate base64 image
        try:
            # Remove data URL prefix if present
            if request.image_data.startswith('data:image'):
                request.image_data = request.image_data.split(',')[1]
            
            # Decode base64 image
            image_bytes = base64.b64decode(request.image_data)
            image = Image.open(io.BytesIO(image_bytes))
            
            # Get image info
            image_info = {
                "width": image.width,
                "height": image.height,
                "format": image.format,
                "size_kb": len(image_bytes) / 1024
            }
            
        except Exception as e:
            return ChartAnalysisResponse(
                success=False,
                error=f"فشل في معالجة الصورة: {str(e)}"
            )
        
        # Get current gold price for context
        gold_price = await price_manager.get_current_price(use_cache=True)
        
        # Create comprehensive analysis prompt for chart
        chart_prompt = f"""
أنت محلل فني محترف من مدرسة الكابوس الذهبية. قم بتحليل صورة الشارت المرفقة بدقة عالية.

معلومات الشارت:
- زوج العملة: {request.currency_pair}
- الإطار الزمني: {request.timeframe}
- ملاحظات إضافية: {request.analysis_notes or 'لا توجد'}

السعر الحالي للذهب: ${gold_price.price_usd:.2f} إذا كان الشارت للذهب

قم بتحليل الشارت وفقاً للنقاط التالية:

📊 **تحليل الشارت التفصيلي:**
1. 🎯 **الاتجاه العام**: (صاعد/هابط/عرضي)
2. 📈 **النماذج الفنية**: حدد أي نماذج فنية مرئية (مثلثات، أعلام، رأس وكتفين، إلخ)
3. 🎚️ **مستويات الدعم والمقاومة**: حدد أهم المستويات المرئية في الشارت
4. 📊 **المؤشرات الفنية**: حلل أي مؤشرات مرئية في الشارت
5. 🔄 **نقاط الانعكاس**: حدد النقاط المهمة للانعكاس المحتمل

💡 **التوصيات التداولية:**
- 🟢 **الدخول الصاعد**: المستويات والشروط
- 🔴 **الدخول الهابط**: المستويات والشروط  
- ⛔ **وقف الخسارة**: المستويات المناسبة
- 🎯 **الأهداف**: الأهداف القريبة والبعيدة

⚠️ **إدارة المخاطر:**
- نسبة المخاطرة إلى العائد المتوقعة
- حجم الصفقة المناسب
- الأوقات المناسبة للدخول

🔮 **السيناريوهات المحتملة:**
- السيناريو الصاعد وشروطه
- السيناريو الهابط وشروطه
- النقاط الحرجة للمتابعة

📋 **ملاحظات مهمة:**
- تحذيرات خاصة بهذا الشارت
- العوامل الخارجية المؤثرة
- الأوقات المتوقعة للحركة

التوقيع: 🏆 Gold Nightmare - عدي
        """
        
        # Generate analysis using Claude AI
        analysis = await ai_manager.generate_analysis(
            user_id=1,  # Default user for web app
            analysis_type=AnalysisType.CHART,
            gold_price=gold_price,
            additional_context=chart_prompt
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
            image_info=image_info,
            processing_time=processing_time
        )
        
    except Exception as e:
        logging.error(f"❌ Chart analysis error: {e}")
        return ChartAnalysisResponse(
            success=False,
            error=f"خطأ في تحليل الشارت: {str(e)}"
        )

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
        
        if not analysis:
            return AnalysisResponse(
                success=False,
                error="فشل في إجراء التحليل. يرجى المحاولة مرة أخرى."
            )
        
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