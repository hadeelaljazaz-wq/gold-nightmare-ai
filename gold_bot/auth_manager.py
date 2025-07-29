"""
Authentication Manager for Gold Analysis Application
إدارة المصادقة وتسجيل المستخدمين
"""
import logging
import hashlib
import secrets
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from motor.motor_asyncio import AsyncIOMotorCollection

from .models import (
    User, UserTier, UserStatus, UserRegistrationRequest, 
    UserLoginRequest, UserAuthResponse, UserSubscriptionUpdate
)
from .database import get_database

logger = logging.getLogger(__name__)

class AuthManager:
    """Manager for user authentication and registration"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.db = None
        self.users_collection: AsyncIOMotorCollection = None
        self.user_counter = 1000  # Start user IDs from 1000
        
    async def initialize(self):
        """Initialize auth manager"""
        try:
            self.db = self.db_manager.db
            self.users_collection = self.db.users
            
            # Create indexes for better performance
            await self.users_collection.create_index("email", unique=True)
            await self.users_collection.create_index("user_id", unique=True)
            await self.users_collection.create_index([("email", 1), ("status", 1)])
            
            # Initialize user counter
            last_user = await self.users_collection.find({}).sort("user_id", -1).limit(1).to_list(length=1)
            if last_user:
                self.user_counter = last_user[0]["user_id"] + 1
            
            logger.info("✅ Auth Manager initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Auth Manager: {e}")
            raise
    
    # Password Management
    
    def _hash_password(self, password: str) -> str:
        """Hash password with salt"""
        salt = secrets.token_hex(16)
        password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return f"{salt}:{password_hash}"
    
    def _verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        try:
            salt, password_hash = hashed.split(':')
            return hashlib.sha256((password + salt).encode()).hexdigest() == password_hash
        except Exception:
            return False
    
    def _validate_email(self, email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def _validate_password(self, password: str) -> Tuple[bool, str]:
        """Validate password strength"""
        if len(password) < 6:
            return False, "كلمة المرور يجب أن تكون 6 أحرف على الأقل"
        if not re.search(r'[A-Za-z]', password):
            return False, "كلمة المرور يجب أن تحتوي على حروف"
        if not re.search(r'[0-9]', password):
            return False, "كلمة المرور يجب أن تحتوي على أرقام"
        return True, ""
    
    # User Registration
    
    async def register_user(self, request: UserRegistrationRequest) -> UserAuthResponse:
        """Register new user"""
        try:
            # Validate email
            if not self._validate_email(request.email):
                return UserAuthResponse(
                    success=False,
                    error="البريد الإلكتروني غير صحيح"
                )
            
            # Check if email already exists
            existing_user = await self.users_collection.find_one({"email": request.email})
            if existing_user:
                return UserAuthResponse(
                    success=False,
                    error="البريد الإلكتروني مُسجل مسبقاً"
                )
            
            # Validate password
            password_valid, password_error = self._validate_password(request.password)
            if not password_valid:
                return UserAuthResponse(
                    success=False,
                    error=password_error
                )
            
            # Create new user
            password_hash = self._hash_password(request.password)
            
            new_user = User(
                user_id=self.user_counter,
                email=request.email.lower(),
                password_hash=password_hash,
                username=request.username,
                first_name=request.first_name,
                last_name=request.last_name,
                tier=UserTier.BASIC,  # Default tier
                status=UserStatus.ACTIVE,
                is_email_verified=True,  # Auto-verify for MVP
                subscription_start_date=datetime.utcnow(),
                activated_at=datetime.utcnow()
            )
            
            # Insert into database
            await self.users_collection.insert_one(new_user.to_dict())
            self.user_counter += 1
            
            logger.info(f"✅ New user registered: {request.email} (ID: {new_user.user_id})")
            
            return UserAuthResponse(
                success=True,
                user_id=new_user.user_id,
                email=new_user.email,
                tier=new_user.tier.value,
                daily_analyses_remaining=new_user.get_remaining_analyses_today()
            )
            
        except Exception as e:
            logger.error(f"❌ User registration failed: {e}")
            return UserAuthResponse(
                success=False,
                error="حدث خطأ في التسجيل، يرجى المحاولة مرة أخرى"
            )
    
    # User Login
    
    async def login_user(self, request: UserLoginRequest) -> UserAuthResponse:
        """Login user"""
        try:
            # Find user by email
            user_data = await self.users_collection.find_one({"email": request.email.lower()})
            if not user_data:
                return UserAuthResponse(
                    success=False,
                    error="البريد الإلكتروني غير مُسجل"
                )
            
            user = User.from_dict(user_data)
            
            # Check password
            if not self._verify_password(request.password, user.password_hash):
                return UserAuthResponse(
                    success=False,
                    error="كلمة المرور غير صحيحة"
                )
            
            # Check account status
            if not user.is_active():
                return UserAuthResponse(
                    success=False,
                    error="الحساب غير مفعل، تواصل مع الإدارة"
                )
            
            # Update last seen
            user.last_seen = datetime.utcnow()
            await self.users_collection.update_one(
                {"user_id": user.user_id},
                {"$set": {"last_seen": user.last_seen}}
            )
            
            logger.info(f"✅ User logged in: {request.email} (ID: {user.user_id})")
            
            return UserAuthResponse(
                success=True,
                user_id=user.user_id,
                email=user.email,
                tier=user.tier.value,
                daily_analyses_remaining=user.get_remaining_analyses_today()
            )
            
        except Exception as e:
            logger.error(f"❌ User login failed: {e}")
            return UserAuthResponse(
                success=False,
                error="حدث خطأ في تسجيل الدخول، يرجى المحاولة مرة أخرى"
            )
    
    # User Management
    
    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        try:
            user_data = await self.users_collection.find_one({"user_id": user_id})
            return User.from_dict(user_data) if user_data else None
        except Exception as e:
            logger.error(f"❌ Failed to get user {user_id}: {e}")
            return None
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        try:
            user_data = await self.users_collection.find_one({"email": email.lower()})
            return User.from_dict(user_data) if user_data else None
        except Exception as e:
            logger.error(f"❌ Failed to get user by email {email}: {e}")
            return None
    
    async def update_user(self, user: User) -> bool:
        """Update user in database"""
        try:
            user.updated_at = datetime.utcnow()
            result = await self.users_collection.update_one(
                {"user_id": user.user_id},
                {"$set": user.to_dict()}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"❌ Failed to update user {user.user_id}: {e}")
            return False
    
    # Analysis Management
    
    async def can_user_analyze(self, user_id: int) -> Tuple[bool, str, int]:
        """Check if user can perform analysis and return remaining count"""
        try:
            user = await self.get_user_by_id(user_id)
            if not user:
                return False, "المستخدم غير موجود", 0
            
            if not user.is_active():
                return False, "الحساب غير مفعل", 0
            
            if not user.can_analyze_today():
                limit = user.get_daily_limit()
                if limit == 1:
                    return False, "تم استنفاد التحليل المجاني اليوم. ترقية الاشتراك للمزيد", 0
                else:
                    return False, f"تم استنفاد حد التحليلات اليومية ({limit} تحليلات)", 0
            
            remaining = user.get_remaining_analyses_today()
            return True, "", remaining
            
        except Exception as e:
            logger.error(f"❌ Failed to check user analysis permission: {e}")
            return False, "حدث خطأ في النظام", 0
    
    async def record_analysis(self, user_id: int) -> bool:
        """Record user analysis"""
        try:
            user = await self.get_user_by_id(user_id)
            if not user:
                return False
            
            if user.increment_daily_analysis():
                await self.update_user(user)
                logger.info(f"✅ Analysis recorded for user {user_id}. Remaining: {user.get_remaining_analyses_today()}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Failed to record analysis for user {user_id}: {e}")
            return False
    
    # Admin Functions
    
    async def update_user_subscription(self, request: UserSubscriptionUpdate) -> Dict[str, Any]:
        """Update user subscription (admin only)"""
        try:
            # Validate tier
            try:
                new_tier = UserTier(request.new_tier)
            except ValueError:
                return {"success": False, "error": f"نوع اشتراك غير صحيح: {request.new_tier}"}
            
            user = await self.get_user_by_id(request.user_id)
            if not user:
                return {"success": False, "error": "المستخدم غير موجود"}
            
            old_tier = user.tier.value
            user.tier = new_tier
            user.subscription_start_date = datetime.utcnow()
            
            # Set subscription end date (1 year from now)
            user.subscription_end_date = datetime.utcnow() + timedelta(days=365)
            
            # Reset daily count for new subscription
            user.daily_analyses_count = 0
            user.daily_analyses_date = datetime.utcnow().strftime("%Y-%m-%d")
            
            success = await self.update_user(user)
            
            if success:
                logger.info(f"✅ Admin {request.admin_id} updated user {request.user_id} subscription: {old_tier} → {request.new_tier}")
                return {
                    "success": True,
                    "message": f"تم تحديث الاشتراك من {old_tier} إلى {request.new_tier}",
                    "old_tier": old_tier,
                    "new_tier": request.new_tier,
                    "new_daily_limit": user.get_daily_limit()
                }
            else:
                return {"success": False, "error": "فشل في تحديث قاعدة البيانات"}
            
        except Exception as e:
            logger.error(f"❌ Failed to update user subscription: {e}")
            return {"success": False, "error": str(e)}
    
    # Statistics
    
    async def get_auth_stats(self) -> Dict[str, Any]:
        """Get authentication statistics"""
        try:
            total_users = await self.users_collection.count_documents({})
            active_users = await self.users_collection.count_documents({"status": UserStatus.ACTIVE.value})
            
            # Users by tier
            basic_users = await self.users_collection.count_documents({"tier": UserTier.BASIC.value})
            premium_users = await self.users_collection.count_documents({"tier": UserTier.PREMIUM.value})
            vip_users = await self.users_collection.count_documents({"tier": UserTier.VIP.value})
            
            # Recent registrations (last 7 days)
            week_ago = datetime.utcnow() - timedelta(days=7)
            recent_registrations = await self.users_collection.count_documents({
                "created_at": {"$gte": week_ago}
            })
            
            return {
                "total_users": total_users,
                "active_users": active_users,
                "tier_distribution": {
                    "basic": basic_users,
                    "premium": premium_users,
                    "vip": vip_users
                },
                "recent_registrations_7d": recent_registrations,
                "last_updated": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get auth stats: {e}")
            return {"error": str(e)}

# Global auth manager instance
auth_manager: Optional[AuthManager] = None

async def get_auth_manager() -> AuthManager:
    """Get global auth manager instance"""
    global auth_manager
    if auth_manager is None:
        from .database import get_database
        db_manager = await get_database()
        auth_manager = AuthManager(db_manager)
        await auth_manager.initialize()
    return auth_manager

async def close_auth_manager():
    """Close global auth manager"""
    global auth_manager
    auth_manager = None