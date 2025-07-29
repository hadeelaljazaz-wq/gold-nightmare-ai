"""
Gold Nightmare Bot AI Analysis Manager
مدير التحليل الذكي للذهب باستخدام Claude AI
"""
import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, Any, Tuple
import hashlib
import time

from emergentintegrations.llm.chat import LlmChat, UserMessage

from .config import get_config
from .models import AnalysisType, Analysis, GoldPrice
from .cache import get_cache_manager

logger = logging.getLogger(__name__)

class AIAnalysisManager:
    """Manages AI-powered gold market analysis using Claude"""
    
    def __init__(self):
        self.config = get_config()
        self.cache_manager = None
        
        # Analysis prompts for different types
        self.analysis_prompts = {
            AnalysisType.QUICK: self._get_quick_analysis_prompt(),
            AnalysisType.DETAILED: self._get_detailed_analysis_prompt(), 
            AnalysisType.CHART: self._get_chart_analysis_prompt(),
            AnalysisType.NEWS: self._get_news_analysis_prompt(),
            AnalysisType.FORECAST: self._get_forecast_analysis_prompt()
        }
        
    async def initialize(self):
        """Initialize the AI manager"""
        try:
            self.cache_manager = await get_cache_manager()
            logger.info("✅ AI Analysis Manager initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize AI Manager: {e}")
            raise
    
    async def generate_analysis(
        self, 
        user_id: int, 
        analysis_type: AnalysisType, 
        gold_price: Optional[GoldPrice] = None,
        additional_context: str = ""
    ) -> Optional[Analysis]:
        """Generate AI analysis of gold market"""
        
        start_time = time.time()
        
        try:
            # Create analysis context
            context = self._build_analysis_context(gold_price, additional_context)
            
            # Check cache first
            content_hash = hashlib.md5(f"{analysis_type.value}:{context}".encode()).hexdigest()[:16]
            
            if self.cache_manager:
                cached_analysis = await self.cache_manager.get_cached_analysis(
                    user_id, analysis_type.value, content_hash
                )
                if cached_analysis:
                    logger.info(f"📦 Using cached analysis for user {user_id}")
                    return cached_analysis
            
            # Generate new analysis
            logger.info(f"🤖 Generating {analysis_type.value} analysis for user {user_id}")
            
            # Create Claude chat instance
            chat = LlmChat(
                api_key=self.config.claude_api_key,
                session_id=f"gold_analysis_{user_id}_{int(datetime.utcnow().timestamp())}",
                system_message=self._get_system_message()
            ).with_model("anthropic", self.config.claude_model).with_max_tokens(self.config.claude_max_tokens)
            
            # Get analysis prompt
            prompt = self.analysis_prompts[analysis_type].format(
                context=context,
                bot_signature=self.config.bot_signature,
                timestamp=datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
            )
            
            # Send message to Claude
            user_message = UserMessage(text=prompt)
            response = await chat.send_message(user_message)
            
            if not response:
                logger.error("❌ Empty response from Claude AI")
                return None
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Create analysis object
            analysis = Analysis(
                user_id=user_id,
                analysis_type=analysis_type,
                content=response,
                gold_price=gold_price.price_usd if gold_price else None,
                price_change=gold_price.price_change if gold_price else None,
                model_used=self.config.claude_model,
                language=self.config.prompt_language,
                processing_time=processing_time,
                created_at=datetime.utcnow()
            )
            
            # Cache the analysis
            if self.cache_manager:
                await self.cache_manager.cache_analysis(user_id, analysis, content_hash)
            
            logger.info(f"✅ Generated {analysis_type.value} analysis in {processing_time:.2f}s")
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Failed to generate analysis: {e}")
            return None
    
    def _get_system_message(self) -> str:
        """Get system message for Claude"""
        return f"""
أنت محلل ذهب محترف من مدرسة الكابوس الذهبية بخبرة 20+ سنة في الأسواق المالية.

خبرتك تشمل:
- تحليل اتجاهات أسعار الذهب XAU/USD
- قراءة المؤشرات الفنية والأساسية
- تقديم توصيات استراتيجية للتداول
- فهم العوامل المؤثرة على أسعار الذهب (تضخم، أسعار فائدة، جيوسياسية)

قواعد مهمة:
1. استخدم السعر المعطى كأساس للتحليل - لا تشكك فيه أبداً
2. قدم تحليلاً دقيقاً ومفصلاً
3. استخدم المؤشرات الفنية المناسبة
4. حدد مستويات واضحة للدخول والخروج
5. أضف إدارة المخاطر دائماً
- اكتب باللغة العربية دائماً
- استخدم رموز emoji مناسبة لجعل التحليل جذاب
- قدم معلومات دقيقة ومفيدة فقط
- لا تقدم نصائح استثمارية مباشرة، بل تحليلات تعليمية
- اذكر دائماً أن التداول محفوف بالمخاطر
- ختم كل تحليل بتوقيع: 🏆 Gold Nightmare - عدي

التاريخ والوقت الحالي: {datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")}
        """
    
    def _build_analysis_context(self, gold_price: Optional[GoldPrice], additional_context: str = "") -> str:
        """Build context for analysis"""
        context = ""
        
        if gold_price:
            context = f"""
معلومات السوق الحالية:
- السعر الحالي: ${gold_price.price_usd:.2f}
- التغيير 24 ساعة: {gold_price.price_change:.2f} ({gold_price.price_change_pct:.2f}%)
- أعلى 24 ساعة: ${gold_price.high_24h:.2f}
- أدنى 24 ساعة: ${gold_price.low_24h:.2f}
- الوقت: {gold_price.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
- المصدر: {gold_price.source}
            """.strip()
        
        if additional_context:
            context += f"\n\nمعلومات إضافية:\n{additional_context}"
        
        return context
    
    def _get_quick_analysis_prompt(self) -> str:
        """Quick analysis prompt"""
        return """
قم بتحليل سريع ومفيد لسعر الذهب الحالي. يجب أن يكون التحليل:
- مختصر (100-200 كلمة)
- يركز على النقاط المهمة فقط
- يتضمن رأي سريع حول الاتجاه المتوقع قصير المدى

بيانات السوق:
{context}

اكتب تحليل سريع وواضح باللغة العربية.

التوقيت: {timestamp}
التوقيع: {bot_signature}
        """
    
    def _get_detailed_analysis_prompt(self) -> str:
        """Detailed analysis prompt"""
        return """
قم بإجراء تحليل مفصل وشامل لسعر الذهب يتضمن:

1. 📊 تحليل السعر الحالي والتغييرات
2. 📈 التحليل الفني (الاتجاهات، المقاومة، الدعم)
3. 🌍 العوامل الاقتصادية المؤثرة
4. 💡 رؤية متوسطة المدى (أسبوع-شهر)
5. ⚠️ المخاطر والفرص
6. 📋 نقاط مهمة للمتداولين

بيانات السوق:
{context}

اجعل التحليل شاملاً ومفيداً (400-600 كلمة) باللغة العربية.

التوقيت: {timestamp}
التوقيع: {bot_signature}
        """
    
    def _get_chart_analysis_prompt(self) -> str:
        """Chart analysis prompt"""
        return """
قم بتحليل فني متخصص لحركة سعر الذهب مع التركيز على:

📊 التحليل الفني:
- مستويات الدعم والمقاومة
- الاتجاهات والقنوات السعرية
- المؤشرات الفنية المهمة
- نقاط الدخول والخروج المحتملة

🎯 إشارات التداول:
- الإشارات الصاعدة أو الهابطة
- مستويات مهمة للمراقبة
- حجم التداول والزخم

بيانات السوق:
{context}

قدم تحليلاً فنياً مفصلاً (300-500 كلمة) باللغة العربية.

التوقيت: {timestamp}  
التوقيع: {bot_signature}
        """
    
    def _get_news_analysis_prompt(self) -> str:
        """News-based analysis prompt"""
        return """
قم بتحليل تأثير الأخبار والأحداث الاقتصادية على سعر الذهب:

📰 تحليل الأخبار:
- الأحداث الاقتصادية المؤثرة
- القرارات السياسة النقدية
- التطورات الجيوسياسية
- مؤشرات التضخم والنمو

💼 تأثير على السوق:
- كيف تؤثر هذه العوامل على الذهب
- التوقعات قصيرة ومتوسطة المدى
- ما يجب متابعته

بيانات السوق:
{context}

قدم تحليلاً إخبارياً شاملاً (300-400 كلمة) باللغة العربية.

التوقيت: {timestamp}
التوقيع: {bot_signature}
        """
    
    def _get_forecast_analysis_prompt(self) -> str:
        """Forecast analysis prompt"""
        return """
قم بإعداد توقع مدروس لاتجاه سعر الذهب مع التركيز على:

🔮 التوقعات:
- الاتجاه المتوقع للأسبوع القادم
- العوامل المؤثرة على التوقع
- السيناريوهات المحتملة (صاعد/هابط/متذبذب)

📊 المستويات المهمة:
- مستويات الدعم والمقاومة المتوقعة
- نقاط الكسر المهمة
- أهداف سعرية محتملة

⚠️ تحذيرات مهمة:
- المخاطر في كل سيناريو
- العوامل التي قد تغير التوقع
- نصائح إدارة المخاطر

بيانات السوق:
{context}

قدم توقعاً مدروساً (400-500 كلمة) باللغة العربية مع التأكيد على أن هذا تحليل تعليمي وليس نصيحة استثمارية.

التوقيت: {timestamp}
التوقيع: {bot_signature}
        """
    
    async def test_ai_connection(self) -> Tuple[bool, str]:
        """Test AI connection and response"""
        try:
            chat = LlmChat(
                api_key=self.config.claude_api_key,
                session_id=f"test_{int(datetime.utcnow().timestamp())}",
                system_message="أنت مساعد ذكي للاختبار"
            ).with_model("anthropic", self.config.claude_model).with_max_tokens(100)
            
            test_message = UserMessage(text="قل 'اختبار ناجح' فقط")
            response = await chat.send_message(test_message)
            
            if response and "اختبار" in response:
                return True, "✅ Claude AI connection successful"
            else:
                return False, f"❌ Unexpected response: {response}"
                
        except Exception as e:
            return False, f"❌ Claude AI test failed: {str(e)}"
    
    async def get_ai_stats(self) -> Dict[str, Any]:
        """Get AI usage statistics"""
        try:
            # Test connection
            is_connected, status = await self.test_ai_connection()
            
            return {
                "model": self.config.claude_model,
                "max_tokens": self.config.claude_max_tokens,
                "temperature": self.config.claude_temperature,
                "language": self.config.prompt_language,
                "connected": is_connected,
                "status": status,
                "available_analysis_types": [t.value for t in AnalysisType]
            }
            
        except Exception as e:
            return {
                "model": self.config.claude_model,
                "connected": False,
                "error": str(e)
            }

# Global AI manager instance
ai_manager: Optional[AIAnalysisManager] = None

async def get_ai_manager() -> AIAnalysisManager:
    """Get global AI manager instance"""
    global ai_manager
    if ai_manager is None:
        ai_manager = AIAnalysisManager()
        await ai_manager.initialize()
    return ai_manager

# Utility functions
async def generate_quick_analysis(user_id: int, gold_price: Optional[GoldPrice] = None) -> Optional[str]:
    """Quick function to generate fast analysis"""
    manager = await get_ai_manager()
    analysis = await manager.generate_analysis(user_id, AnalysisType.QUICK, gold_price)
    return analysis.content if analysis else None

async def generate_detailed_analysis(user_id: int, gold_price: Optional[GoldPrice] = None) -> Optional[str]:
    """Quick function to generate detailed analysis"""
    manager = await get_ai_manager()
    analysis = await manager.generate_analysis(user_id, AnalysisType.DETAILED, gold_price)
    return analysis.content if analysis else None