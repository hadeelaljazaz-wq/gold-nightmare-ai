"""
Gold Nightmare Bot Database Manager
إدارة قاعدة البيانات والتخزين المستمر
"""
import asyncio
from typing import Optional, List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
from datetime import datetime, timedelta
import logging

from .config import get_config
from .models import User, Analysis, BotStats, UserStatus, UserTier, AnalysisType

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Async MongoDB database manager"""
    
    def __init__(self):
        self.config = get_config()
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None
        self.users: Optional[AsyncIOMotorCollection] = None
        self.analyses: Optional[AsyncIOMotorCollection] = None
        self.stats: Optional[AsyncIOMotorCollection] = None
        self.gold_prices: Optional[AsyncIOMotorCollection] = None
    
    async def initialize(self):
        """Initialize database connection and collections"""
        try:
            self.client = AsyncIOMotorClient(self.config.mongo_url)
            self.db = self.client[self.config.db_name]
            
            # Initialize collections
            self.users = self.db.users
            self.analyses = self.db.analyses  
            self.stats = self.db.stats
            self.gold_prices = self.db.gold_prices
            
            # Create indexes for performance
            await self._create_indexes()
            
            logger.info("✅ Database initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            raise
    
    async def close(self):
        """Close database connection"""
        if self.client:
            self.client.close()
            logger.info("🔚 Database connection closed")
    
    async def _create_indexes(self):
        """Create database indexes for better performance"""
        try:
            # Users indexes
            await self.users.create_index("user_id", unique=True)
            await self.users.create_index([("status", 1), ("tier", 1)])
            await self.users.create_index("last_seen")
            
            # Analyses indexes
            await self.analyses.create_index([("user_id", 1), ("created_at", -1)])
            await self.analyses.create_index("analysis_type")
            await self.analyses.create_index("created_at")
            
            # Gold prices indexes
            await self.gold_prices.create_index([("timestamp", -1)])
            await self.gold_prices.create_index("source")
            
            logger.info("✅ Database indexes created")
            
        except Exception as e:
            logger.error(f"❌ Failed to create indexes: {e}")
    
    # User management methods
    async def get_user(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        try:
            user_data = await self.users.find_one({"user_id": user_id})
            if user_data:
                return User.from_dict(user_data)
            return None
            
        except Exception as e:
            logger.error(f"❌ Failed to get user {user_id}: {e}")
            return None
    
    async def create_user(self, user_id: int, username: str = None, 
                         first_name: str = None, last_name: str = None) -> User:
        """Create new user"""
        try:
            user = User(
                user_id=user_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
                status=UserStatus.INACTIVE,
                tier=UserTier.BASIC
            )
            
            await self.users.insert_one(user.to_dict())
            logger.info(f"✅ Created new user: {user_id}")
            return user
            
        except Exception as e:
            logger.error(f"❌ Failed to create user {user_id}: {e}")
            raise
    
    async def update_user(self, user: User) -> bool:
        """Update existing user"""
        try:
            user.updated_at = datetime.utcnow()
            result = await self.users.update_one(
                {"user_id": user.user_id},
                {"$set": user.to_dict()}
            )
            
            if result.modified_count > 0:
                logger.info(f"✅ Updated user: {user.user_id}")
                return True
            else:
                logger.warning(f"⚠️ No changes made to user: {user.user_id}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to update user {user.user_id}: {e}")
            return False
    
    async def activate_user(self, user_id: int) -> bool:
        """Activate user with session expiration"""
        try:
            session_expires = datetime.utcnow() + timedelta(seconds=self.config.session_timeout)
            
            result = await self.users.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "status": UserStatus.ACTIVE.value,
                        "activated_at": datetime.utcnow(),
                        "session_expires": session_expires,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count > 0:
                logger.info(f"✅ Activated user: {user_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"❌ Failed to activate user {user_id}: {e}")
            return False
    
    async def get_all_users(self, status: Optional[UserStatus] = None) -> List[User]:
        """Get all users, optionally filtered by status"""
        try:
            query = {}
            if status:
                query["status"] = status.value
            
            cursor = self.users.find(query)
            users = []
            
            async for user_data in cursor:
                try:
                    user = User.from_dict(user_data)
                    users.append(user)
                except Exception as e:
                    logger.error(f"❌ Failed to parse user data: {e}")
                    continue
            
            return users
            
        except Exception as e:
            logger.error(f"❌ Failed to get users: {e}")
            return []
    
    # Analysis management methods
    async def save_analysis(self, analysis: Analysis) -> bool:
        """Save analysis to database"""
        try:
            await self.analyses.insert_one(analysis.to_dict())
            logger.info(f"✅ Saved analysis: {analysis.id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to save analysis: {e}")
            return False
    
    async def get_user_analyses(self, user_id: int, limit: int = 10) -> List[Analysis]:
        """Get user's recent analyses"""
        try:
            cursor = self.analyses.find(
                {"user_id": user_id}
            ).sort("created_at", -1).limit(limit)
            
            analyses = []
            async for analysis_data in cursor:
                try:
                    analysis = Analysis.from_dict(analysis_data)
                    analyses.append(analysis)
                except Exception as e:
                    logger.error(f"❌ Failed to parse analysis data: {e}")
                    continue
            
            return analyses
            
        except Exception as e:
            logger.error(f"❌ Failed to get user analyses: {e}")
            return []
    
    async def get_analyses_by_type(self, analysis_type: AnalysisType, limit: int = 50) -> List[Analysis]:
        """Get recent analyses by type"""
        try:
            cursor = self.analyses.find(
                {"analysis_type": analysis_type.value}
            ).sort("created_at", -1).limit(limit)
            
            analyses = []
            async for analysis_data in cursor:
                try:
                    analysis = Analysis.from_dict(analysis_data)
                    analyses.append(analysis)
                except Exception as e:
                    logger.error(f"❌ Failed to parse analysis data: {e}")
                    continue
            
            return analyses
            
        except Exception as e:
            logger.error(f"❌ Failed to get analyses by type: {e}")
            return []
    
    # Statistics methods
    async def get_bot_stats(self) -> BotStats:
        """Get comprehensive bot statistics"""
        try:
            # Count users by status and tier
            total_users = await self.users.count_documents({})
            active_users = await self.users.count_documents({"status": UserStatus.ACTIVE.value})
            
            basic_users = await self.users.count_documents({"tier": UserTier.BASIC.value})
            premium_users = await self.users.count_documents({"tier": UserTier.PREMIUM.value})
            vip_users = await self.users.count_documents({"tier": UserTier.VIP.value})
            
            # Count analyses
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            analyses_today = await self.analyses.count_documents({"created_at": {"$gte": today_start}})
            analyses_total = await self.analyses.count_documents({})
            
            # Calculate average response time (from last 100 analyses)
            pipeline = [
                {"$match": {"processing_time": {"$ne": None}}},
                {"$sort": {"created_at": -1}},
                {"$limit": 100},
                {"$group": {"_id": None, "avg_time": {"$avg": "$processing_time"}}}
            ]
            
            avg_time_result = await self.analyses.aggregate(pipeline).to_list(1)
            avg_response_time = avg_time_result[0]["avg_time"] if avg_time_result else 0.0
            
            stats = BotStats(
                total_users=total_users,
                active_users=active_users,
                analyses_today=analyses_today,
                analyses_total=analyses_total,
                basic_users=basic_users,
                premium_users=premium_users,
                vip_users=vip_users,
                avg_response_time=avg_response_time,
                last_updated=datetime.utcnow()
            )
            
            # Save stats to database
            await self.stats.replace_one(
                {"type": "bot_stats"},
                {**stats.to_dict(), "type": "bot_stats"},
                upsert=True
            )
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ Failed to get bot stats: {e}")
            return BotStats()
    
    async def cleanup_old_data(self):
        """Clean up old data to maintain performance"""
        try:
            # Remove old gold prices (keep last 30 days)
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            
            result = await self.gold_prices.delete_many({"timestamp": {"$lt": cutoff_date}})
            if result.deleted_count > 0:
                logger.info(f"🧹 Cleaned up {result.deleted_count} old gold price records")
            
            # Remove expired user sessions
            expired_users = await self.users.update_many(
                {
                    "status": UserStatus.ACTIVE.value,
                    "session_expires": {"$lt": datetime.utcnow()}
                },
                {"$set": {"status": UserStatus.INACTIVE.value}}
            )
            
            if expired_users.modified_count > 0:
                logger.info(f"🧹 Deactivated {expired_users.modified_count} expired user sessions")
                
        except Exception as e:
            logger.error(f"❌ Cleanup failed: {e}")

# Global database instance
db_manager: Optional[DatabaseManager] = None

async def get_database() -> DatabaseManager:
    """Get global database manager instance"""
    global db_manager
    if db_manager is None:
        db_manager = DatabaseManager()
        await db_manager.initialize()
    return db_manager

async def close_database():
    """Close global database connection"""
    global db_manager
    if db_manager:
        await db_manager.close()
        db_manager = None