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
class User:
    """User data model"""
    user_id: int
    username: str = None
    first_name: str = None
    last_name: str = None
    
    # Status & Authentication
    status: UserStatus = UserStatus.INACTIVE
    tier: UserTier = UserTier.BASIC
    activated_at: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    session_expires: Optional[datetime] = None
    
    # Usage Tracking
    analyses_today: int = 0
    total_analyses: int = 0
    last_analysis_at: Optional[datetime] = None
    
    # Rate Limiting
    hourly_requests: Dict[int, int] = field(default_factory=dict)  # hour -> count
    daily_requests: Dict[str, int] = field(default_factory=dict)   # date -> count
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    # Database fields
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    def is_active(self) -> bool:
        """Check if user is active and session is valid"""
        if self.status != UserStatus.ACTIVE:
            return False
        if self.session_expires and datetime.utcnow() > self.session_expires:
            return False
        return True
    
    def get_rate_limit(self) -> int:
        """Get rate limit based on user tier"""
        limits = {
            UserTier.BASIC: 5,
            UserTier.PREMIUM: 20,
            UserTier.VIP: 50
        }
        return limits.get(self.tier, 5)
    
    def can_request_analysis(self) -> tuple[bool, str]:
        """Check if user can request analysis"""
        if not self.is_active():
            return False, "غير مفعل - استخدم كلمة المرور للتفعيل"
        
        # Check daily limit
        today = datetime.utcnow().strftime("%Y-%m-%d")
        daily_count = self.daily_requests.get(today, 0)
        daily_limit = self.get_rate_limit() * 3  # 3x hourly limit per day
        
        if daily_count >= daily_limit:
            return False, f"تم تجاوز الحد اليومي ({daily_limit} تحليل/يوم)"
        
        # Check hourly limit
        current_hour = datetime.utcnow().hour
        hourly_count = self.hourly_requests.get(current_hour, 0)
        hourly_limit = self.get_rate_limit()
        
        if hourly_count >= hourly_limit:
            return False, f"تم تجاوز الحد الساعي ({hourly_limit} تحليل/ساعة)"
        
        return True, ""
    
    def record_analysis(self):
        """Record an analysis request"""
        now = datetime.utcnow()
        today = now.strftime("%Y-%m-%d")
        current_hour = now.hour
        
        # Update counters
        self.analyses_today += 1
        self.total_analyses += 1
        self.last_analysis_at = now
        
        # Update rate limiting counters
        if today not in self.daily_requests:
            self.daily_requests = {today: 0}  # Reset for new day
        self.daily_requests[today] += 1
        
        if current_hour not in self.hourly_requests:
            # Clean old hours (keep only last 24 hours)
            old_hours = [h for h in self.hourly_requests.keys() if h < current_hour - 24]
            for h in old_hours:
                del self.hourly_requests[h]
        
        self.hourly_requests[current_hour] = self.hourly_requests.get(current_hour, 0) + 1
        self.updated_at = now
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MongoDB storage"""
        data = asdict(self)
        # Convert enums to strings
        data['status'] = self.status.value
        data['tier'] = self.tier.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        """Create User from dictionary"""
        # Convert strings back to enums
        if 'status' in data and isinstance(data['status'], str):
            data['status'] = UserStatus(data['status'])
        if 'tier' in data and isinstance(data['tier'], str):
            data['tier'] = UserTier(data['tier'])
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