"""
Gold Nightmare Bot Telegram UI Components
مكونات واجهة المستخدم لتليجرام
"""
import logging
from typing import List, Dict, Any, Optional
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode

from .models import User, UserTier, AnalysisType, UserStatus

logger = logging.getLogger(__name__)

class TelegramUI:
    """Telegram UI helper for keyboards and messages"""
    
    @staticmethod
    def get_main_menu_keyboard(user: Optional[User] = None) -> InlineKeyboardMarkup:
        """Get main menu keyboard based on user tier"""
        
        buttons = []
        
        # Always available options
        buttons.append([
            InlineKeyboardButton("💰 سعر الذهب", callback_data="price"),
            InlineKeyboardButton("📊 تحليل سريع", callback_data="analysis_quick")
        ])
        
        if user and user.is_active():
            # User-specific options based on tier
            if user.tier in [UserTier.PREMIUM, UserTier.VIP]:
                buttons.append([
                    InlineKeyboardButton("📈 تحليل مفصل", callback_data="analysis_detailed"),
                    InlineKeyboardButton("📊 تحليل فني", callback_data="analysis_chart")
                ])
            
            if user.tier == UserTier.VIP:
                buttons.append([
                    InlineKeyboardButton("📰 تحليل الأخبار", callback_data="analysis_news"),
                    InlineKeyboardButton("🔮 التوقعات", callback_data="analysis_forecast")
                ])
            
            buttons.append([
                InlineKeyboardButton("📋 إعداداتي", callback_data="settings"),
                InlineKeyboardButton("📊 إحصائياتي", callback_data="my_stats")
            ])
        
        else:
            # Not activated
            buttons.append([
                InlineKeyboardButton("🔐 تفعيل الحساب", callback_data="activate")
            ])
        
        # Always available
        buttons.append([
            InlineKeyboardButton("ℹ️ المساعدة", callback_data="help"),
            InlineKeyboardButton("📞 التواصل", callback_data="contact")
        ])
        
        return InlineKeyboardMarkup(buttons)
    
    @staticmethod
    def get_analysis_type_keyboard(user: Optional[User] = None) -> InlineKeyboardMarkup:
        """Get analysis type selection keyboard"""
        
        buttons = []
        
        # Quick analysis (always available)
        buttons.append([
            InlineKeyboardButton("⚡ تحليل سريع", callback_data="analysis_quick")
        ])
        
        if user and user.is_active():
            if user.tier in [UserTier.PREMIUM, UserTier.VIP]:
                buttons.append([
                    InlineKeyboardButton("📊 تحليل مفصل", callback_data="analysis_detailed")
                ])
                buttons.append([
                    InlineKeyboardButton("📈 تحليل فني", callback_data="analysis_chart")
                ])
            
            if user.tier == UserTier.VIP:
                buttons.append([
                    InlineKeyboardButton("📰 تحليل الأخبار", callback_data="analysis_news")
                ])
                buttons.append([
                    InlineKeyboardButton("🔮 توقعات السوق", callback_data="analysis_forecast")
                ])
        
        buttons.append([
            InlineKeyboardButton("🔙 الرجوع للقائمة", callback_data="main_menu")
        ])
        
        return InlineKeyboardMarkup(buttons)
    
    @staticmethod
    def get_settings_keyboard(user: User) -> InlineKeyboardMarkup:
        """Get user settings keyboard"""
        
        buttons = []
        
        # Tier information
        tier_emoji = {"basic": "🥉", "premium": "🥈", "vip": "🏆"}
        tier_text = f"{tier_emoji.get(user.tier.value, '❓')} الباقة: {user.tier.value.title()}"
        
        buttons.append([
            InlineKeyboardButton(tier_text, callback_data="tier_info")
        ])
        
        # Usage stats
        buttons.append([
            InlineKeyboardButton("📊 استخدامي اليوم", callback_data="usage_today"),
            InlineKeyboardButton("📈 إجمالي الاستخدام", callback_data="usage_total")
        ])
        
        # Account actions
        buttons.append([
            InlineKeyboardButton("🔄 تحديث البيانات", callback_data="refresh_data")
        ])
        
        if user.tier == UserTier.BASIC:
            buttons.append([
                InlineKeyboardButton("⬆️ ترقية الباقة", callback_data="upgrade_tier")
            ])
        
        buttons.append([
            InlineKeyboardButton("🔙 الرجوع للقائمة", callback_data="main_menu")
        ])
        
        return InlineKeyboardMarkup(buttons)
    
    @staticmethod
    def get_admin_keyboard() -> InlineKeyboardMarkup:
        """Get admin panel keyboard"""
        
        buttons = [
            [
                InlineKeyboardButton("👥 إحصائيات المستخدمين", callback_data="admin_users"),
                InlineKeyboardButton("📊 إحصائيات البوت", callback_data="admin_stats")
            ],
            [
                InlineKeyboardButton("📋 سجل التحليلات", callback_data="admin_analyses"),
                InlineKeyboardButton("🔧 حالة الأنظمة", callback_data="admin_system")
            ],
            [
                InlineKeyboardButton("📢 إرسال رسالة جماعية", callback_data="admin_broadcast")
            ],
            [
                InlineKeyboardButton("🔙 الرجوع للقائمة", callback_data="main_menu")
            ]
        ]
        
        return InlineKeyboardMarkup(buttons)
    
    @staticmethod
    def get_back_to_menu_keyboard() -> InlineKeyboardMarkup:
        """Simple back to menu keyboard"""
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 الرجوع للقائمة الرئيسية", callback_data="main_menu")]
        ])
    
    @staticmethod
    def get_confirmation_keyboard(action: str) -> InlineKeyboardMarkup:
        """Get yes/no confirmation keyboard"""
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ نعم", callback_data=f"confirm_{action}"),
                InlineKeyboardButton("❌ لا", callback_data=f"cancel_{action}")
            ]
        ])

