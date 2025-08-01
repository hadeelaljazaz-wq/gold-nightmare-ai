"""
Gold Nightmare Bot Configuration
جميع إعدادات البوت والتكوين
"""
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

@dataclass
class BotConfig:
    """Bot configuration class"""
    
    # Required fields first
    telegram_token: str
    master_user_id: int  
    activation_password: str
    claude_api_key: str
    gold_api_token: str
    
    # Optional fields with defaults
    session_timeout: int = 86400
    claude_model: str = "claude-sonnet-4-20250514"
    claude_max_tokens: int = 4000
    claude_temperature: float = 0.7
    metals_api_key: Optional[str] = None
    forex_api_key: Optional[str] = None
    prompt_language: str = "arabic"
    bot_signature: str = "Gold Nightmare Bot"
    price_cache_ttl: int = 300
    analysis_cache_ttl: int = 1800
    rate_limit_basic: int = 5
    rate_limit_premium: int = 20
    rate_limit_vip: int = 50
    mongo_url: str = "mongodb://localhost:27017"
    db_name: str = "gold_nightmare_bot"

def load_config() -> BotConfig:
    """Load configuration from environment variables"""
    
    # Load .env file if it exists
    env_path = os.path.join(os.path.dirname(__file__), '..', 'backend', '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
    
    try:
        config = BotConfig(
            # Telegram Settings
            telegram_token=os.environ['TELEGRAM_BOT_TOKEN'],
            master_user_id=int(os.environ['MASTER_USER_ID']),
            activation_password=os.environ['ACTIVATION_PASSWORD'],
            session_timeout=int(os.environ.get('SESSION_TIMEOUT', 86400)),
            
            # Claude AI Settings
            claude_api_key=os.environ['CLAUDE_API_KEY'],
            claude_model=os.environ.get('CLAUDE_MODEL', 'claude-sonnet-4-20250514'),
            claude_max_tokens=int(os.environ.get('CLAUDE_MAX_TOKENS', 4000)),
            claude_temperature=float(os.environ.get('CLAUDE_TEMPERATURE', 0.7)),
            
            # Gold API Settings
            gold_api_token=os.environ['GOLD_API_TOKEN'],
            metals_api_key=os.environ.get('METALS_API_KEY'),
            forex_api_key=os.environ.get('FOREX_API_KEY'),
            
            # Bot Behavior
            prompt_language=os.environ.get('PROMPT_LANGUAGE', 'arabic'),
            bot_signature=os.environ.get('BOT_SIGNATURE', 'Gold Nightmare – عدي'),
            
            # Cache & Rate Limiting - Updated to 15 minutes for gold price
            price_cache_ttl=int(os.environ.get('PRICE_CACHE_TTL', 900)),  # 15 minutes
            analysis_cache_ttl=int(os.environ.get('ANALYSIS_CACHE_TTL', 1800)),
            rate_limit_basic=int(os.environ.get('RATE_LIMIT_BASIC', 5)),
            rate_limit_premium=int(os.environ.get('RATE_LIMIT_PREMIUM', 20)),
            rate_limit_vip=int(os.environ.get('RATE_LIMIT_VIP', 50)),
            
            # Database
            mongo_url=os.environ.get('MONGO_URL', 'mongodb://localhost:27017'),
            db_name=os.environ.get('DB_NAME', 'gold_nightmare_bot')
        )
        
        logger.info("✅ Configuration loaded successfully")
        return config
        
    except KeyError as e:
        logger.error(f"❌ Missing required environment variable: {e}")
        raise ValueError(f"Missing required environment variable: {e}")
    except ValueError as e:
        logger.error(f"❌ Invalid configuration value: {e}")
        raise

# Global config instance
CONFIG = None

def get_config() -> BotConfig:
    """Get global configuration instance"""
    global CONFIG
    if CONFIG is None:
        CONFIG = load_config()
    return CONFIG

# Quick access to common settings
def get_telegram_token() -> str:
    return get_config().telegram_token

def get_claude_api_key() -> str:
    return get_config().claude_api_key

def is_master_user(user_id: int) -> bool:
    return user_id == get_config().master_user_id