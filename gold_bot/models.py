"""
Gold Nightmare Bot Data Models
نماذج البيانات للمستخدمين والتحليلات
"""
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
import uuid

class UserTier(Enum):
    """User subscription tiers"""
    BASIC = "basic"
    PREMIUM = "premium" 
    VIP = "vip"

class AnalysisType(Enum):
    """Types of analysis available"""
    QUICK = "quick"
    DETAILED = "detailed"
    CHART = "chart"
    NEWS = "news"
    FORECAST = "forecast"

class UserStatus(Enum):
    """User activation status"""
    INACTIVE = "inactive"
    ACTIVE = "active"
    BLOCKED = "blocked"
    SUSPENDED = "suspended"

@dataclass
class AdminUser:
    """Admin user data model for admin panel access"""
    admin_id: str
    username: str
    email: str = None
    
    # Admin permissions
    can_manage_users: bool = True
    can_view_analytics: bool = True
    can_modify_settings: bool = False
    is_super_admin: bool = False
    
    # Metadata
    last_login: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    # Database fields
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

@dataclass
class AnalysisLog:
    """Detailed analysis log for admin tracking"""
    user_id: int
    analysis_type: AnalysisType
    success: bool
    
    # Request details
    processing_time: Optional[float] = None
    error_message: Optional[str] = None
    user_tier: UserTier = UserTier.BASIC
    
    # Context
    gold_price_at_request: Optional[float] = None
    tokens_used: Optional[int] = None
    
    # Timestamps
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    # Database fields
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MongoDB storage"""
        data = asdict(self)
        data['analysis_type'] = self.analysis_type.value
        data['user_tier'] = self.user_tier.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AnalysisLog':
        """Create AnalysisLog from dictionary"""
        if 'analysis_type' in data and isinstance(data['analysis_type'], str):
            data['analysis_type'] = AnalysisType(data['analysis_type'])
        if 'user_tier' in data and isinstance(data['user_tier'], str):
            data['user_tier'] = UserTier(data['user_tier'])
        return cls(**data)

@dataclass
class UserDailySummary:
    """Daily usage summary for each user"""
    user_id: int
    date: str  # YYYY-MM-DD format
    
    # Counts
    total_requests: int = 0
    successful_analyses: int = 0
    failed_analyses: int = 0
    
    # Performance
    avg_response_time: float = 0.0
    
    # Analysis breakdown
    quick_analyses: int = 0
    detailed_analyses: int = 0
    chart_analyses: int = 0
    news_analyses: int = 0
    forecast_analyses: int = 0
    
    # Database fields
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)

@dataclass
class BotStats:
    """Bot usage statistics"""
    total_users: int = 0
    active_users: int = 0
    analyses_today: int = 0
    analyses_total: int = 0
    
    # User tier breakdown
    basic_users: int = 0
    premium_users: int = 0
    vip_users: int = 0
    
    # Status breakdown
    active_users_count: int = 0
    inactive_users_count: int = 0
    blocked_users_count: int = 0
    
    # API usage
    gold_api_calls: int = 0
    claude_api_calls: int = 0
    
    # Performance
    avg_response_time: float = 0.0
    uptime_hours: float = 0.0
    
    # Error tracking
    total_errors: int = 0
    api_errors: int = 0
    
    # Timestamps
    last_updated: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)

@dataclass
class User:
    """Enhanced User data model with authentication and subscription system"""
    user_id: int
    email: str
    password_hash: str
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    
    # Subscription Management
    tier: UserTier = UserTier.BASIC
    subscription_start_date: Optional[datetime] = None
    subscription_end_date: Optional[datetime] = None
    
    # Usage Tracking
    total_analyses: int = 0
    daily_analyses_count: int = 0
    daily_analyses_date: Optional[str] = None  # YYYY-MM-DD format
    
    # Account Status
    status: UserStatus = UserStatus.ACTIVE
    is_email_verified: bool = False
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    last_seen: Optional[datetime] = None
    activated_at: Optional[datetime] = None
    
    # Database fields
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    def get_daily_limit(self) -> int:
        """Get daily analysis limit based on subscription tier"""
        if self.tier == UserTier.BASIC:
            return 1  # 1 analysis per day
        elif self.tier == UserTier.PREMIUM:
            return 5  # 5 analyses per day
        elif self.tier == UserTier.VIP:
            return -1  # Unlimited (-1 means no limit)
        return 1
    
    def get_remaining_analyses_today(self) -> int:
        """Get remaining analyses for today"""
        today = datetime.utcnow().strftime("%Y-%m-%d")
        
        # Reset daily count if it's a new day
        if self.daily_analyses_date != today:
            self.daily_analyses_count = 0
            self.daily_analyses_date = today
        
        limit = self.get_daily_limit()
        if limit == -1:  # Unlimited
            return -1
        
        remaining = limit - self.daily_analyses_count
        return max(0, remaining)
    
    def can_analyze_today(self) -> bool:
        """Check if user can perform analysis today"""
        remaining = self.get_remaining_analyses_today()
        return remaining != 0  # -1 (unlimited) or > 0
    
    def increment_daily_analysis(self) -> bool:
        """Increment daily analysis count, return True if successful"""
        if not self.can_analyze_today():
            return False
        
        today = datetime.utcnow().strftime("%Y-%m-%d")
        if self.daily_analyses_date != today:
            self.daily_analyses_count = 0
            self.daily_analyses_date = today
        
        self.daily_analyses_count += 1
        self.total_analyses += 1
        self.updated_at = datetime.utcnow()
        return True
    
    def get_tier_features(self) -> Dict[str, Any]:
        """Get features available for current tier"""
        features = {
            UserTier.BASIC: {
                "daily_analyses": 1,
                "save_history": False,
                "priority_support": False,
                "advanced_charts": False,
                "voice_analysis": False,
                "custom_indicators": False
            },
            UserTier.PREMIUM: {
                "daily_analyses": 5,
                "save_history": True,
                "priority_support": False,
                "advanced_charts": True,
                "voice_analysis": False,
                "custom_indicators": False
            },
            UserTier.VIP: {
                "daily_analyses": -1,  # Unlimited
                "save_history": True,
                "priority_support": True,
                "advanced_charts": True,
                "voice_analysis": True,
                "custom_indicators": True
            }
        }
        return features.get(self.tier, features[UserTier.BASIC])
    
    def is_active(self) -> bool:
        """Check if user account is active"""
        return self.status == UserStatus.ACTIVE
    
    def get_rate_limit(self) -> int:
        """Get rate limit per hour based on tier"""
        rate_limits = {
            UserTier.BASIC: 5,
            UserTier.PREMIUM: 20,
            UserTier.VIP: 50
        }
        return rate_limits.get(self.tier, 5)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MongoDB storage"""
        data = asdict(self)
        data['tier'] = self.tier.value
        data['status'] = self.status.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        """Create User from dictionary"""
        if 'tier' in data and isinstance(data['tier'], str):
            data['tier'] = UserTier(data['tier'])
        if 'status' in data and isinstance(data['status'], str):
            data['status'] = UserStatus(data['status'])
        return cls(**data)

