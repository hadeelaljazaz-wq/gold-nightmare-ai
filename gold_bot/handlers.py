"""
Gold Nightmare Bot Telegram Handlers
معالجات أوامر ورسائل تليجرام
"""
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from telegram import Update, Message, CallbackQuery
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler
from telegram.constants import ParseMode
from telegram.error import TelegramError

from .config import get_config, is_master_user
from .database import get_database
from .models import User, UserStatus, UserTier, AnalysisType
from .telegram_ui import TelegramUI, MessageFormatter
from .gold_price import get_current_gold_price
from .ai_manager import get_ai_manager

logger = logging.getLogger(__name__)

class BotHandlers:
    """Main handler class for all bot interactions"""
    
    def __init__(self):
        self.config = get_config()
        self.ui = TelegramUI()
        self.formatter = MessageFormatter()
        self.db = None
        self.ai_manager = None
    
    async def initialize(self):
        """Initialize handlers"""
        self.db = await get_database()
        self.ai_manager = await get_ai_manager()
        logger.info("✅ Bot handlers initialized")
    
    # Command Handlers
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        try:
            user_info = update.effective_user
            chat_id = update.effective_chat.id
            
            logger.info(f"👋 Start command from user {user_info.id}")
            
            # Get or create user
            user = await self.db.get_user(user_info.id)
            if not user:
                user = await self.db.create_user(
                    user_id=user_info.id,
                    username=user_info.username,
                    first_name=user_info.first_name,
                    last_name=user_info.last_name
                )
            
            # Update last seen
            user.last_seen = datetime.utcnow()
            await self.db.update_user(user)
            
            # Send welcome message
            welcome_text = self.formatter.format_welcome_message(user)
            keyboard = self.ui.get_main_menu_keyboard(user)
            
            await context.bot.send_message(
                chat_id=chat_id,
                text=welcome_text,
                reply_markup=keyboard,
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error(f"❌ Error in start command: {e}")
            await self._send_error_message(update, context, "فشل في بدء التشغيل")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        try:
            chat_id = update.effective_chat.id
            help_text = self.formatter.format_help_message()
            keyboard = self.ui.get_back_to_menu_keyboard()
            
            await context.bot.send_message(
                chat_id=chat_id,
                text=help_text,
                reply_markup=keyboard,
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error(f"❌ Error in help command: {e}")
            await self._send_error_message(update, context, "فشل في عرض المساعدة")
    
    async def price_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /price command"""
        try:
            chat_id = update.effective_chat.id
            
            # Send "fetching" message first
            status_msg = await context.bot.send_message(
                chat_id=chat_id,
                text="📊 جاري جلب أسعار الذهب اللحظية..."
            )
            
            # Get current price
            from .gold_price import get_gold_price_text
            price_text = await get_gold_price_text()
            
            # Update message with price
            keyboard = self.ui.get_back_to_menu_keyboard()
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=status_msg.message_id,
                text=price_text,
                reply_markup=keyboard,
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error(f"❌ Error in price command: {e}")
            await self._send_error_message(update, context, "فشل في جلب أسعار الذهب")
    
    async def quick_analysis_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /quick command"""
        try:
            user_info = update.effective_user
            await self._handle_analysis_request(update, context, user_info.id, AnalysisType.QUICK)
            
        except Exception as e:
            logger.error(f"❌ Error in quick analysis command: {e}")
            await self._send_error_message(update, context, "فشل في إجراء التحليل السريع")
    
    # Callback Query Handlers
    async def handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle all inline keyboard callbacks"""
        try:
            query = update.callback_query
            await query.answer()
            
            user_info = query.from_user
            data = query.data
            
            logger.info(f"🔘 Callback from user {user_info.id}: {data}")
            
            # Route callback to appropriate handler
            if data == "main_menu":
                await self._handle_main_menu(query, context, user_info.id)
            elif data == "price":
                await self._handle_price_callback(query, context)
            elif data.startswith("analysis_"):
                await self._handle_analysis_callback(query, context, user_info.id, data)
            elif data == "activate":
                await self._handle_activation_prompt(query, context)
            elif data == "settings":
                await self._handle_settings(query, context, user_info.id)
            elif data == "help":
                await self._handle_help_callback(query, context)
            elif data.startswith("admin_"):
                await self._handle_admin_callback(query, context, user_info.id, data)
            else:
                await query.edit_message_text("❌ خيار غير متاح")
                
        except Exception as e:
            logger.error(f"❌ Error in callback query: {e}")
            try:
                await query.edit_message_text("❌ حدث خطأ في معالجة الطلب")
            except:
                pass
    
    # Message Handlers
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages (activation, etc.)"""
        try:
            user_info = update.effective_user
            message_text = update.message.text.strip()
            
            # Check if it's activation password
            if message_text == self.config.activation_password:
                await self._handle_activation(update, context, user_info.id)
                return
            
            # Default response for other messages
            await update.message.reply_text(
                "ℹ️ استخدم الأوامر أو الأزرار للتفاعل مع البوت\n"
                "للمساعدة: /help",
                reply_markup=self.ui.get_main_menu_keyboard()
            )
            
        except Exception as e:
            logger.error(f"❌ Error in message handler: {e}")
            await self._send_error_message(update, context, "فشل في معالجة الرسالة")
    
    # Internal Handler Methods
    async def _handle_main_menu(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE, user_id: int):
        """Handle main menu callback"""
        user = await self.db.get_user(user_id)
        welcome_text = self.formatter.format_welcome_message(user) if user else "مرحباً! استخدم /start للبدء"
        keyboard = self.ui.get_main_menu_keyboard(user)
        
        await query.edit_message_text(
            text=welcome_text,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _handle_price_callback(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
        """Handle price callback"""
        await query.edit_message_text("📊 جاري جلب أسعار الذهب...")
        
        from .gold_price import get_gold_price_text
        price_text = await get_gold_price_text()
        keyboard = self.ui.get_back_to_menu_keyboard()
        
        await query.edit_message_text(
            text=price_text,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _handle_analysis_callback(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE, 
                                      user_id: int, data: str):
        """Handle analysis type callbacks"""
        analysis_type_map = {
            "analysis_quick": AnalysisType.QUICK,
            "analysis_detailed": AnalysisType.DETAILED,
            "analysis_chart": AnalysisType.CHART,
            "analysis_news": AnalysisType.NEWS,
            "analysis_forecast": AnalysisType.FORECAST
        }
        
        analysis_type = analysis_type_map.get(data)
        if not analysis_type:
            await query.edit_message_text("❌ نوع تحليل غير متاح")
            return
        
        # Update message to show loading
        await query.edit_message_text("🤖 جاري إجراء التحليل باستخدام الذكاء الاصطناعي...")
        
        await self._perform_analysis(query, context, user_id, analysis_type)
    
    async def _handle_activation_prompt(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
        """Handle activation prompt"""
        activation_text = self.formatter.format_activation_prompt()
        await query.edit_message_text(
            text=activation_text,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _handle_activation(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
        """Handle user activation"""
        try:
            # Activate user
            success = await self.db.activate_user(user_id)
            
            if success:
                user = await self.db.get_user(user_id)
                await update.message.reply_text(
                    "✅ **تم تفعيل حسابك بنجاح!**\n\n"
                    f"🎯 يمكنك الآن الاستمتاع بجميع ميزات {self.config.bot_signature}\n"
                    "📊 ابدأ بطلب تحليل أو سعر الذهب",
                    reply_markup=self.ui.get_main_menu_keyboard(user),
                    parse_mode=ParseMode.MARKDOWN
                )
                logger.info(f"✅ User {user_id} activated successfully")
            else:
                await update.message.reply_text("❌ فشل في التفعيل، يرجى المحاولة مرة أخرى")
                
        except Exception as e:
            logger.error(f"❌ Activation error: {e}")
            await update.message.reply_text("❌ حدث خطأ في التفعيل")
    
    async def _handle_settings(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE, user_id: int):
        """Handle settings callback"""
        user = await self.db.get_user(user_id)
        if not user:
            await query.edit_message_text("❌ لم يتم العثور على بيانات المستخدم")
            return
        
        stats_text = self.formatter.format_user_stats(user)
        keyboard = self.ui.get_settings_keyboard(user)
        
        await query.edit_message_text(
            text=stats_text,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _handle_help_callback(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
        """Handle help callback"""
        help_text = self.formatter.format_help_message()
        keyboard = self.ui.get_back_to_menu_keyboard()
        
        await query.edit_message_text(
            text=help_text,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def _handle_admin_callback(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE, 
                                   user_id: int, data: str):
        """Handle admin callbacks"""
        if not is_master_user(user_id):
            await query.edit_message_text("❌ غير مخول للوصول للوحة الإدارة")
            return
        
        if data == "admin_stats":
            await self._show_admin_stats(query, context)
        elif data == "admin_users":
            await self._show_user_stats(query, context)
        elif data == "admin_system":
            await self._show_system_status(query, context)
        else:
            await query.edit_message_text("🔧 لوحة الإدارة قيد التطوير")
    
    async def _perform_analysis(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE, 
                              user_id: int, analysis_type: AnalysisType):
        """Perform AI analysis"""
        try:
            # Get user and check permissions
            user = await self.db.get_user(user_id)
            if not user:
                await query.edit_message_text("❌ لم يتم العثور على بيانات المستخدم")
                return
            
            # Check rate limits
            can_request, reason = user.can_request_analysis()
            if not can_request:
                # Calculate cooldown for rate limit message
                from .models import RateLimiter
                is_limited, limit_reason, cooldown = RateLimiter.is_rate_limited(user)
                
                if is_limited:
                    limit_message = self.formatter.format_rate_limit_message(limit_reason, cooldown)
                    keyboard = self.ui.get_back_to_menu_keyboard()
                    await query.edit_message_text(
                        text=limit_message,
                        reply_markup=keyboard,
                        parse_mode=ParseMode.MARKDOWN
                    )
                    return
            
            # Get current gold price
            gold_price = await get_current_gold_price()
            
            # Generate analysis
            analysis = await self.ai_manager.generate_analysis(user_id, analysis_type, gold_price)
            
            if not analysis:
                await query.edit_message_text(
                    "❌ فشل في إجراء التحليل، يرجى المحاولة مرة أخرى",
                    reply_markup=self.ui.get_back_to_menu_keyboard()
                )
                return
            
            # Record analysis in user stats
            user.record_analysis()
            await self.db.update_user(user)
            
            # Save analysis to database
            await self.db.save_analysis(analysis)
            
            # Send analysis result
            keyboard = self.ui.get_back_to_menu_keyboard()
            
            # Split long messages if needed
            max_length = 4000
            content = analysis.content
            
            if len(content) <= max_length:
                await query.edit_message_text(
                    text=content,
                    reply_markup=keyboard,
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                # Split into multiple messages
                parts = [content[i:i+max_length] for i in range(0, len(content), max_length)]
                
                # Edit first message
                await query.edit_message_text(
                    text=parts[0],
                    parse_mode=ParseMode.MARKDOWN
                )
                
                # Send remaining parts
                for i, part in enumerate(parts[1:]):
                    if i == len(parts) - 2:  # Last part gets the keyboard
                        await context.bot.send_message(
                            chat_id=query.message.chat_id,
                            text=part,
                            reply_markup=keyboard,
                            parse_mode=ParseMode.MARKDOWN
                        )
                    else:
                        await context.bot.send_message(
                            chat_id=query.message.chat_id,
                            text=part,
                            parse_mode=ParseMode.MARKDOWN
                        )
            
            logger.info(f"✅ Analysis completed for user {user_id}: {analysis_type.value}")
            
        except Exception as e:
            logger.error(f"❌ Analysis error: {e}")
            await query.edit_message_text(
                text=self.formatter.format_error_message("فشل في إجراء التحليل"),
                reply_markup=self.ui.get_back_to_menu_keyboard(),
                parse_mode=ParseMode.MARKDOWN
            )
    
    async def _handle_analysis_request(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                     user_id: int, analysis_type: AnalysisType):
        """Handle analysis request from command"""
        try:
            # Send loading message
            loading_msg = await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="🤖 جاري إجراء التحليل..."
            )
            
            # Create fake query object for analysis
            class FakeQuery:
                def __init__(self, message):
                    self.message = message
                
                async def edit_message_text(self, text, reply_markup=None, parse_mode=None):
                    await context.bot.edit_message_text(
                        chat_id=self.message.chat_id,
                        message_id=self.message.message_id,
                        text=text,
                        reply_markup=reply_markup,
                        parse_mode=parse_mode
                    )
            
            fake_query = FakeQuery(loading_msg)
            await self._perform_analysis(fake_query, context, user_id, analysis_type)
            
        except Exception as e:
            logger.error(f"❌ Analysis request error: {e}")
            await self._send_error_message(update, context, "فشل في إجراء التحليل")
    
    async def _show_admin_stats(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
        """Show admin statistics"""
        try:
            stats = await self.db.get_bot_stats()
            
            stats_text = f"""
📊 **إحصائيات البوت**
━━━━━━━━━━━━━━━━━━━

👥 **المستخدمين:**
• إجمالي: {stats.total_users}
• نشط: {stats.active_users}
• أساسي: {stats.basic_users}
• مميز: {stats.premium_users}  
• ذهبي: {stats.vip_users}

📈 **التحليلات:**
• اليوم: {stats.analyses_today}
• الإجمالي: {stats.analyses_total}

⚡ **الأداء:**
• متوسط وقت الاستجابة: {stats.avg_response_time:.2f}s
• آخر تحديث: {stats.last_updated.strftime('%Y-%m-%d %H:%M')}
            """.strip()
            
            await query.edit_message_text(
                text=stats_text,
                reply_markup=self.ui.get_back_to_menu_keyboard(),
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error(f"❌ Admin stats error: {e}")
            await query.edit_message_text("❌ فشل في جلب الإحصائيات")
    
    async def _show_system_status(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
        """Show system status"""
        try:
            # Test API connections
            from .gold_price import get_price_manager
            price_manager = await get_price_manager()
            api_status = await price_manager.get_api_status()
            
            ai_stats = await self.ai_manager.get_ai_stats()
            
            status_text = "🔧 **حالة الأنظمة**\n━━━━━━━━━━━━━━━━━━━\n\n"
            
            # AI Status
            ai_emoji = "✅" if ai_stats.get('connected') else "❌"
            status_text += f"{ai_emoji} **Claude AI:** {'متصل' if ai_stats.get('connected') else 'غير متصل'}\n"
            status_text += f"• النموذج: {ai_stats.get('model', 'غير محدد')}\n\n"
            
            # Gold APIs Status
            status_text += "💰 **APIs أسعار الذهب:**\n"
            for api_name, status in api_status.items():
                emoji = "✅" if status.get('working') else "❌"
                status_text += f"{emoji} {api_name.title()}: {'يعمل' if status.get('working') else 'لا يعمل'}\n"
            
            await query.edit_message_text(
                text=status_text,
                reply_markup=self.ui.get_back_to_menu_keyboard(),
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error(f"❌ System status error: {e}")
            await query.edit_message_text("❌ فشل في جلب حالة الأنظمة")
    
    async def _send_error_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE, error_text: str):
        """Send formatted error message"""
        try:
            error_msg = self.formatter.format_error_message(error_text)
            keyboard = self.ui.get_back_to_menu_keyboard()
            
            if update.callback_query:
                await update.callback_query.edit_message_text(
                    text=error_msg,
                    reply_markup=keyboard,
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=error_msg,
                    reply_markup=keyboard,
                    parse_mode=ParseMode.MARKDOWN
                )
                
        except Exception as e:
            logger.error(f"❌ Error sending error message: {e}")

# Global handlers instance
handlers: Optional[BotHandlers] = None

def get_handlers() -> BotHandlers:
    """Get global handlers instance"""
    global handlers
    if handlers is None:
        handlers = BotHandlers()
    return handlers

def setup_handlers():
    """Setup all command and message handlers"""
    bot_handlers = get_handlers()
    
    return [
        # Commands
        CommandHandler("start", bot_handlers.start_command),
        CommandHandler("help", bot_handlers.help_command),
        CommandHandler("price", bot_handlers.price_command),
        CommandHandler("quick", bot_handlers.quick_analysis_command),
        
        # Callbacks
        CallbackQueryHandler(bot_handlers.handle_callback_query),
        
        # Messages  
        MessageHandler(None, bot_handlers.handle_message)
    ]