class MessageFormatter:
    """Format messages with proper Arabic styling"""
    
    @staticmethod
    def format_welcome_message(user: User) -> str:
        """Format welcome message"""
        
        if user.is_active():
            status_emoji = "✅"
            status_text = "مفعل"
        else:
            status_emoji = "❌" 
            status_text = "غير مفعل"
        
        tier_emoji = {"basic": "🥉", "premium": "🥈", "vip": "🏆"}
        
        return f"""
🏆 **أهلاً وسهلاً بك في Gold Nightmare Bot**
━━━━━━━━━━━━━━━━━━━━━━━━━━

👋 مرحباً **{user.first_name or 'المتداول'}**

{status_emoji} **حالة الحساب:** {status_text}
{tier_emoji.get(user.tier.value, '❓')} **نوع الباقة:** {user.tier.value.title()}
📊 **التحليلات اليوم:** {user.analyses_today}/{user.get_rate_limit()}
📈 **إجمالي التحليلات:** {user.total_analyses}

🎯 **خدماتنا المتاحة:**
• 💰 أسعار الذهب اللحظية
• 📊 تحليلات ذكية بالذكاء الاصطناعي
• 📈 تحليل فني متقدم
• 📰 تحليل الأخبار والأحداث
• 🔮 توقعات السوق

⚠️ **تنبيه مهم:** جميع التحليلات تعليمية وليست نصائح استثمارية

اختر من القائمة أدناه للبدء 👇
        """.strip()
    
    @staticmethod
    def format_help_message() -> str:
        """Format help message"""
        return """
ℹ️ **دليل استخدام Gold Nightmare Bot**
━━━━━━━━━━━━━━━━━━━━━━━━━━

🔧 **الأوامر المتاحة:**
• `/start` - بدء استخدام البوت
• `/help` - عرض هذه المساعدة
• `/price` - سعر الذهب الحالي
• `/quick` - تحليل سريع
• `/settings` - إعداداتك الشخصية

💰 **أنواع الباقات:**

🥉 **الباقة الأساسية (مجانية):**
• 5 تحليلات في الساعة
• تحليل سريع فقط
• أسعار الذهب اللحظية

🥈 **الباقة المميزة:**
• 20 تحليل في الساعة
• تحليل مفصل وفني
• إشعارات متقدمة

🏆 **الباقة الذهبية:**
• 50 تحليل في الساعة
• تحليل الأخبار والتوقعات
• دعم فني مخصص

🔐 **التفعيل:**
استخدم كلمة المرور للحصول على وصول كامل

⚠️ **المخاطر:**
• التداول ينطوي على مخاطر عالية
• لا تستثمر أكثر مما يمكنك تحمل خسارته
• استشر خبير مالي قبل اتخاذ قرارات استثمارية

📞 **للدعم:** راسل المطور أو استخدم أمر المساعدة
        """.strip()
    
    @staticmethod
    def format_activation_prompt() -> str:
        """Format activation prompt message"""
        return """
🔐 **تفعيل حسابك في Gold Nightmare Bot**
━━━━━━━━━━━━━━━━━━━━━━━━━━

للحصول على الوصول الكامل لجميع الميزات، يرجى إدخال كلمة المرور.

🎯 **ما ستحصل عليه بعد التفعيل:**
• 📊 تحليلات ذكية غير محدودة
• 💰 أسعار الذهب اللحظية مع التحديثات
• 📈 تحليل فني متقدم للمخططات
• 🔮 توقعات وتحليل الأخبار (حسب الباقة)
• 📱 واجهة مخصصة متطورة

⌨️ **أرسل كلمة المرور الآن:**
        """.strip()
    
    @staticmethod
    def format_rate_limit_message(reason: str, cooldown_seconds: int) -> str:
        """Format rate limiting message with cooldown"""
        
        if cooldown_seconds > 3600:  # More than 1 hour
            hours = cooldown_seconds // 3600
            time_text = f"{hours} ساعة"
        elif cooldown_seconds > 60:  # More than 1 minute
            minutes = cooldown_seconds // 60
            time_text = f"{minutes} دقيقة"
        else:
            time_text = f"{cooldown_seconds} ثانية"
        
        return f"""
⏱️ **تم الوصول للحد الأقصى**
━━━━━━━━━━━━━━━━━━━━━━━━━━

❌ **السبب:** {reason}

⏰ **الانتظار المطلوب:** {time_text}

💡 **لزيادة الحد:**
• 🥈 ترقية للباقة المميزة: 20 تحليل/ساعة
• 🏆 ترقية للباقة الذهبية: 50 تحليل/ساعة

📞 للترقية راسل المطور أو استخدم /upgrade
        """.strip()
    
    @staticmethod
    def format_user_stats(user: User) -> str:
        """Format user statistics"""
        
        tier_emoji = {"basic": "🥉", "premium": "🥈", "vip": "🏆"}
        status_emoji = "✅" if user.is_active() else "❌"
        
        # Calculate usage percentage
        daily_limit = user.get_rate_limit() * 24  # Rough daily limit
        usage_pct = (user.analyses_today / daily_limit * 100) if daily_limit > 0 else 0
        
        last_analysis = "لم يتم بعد" if not user.last_analysis_at else user.last_analysis_at.strftime("%Y-%m-%d %H:%M")
        
        return f"""
📊 **إحصائياتك الشخصية**
━━━━━━━━━━━━━━━━━━━━━━━━━━

👤 **معلومات الحساب:**
• الاسم: {user.first_name or 'غير محدد'}
• المعرف: @{user.username or 'غير محدد'}
• {status_emoji} الحالة: {'مفعل' if user.is_active() else 'غير مفعل'}
• {tier_emoji.get(user.tier.value, '❓')} الباقة: {user.tier.value.title()}

📈 **إحصائيات الاستخدام:**
• التحليلات اليوم: {user.analyses_today}/{user.get_rate_limit() * 3}
• إجمالي التحليلات: {user.total_analyses}
• نسبة الاستخدام اليومي: {usage_pct:.1f}%
• آخر تحليل: {last_analysis}

📅 **تواريخ مهمة:**
• تاريخ الانضمام: {user.created_at.strftime('%Y-%m-%d')}
• آخر نشاط: {user.last_seen.strftime('%Y-%m-%d %H:%M') if user.last_seen else 'الآن'}

💡 **نصائح:**
• استخدم التحليل السريع للمتابعة المستمرة
• التحليل المفصل أفضل للقرارات الاستراتيجية
• تابع الأخبار لفهم تحركات السوق
        """.strip()
    
    @staticmethod
    def escape_markdown(text: str) -> str:
        """Escape special characters for MarkdownV2"""
        special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        for char in special_chars:
            text = text.replace(char, f'\\{char}')
        return text
    
    @staticmethod  
    def format_error_message(error: str) -> str:
        """Format error message"""
        return f"""
❌ **حدث خطأ**
━━━━━━━━━━━━━

{error}

💡 يرجى المحاولة مرة أخرى خلال دقائق قليلة
📞 إذا استمر الخطأ، راسل الدعم الفني

🔄 جرب الأوامر التالية:
• /start - إعادة تشغيل البوت
• /help - المساعدة
• /price - سعر الذهب
        """.strip()