"""
Gold Nightmare Bot - Main Bot Application
التطبيق الرئيسي لبوت Gold Nightmare
"""
import asyncio
import logging
import signal
from datetime import datetime
from typing import Optional, Dict, Any

from telegram.ext import Application, ApplicationBuilder
from telegram.error import TelegramError

from .config import get_config
from .database import get_database, close_database
from .cache import get_cache_manager, close_cache_manager
from .gold_price import get_price_manager, close_price_manager
from .ai_manager import get_ai_manager
from .handlers import get_handlers, setup_handlers

logger = logging.getLogger(__name__)

class GoldNightmareBot:
    """Main Gold Nightmare Bot application"""
    
    def __init__(self):
        self.config = get_config()
        self.application: Optional[Application] = None
        self.running = False
        self.handlers = None
        
        # Component managers
        self.db = None
        self.cache_manager = None
        self.price_manager = None
        self.ai_manager = None
        
        self.start_time = datetime.utcnow()
        
        logger.info(f"🚀 Initializing {self.config.bot_signature}")
    
    async def initialize(self):
        """Initialize all bot components"""
        try:
            logger.info("🔧 Initializing bot components...")
            
            # Initialize database
            self.db = await get_database()
            logger.info("✅ Database initialized")
            
            # Initialize cache
            self.cache_manager = await get_cache_manager()
            logger.info("✅ Cache manager initialized")
            
            # Initialize price manager
            self.price_manager = await get_price_manager()
            logger.info("✅ Price manager initialized")
            
            # Initialize AI manager
            self.ai_manager = await get_ai_manager()
            logger.info("✅ AI manager initialized")
            
            # Initialize handlers
            self.handlers = get_handlers()
            await self.handlers.initialize()
            logger.info("✅ Handlers initialized")
            
            # Build Telegram application
            self.application = (
                ApplicationBuilder()
                .token(self.config.telegram_token)
                .build()
            )
            
            # Add handlers
            handler_list = setup_handlers()
            for handler in handler_list:
                self.application.add_handler(handler)
            
            logger.info("✅ Telegram application built and configured")
            
            # Test connections
            await self._test_connections()
            
            logger.info("🎉 Bot initialization completed successfully!")
            
        except Exception as e:
            logger.error(f"❌ Bot initialization failed: {e}")
            raise
    
    async def start(self):
        """Start the bot"""
        try:
            if not self.application:
                await self.initialize()
            
            logger.info("🚀 Starting Gold Nightmare Bot...")
            
            # Start the application
            await self.application.initialize()
            await self.application.start()
            
            # Start polling
            await self.application.updater.start_polling(
                drop_pending_updates=True,
                poll_interval=1.0,
                timeout=30,
                read_timeout=15,
                write_timeout=15,
                connect_timeout=15
            )
            
            self.running = True
            self.start_time = datetime.utcnow()
            
            logger.info("✅ Bot started successfully! Listening for updates...")
            
            # Setup graceful shutdown
            self._setup_signal_handlers()
            
            # Start background tasks
            asyncio.create_task(self._background_cleanup_task())
            
            # Keep the bot running
            await self._keep_alive()
            
        except Exception as e:
            logger.error(f"❌ Failed to start bot: {e}")
            raise
    
    async def stop(self):
        """Stop the bot gracefully"""
        try:
            logger.info("🛑 Stopping Gold Nightmare Bot...")
            
            self.running = False
            
            if self.application:
                # Stop polling
                if self.application.updater:
                    await self.application.updater.stop()
                
                # Stop application
                await self.application.stop()
                await self.application.shutdown()
            
            # Close all managers
            await self._cleanup_resources()
            
            logger.info("✅ Bot stopped successfully")
            
        except Exception as e:
            logger.error(f"❌ Error stopping bot: {e}")
    
    async def _test_connections(self):
        """Test all external connections"""
        logger.info("🔍 Testing external connections...")
        
        try:
            # Test Telegram API
            bot_info = await self.application.bot.get_me()
            logger.info(f"✅ Telegram API: Connected as @{bot_info.username}")
            
            # Test Claude AI
            ai_connected, ai_status = await self.ai_manager.test_ai_connection()
            logger.info(f"{'✅' if ai_connected else '❌'} Claude AI: {ai_status}")
            
            # Test Gold Price APIs
            api_status = await self.price_manager.test_apis()
            for api_name, working in api_status.items():
                logger.info(f"{'✅' if working else '❌'} {api_name.title()} API: {'Working' if working else 'Failed'}")
            
            # Test database
            try:
                stats = await self.db.get_bot_stats()
                logger.info(f"✅ Database: Connected ({stats.total_users} total users)")
            except Exception as e:
                logger.error(f"❌ Database test failed: {e}")
                
            logger.info("🎯 Connection tests completed")
            
        except Exception as e:
            logger.error(f"❌ Connection test failed: {e}")
            raise
    
    def _setup_signal_handlers(self):
        """Setup graceful shutdown on SIGTERM/SIGINT"""
        def signal_handler(signum, frame):
            logger.info(f"📡 Received signal {signum}, initiating graceful shutdown...")
            asyncio.create_task(self.stop())
        
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
    
    async def _keep_alive(self):
        """Keep the bot alive while running"""
        try:
            while self.running:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            logger.info("🛑 Keep-alive task cancelled")
    
    async def _background_cleanup_task(self):
        """Background task for periodic cleanup"""
        while self.running:
            try:
                await asyncio.sleep(3600)  # Run every hour
                
                if self.db:
                    await self.db.cleanup_old_data()
                
                logger.info("🧹 Background cleanup completed")
                
            except asyncio.CancelledError:
                logger.info("🛑 Cleanup task cancelled")
                break
            except Exception as e:
                logger.error(f"❌ Background cleanup error: {e}")
    
    async def _cleanup_resources(self):
        """Cleanup all resources"""
        try:
            # Close managers in reverse order
            await close_price_manager()
            await close_cache_manager()
            await close_database()
            
            logger.info("🧹 Resources cleaned up")
            
        except Exception as e:
            logger.error(f"❌ Resource cleanup error: {e}")
    
    def is_running(self) -> bool:
        """Check if bot is running"""
        return self.running
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get bot runtime statistics"""
        try:
            uptime = datetime.utcnow() - self.start_time
            uptime_hours = uptime.total_seconds() / 3600
            
            db_stats = await self.db.get_bot_stats() if self.db else None
            
            return {
                "bot_name": self.config.bot_signature,
                "running": self.running,
                "uptime_hours": round(uptime_hours, 2),
                "start_time": self.start_time.isoformat(),
                "total_users": db_stats.total_users if db_stats else 0,
                "active_users": db_stats.active_users if db_stats else 0,
                "analyses_today": db_stats.analyses_today if db_stats else 0,
                "analyses_total": db_stats.analyses_total if db_stats else 0
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting stats: {e}")
            return {"error": str(e)}
    
    async def broadcast_message(self, message: str) -> int:
        """Broadcast message to all active users"""
        try:
            if not self.db:
                raise ValueError("Database not initialized")
            
            users = await self.db.get_all_users(status=None)  # Get all users
            sent_count = 0
            
            for user in users:
                try:
                    await self.application.bot.send_message(
                        chat_id=user.user_id,
                        text=f"📢 **إعلان من {self.config.bot_signature}**\n\n{message}",
                        parse_mode="Markdown"
                    )
                    sent_count += 1
                    
                    # Small delay to avoid rate limiting
                    await asyncio.sleep(0.1)
                    
                except TelegramError as e:
                    logger.warning(f"⚠️ Failed to send broadcast to user {user.user_id}: {e}")
                    continue
            
            logger.info(f"📢 Broadcast sent to {sent_count}/{len(users)} users")
            return sent_count
            
        except Exception as e:
            logger.error(f"❌ Broadcast error: {e}")
            return 0

# Main entry point for direct execution
async def main():
    """Main function to run the bot directly"""
    try:
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('/var/log/supervisor/gold_bot.log'),
                logging.StreamHandler()
            ]
        )
        
        # Create and start bot
        bot = GoldNightmareBot()
        await bot.start()
        
    except KeyboardInterrupt:
        logger.info("👋 Bot stopped by user")
    except Exception as e:
        logger.error(f"💥 Bot crashed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())