@dataclass  
class GoldPrice:
    """Gold price data model"""
    price_usd: float
    price_change: float
    price_change_pct: float
    
    # Price details
    ask: Optional[float] = None
    bid: Optional[float] = None
    high_24h: Optional[float] = None
    low_24h: Optional[float] = None
    
    # Metadata
    source: str = "goldapi"
    currency: str = "USD"
    unit: str = "oz"  # ounce
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    # Database fields
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    def to_arabic_text(self) -> str:
        """Convert to Arabic formatted text"""
        change_emoji = "📈" if self.price_change > 0 else "📉" if self.price_change < 0 else "➡️"
        change_color = "🟢" if self.price_change > 0 else "🔴" if self.price_change < 0 else "🟡"
        
        text = f"""
🏆 **سعر الذهب الحالي**
━━━━━━━━━━━━━━━━━━━━

💰 السعر: **${self.price_usd:.2f}** لكل أونصة
{change_emoji} التغيير: **{self.price_change:+.2f}** ({self.price_change_pct:+.2f}%) {change_color}

📊 **تفاصيل السوق:**
• السعر العالي: ${self.high_24h:.2f} (24س)
• السعر المنخفض: ${self.low_24h:.2f} (24س)  
• سعر الطلب: ${self.ask:.2f}
• سعر البيع: ${self.bid:.2f}

⏰ آخر تحديث: {self.timestamp.strftime("%Y-%m-%d %H:%M")} UTC
📡 المصدر: {self.source.upper()}
        """.strip()
        
        return text

@dataclass
class Analysis:
    """Analysis data model"""
    user_id: int
    analysis_type: AnalysisType
    content: str
    
    # Gold price context
    gold_price: Optional[float] = None
    price_change: Optional[float] = None
    
    # Analysis metadata
    model_used: str = "claude-sonnet-4-20250514"
    language: str = "arabic"
    tokens_used: Optional[int] = None
    processing_time: Optional[float] = None
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    # Database fields
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MongoDB storage"""
        data = asdict(self)
        data['analysis_type'] = self.analysis_type.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Analysis':
        """Create Analysis from dictionary"""
        if 'analysis_type' in data and isinstance(data['analysis_type'], str):
            data['analysis_type'] = AnalysisType(data['analysis_type'])
        return cls(**data)

@dataclass
class BotStats:
    """Bot usage statistics"""
    total_users: int = 0
    active_users: int = 0
    analyses_today: int = 0
    analyses_total: int = 0
    
    # User tier breakdown
    basic_users: int = 0
    premium_users: int = 0
    vip_users: int = 0
    
    # API usage
    gold_api_calls: int = 0
    claude_api_calls: int = 0
    
    # Performance
    avg_response_time: float = 0.0
    uptime_hours: float = 0.0
    
    # Timestamps
    last_updated: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)

# Rate limiting helpers
class RateLimiter:
    """Rate limiting utility"""
    
    @staticmethod
    def is_rate_limited(user: User) -> tuple[bool, str, int]:
        """
        Check if user is rate limited
        Returns: (is_limited, reason, cooldown_seconds)
        """
        can_request, reason = user.can_request_analysis()
        if not can_request:
            if "ساعي" in reason:
                # Calculate cooldown until next hour
                now = datetime.utcnow()
                next_hour = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
                cooldown = int((next_hour - now).total_seconds())
                return True, reason, cooldown
            elif "يومي" in reason:
                # Calculate cooldown until next day
                now = datetime.utcnow()
                next_day = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
                cooldown = int((next_day - now).total_seconds())
                return True, reason, cooldown
            else:
                return True, reason, 0
        
        return False, "", 0

# Cache keys
class CacheKeys:
    """Cache key constants"""
    GOLD_PRICE = "gold_price:latest"
    GOLD_PRICE_HISTORY = "gold_price:history:{date}"
    ANALYSIS_CACHE = "analysis:{user_id}:{type}:{hash}"
    USER_SESSION = "user:session:{user_id}"
    BOT_STATS = "bot:stats"
    
    @staticmethod
    def analysis_key(user_id: int, analysis_type: AnalysisType, content_hash: str) -> str:
        return f"analysis:{user_id}:{analysis_type.value}:{content_hash}"