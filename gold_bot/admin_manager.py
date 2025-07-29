"""
Admin Panel Manager for Gold Nightmare Bot
إدارة لوحة تحكم البوت والإحصائيات
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from motor.motor_asyncio import AsyncIOMotorCollection
import asyncio

from .models import (
    User, UserTier, UserStatus, AdminUser, AnalysisLog, 
    UserDailySummary, BotStats, AnalysisType
)
from .database import get_database

logger = logging.getLogger(__name__)

class AdminManager:
    """Manager for admin panel operations"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.db = None
        
        # Collection references
        self.users_collection: AsyncIOMotorCollection = None
        self.analysis_logs_collection: AsyncIOMotorCollection = None
        self.daily_summaries_collection: AsyncIOMotorCollection = None
        self.admin_users_collection: AsyncIOMotorCollection = None
        
    async def initialize(self):
        """Initialize admin manager"""
        try:
            self.db = self.db_manager.db
            
            # Initialize collections
            self.users_collection = self.db.users
            self.analysis_logs_collection = self.db.analysis_logs
            self.daily_summaries_collection = self.db.daily_summaries
            self.admin_users_collection = self.db.admin_users
            
            # Create indexes for better performance
            await self._create_indexes()
            
            logger.info("✅ Admin Manager initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Admin Manager: {e}")
            raise
    
    async def _create_indexes(self):
        """Create database indexes for better performance"""
        try:
            # Users indexes
            await self.users_collection.create_index("user_id", unique=True)
            await self.users_collection.create_index([("status", 1), ("tier", 1)])
            await self.users_collection.create_index("last_seen")
            
            # Analysis logs indexes
            await self.analysis_logs_collection.create_index([("user_id", 1), ("timestamp", -1)])
            await self.analysis_logs_collection.create_index("timestamp")
            await self.analysis_logs_collection.create_index("analysis_type")
            
            # Daily summaries indexes
            await self.daily_summaries_collection.create_index([("user_id", 1), ("date", 1)], unique=True)
            await self.daily_summaries_collection.create_index("date")
            
            logger.info("✅ Database indexes created")
            
        except Exception as e:
            logger.warning(f"⚠️ Index creation warning: {e}")
    
    # User Management Functions
    
    async def get_all_users(self, page: int = 1, per_page: int = 50) -> Dict[str, Any]:
        """Get all users with pagination"""
        try:
            skip = (page - 1) * per_page
            
            # Get users with pagination
            users_cursor = self.users_collection.find({}).skip(skip).limit(per_page)
            users_data = await users_cursor.to_list(length=per_page)
            
            users = []
            for user_data in users_data:
                try:
                    user = User.from_dict(user_data)
                    
                    # Get today's analysis count
                    today = datetime.utcnow().strftime("%Y-%m-%d")
                    daily_summary = await self.daily_summaries_collection.find_one({
                        "user_id": user.user_id,
                        "date": today
                    })
                    
                    today_count = daily_summary["total_requests"] if daily_summary else 0
                    
                    users.append({
                        "user_id": user.user_id,
                        "username": user.username or "Unknown",
                        "first_name": user.first_name or "",
                        "last_name": user.last_name or "",
                        "status": user.status.value,
                        "tier": user.tier.value,
                        "total_analyses": user.total_analyses,
                        "today_count": today_count,
                        "last_seen": user.last_seen.isoformat() if user.last_seen else None,
                        "created_at": user.created_at.isoformat(),
                        "rate_limit": user.get_rate_limit(),
                        "is_active": user.is_active()
                    })
                except Exception as e:
                    logger.error(f"Error processing user {user_data.get('user_id', 'unknown')}: {e}")
                    continue
            
            # Get total count
            total_users = await self.users_collection.count_documents({})
            
            return {
                "users": users,
                "total": total_users,
                "page": page,
                "per_page": per_page,
                "total_pages": (total_users + per_page - 1) // per_page
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get users: {e}")
            return {"users": [], "total": 0, "page": 1, "per_page": per_page, "total_pages": 0}
    
    async def get_user_details(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific user"""
        try:
            # Get user data
            user_data = await self.users_collection.find_one({"user_id": user_id})
            if not user_data:
                return None
            
            user = User.from_dict(user_data)
            
            # Get analysis logs for last 30 days
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            analysis_logs = await self.analysis_logs_collection.find({
                "user_id": user_id,
                "timestamp": {"$gte": thirty_days_ago}
            }).sort("timestamp", -1).to_list(length=100)
            
            # Get daily summaries for last 7 days
            seven_days_ago = datetime.utcnow() - timedelta(days=7)
            daily_summaries = await self.daily_summaries_collection.find({
                "user_id": user_id,
                "date": {"$gte": seven_days_ago.strftime("%Y-%m-%d")}
            }).sort("date", -1).to_list(length=7)
            
            # Calculate statistics
            total_successful = sum(1 for log in analysis_logs if log.get("success", False))
            total_failed = len(analysis_logs) - total_successful
            avg_response_time = sum(log.get("processing_time", 0) for log in analysis_logs if log.get("processing_time")) / len(analysis_logs) if analysis_logs else 0
            
            # Analysis type breakdown
            analysis_breakdown = {}
            for analysis_type in AnalysisType:
                analysis_breakdown[analysis_type.value] = sum(1 for log in analysis_logs if log.get("analysis_type") == analysis_type.value)
            
            return {
                "user": {
                    "user_id": user.user_id,
                    "username": user.username or "Unknown",
                    "first_name": user.first_name or "",
                    "last_name": user.last_name or "",
                    "status": user.status.value,
                    "tier": user.tier.value,
                    "total_analyses": user.total_analyses,
                    "last_seen": user.last_seen.isoformat() if user.last_seen else None,
                    "created_at": user.created_at.isoformat(),
                    "activated_at": user.activated_at.isoformat() if user.activated_at else None,
                    "rate_limit": user.get_rate_limit(),
                    "is_active": user.is_active()
                },
                "statistics": {
                    "total_requests_30d": len(analysis_logs),
                    "successful_analyses": total_successful,
                    "failed_analyses": total_failed,
                    "success_rate": (total_successful / len(analysis_logs) * 100) if analysis_logs else 0,
                    "avg_response_time": avg_response_time,
                    "analysis_breakdown": analysis_breakdown
                },
                "recent_logs": [
                    {
                        "timestamp": log.get("timestamp", datetime.utcnow()).isoformat(),
                        "analysis_type": log.get("analysis_type", "unknown"),
                        "success": log.get("success", False),
                        "processing_time": log.get("processing_time", 0),
                        "error_message": log.get("error_message")
                    } for log in analysis_logs[:20]
                ],
                "daily_summaries": [
                    {
                        "date": summary.get("date"),
                        "total_requests": summary.get("total_requests", 0),
                        "successful_analyses": summary.get("successful_analyses", 0),
                        "failed_analyses": summary.get("failed_analyses", 0),
                        "avg_response_time": summary.get("avg_response_time", 0)
                    } for summary in daily_summaries
                ]
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get user details for {user_id}: {e}")
            return None
    
    async def toggle_user_status(self, user_id: int, admin_id: str) -> Dict[str, Any]:
        """Toggle user active/inactive status"""
        try:
            user_data = await self.users_collection.find_one({"user_id": user_id})
            if not user_data:
                return {"success": False, "error": "User not found"}
            
            user = User.from_dict(user_data)
            
            # Toggle status
            if user.status == UserStatus.ACTIVE:
                new_status = UserStatus.INACTIVE
                action = "deactivated"
            elif user.status == UserStatus.INACTIVE:
                new_status = UserStatus.ACTIVE
                user.activated_at = datetime.utcnow()
                action = "activated"
            else:  # BLOCKED or SUSPENDED
                return {"success": False, "error": f"Cannot toggle user with status: {user.status.value}"}
            
            user.status = new_status
            user.updated_at = datetime.utcnow()
            
            # Update in database
            await self.users_collection.update_one(
                {"user_id": user_id},
                {"$set": user.to_dict()}
            )
            
            # Log the action
            await self.log_analysis(
                user_id=0,  # System action
                analysis_type=AnalysisType.QUICK,  # Placeholder
                success=True,
                processing_time=0,
                error_message=f"Admin {admin_id} {action} user {user_id}"
            )
            
            logger.info(f"✅ Admin {admin_id} {action} user {user_id}")
            
            return {
                "success": True,
                "new_status": new_status.value,
                "action": action,
                "message": f"User {user_id} has been {action}"
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to toggle user status for {user_id}: {e}")
            return {"success": False, "error": str(e)}
    
    async def update_user_tier(self, user_id: int, new_tier: str, admin_id: str) -> Dict[str, Any]:
        """Update user subscription tier"""
        try:
            # Validate tier
            try:
                tier_enum = UserTier(new_tier)
            except ValueError:
                return {"success": False, "error": f"Invalid tier: {new_tier}"}
            
            user_data = await self.users_collection.find_one({"user_id": user_id})
            if not user_data:
                return {"success": False, "error": "User not found"}
            
            user = User.from_dict(user_data)
            old_tier = user.tier.value
            user.tier = tier_enum
            user.updated_at = datetime.utcnow()
            
            # Update in database
            await self.users_collection.update_one(
                {"user_id": user_id},
                {"$set": user.to_dict()}
            )
            
            # Log the action
            await self.log_analysis(
                user_id=0,  # System action
                analysis_type=AnalysisType.QUICK,  # Placeholder
                success=True,
                processing_time=0,
                error_message=f"Admin {admin_id} changed user {user_id} tier from {old_tier} to {new_tier}"
            )
            
            logger.info(f"✅ Admin {admin_id} updated user {user_id} tier: {old_tier} → {new_tier}")
            
            return {
                "success": True,
                "old_tier": old_tier,
                "new_tier": new_tier,
                "new_rate_limit": user.get_rate_limit(),
                "message": f"User tier updated from {old_tier} to {new_tier}"
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to update user tier for {user_id}: {e}")
            return {"success": False, "error": str(e)}
    
    # Analytics and Statistics Functions
    
    async def get_dashboard_stats(self) -> Dict[str, Any]:
        """Get dashboard statistics"""
        try:
            today = datetime.utcnow().strftime("%Y-%m-%d")
            yesterday = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
            seven_days_ago = datetime.utcnow() - timedelta(days=7)
            
            # User statistics
            total_users = await self.users_collection.count_documents({})
            active_users = await self.users_collection.count_documents({"status": UserStatus.ACTIVE.value})
            inactive_users = await self.users_collection.count_documents({"status": UserStatus.INACTIVE.value})
            blocked_users = await self.users_collection.count_documents({"status": UserStatus.BLOCKED.value})
            
            # User tier breakdown
            basic_users = await self.users_collection.count_documents({"tier": UserTier.BASIC.value})
            premium_users = await self.users_collection.count_documents({"tier": UserTier.PREMIUM.value})
            vip_users = await self.users_collection.count_documents({"tier": UserTier.VIP.value})
            
            # Today's analysis statistics
            today_analyses = await self.analysis_logs_collection.count_documents({
                "timestamp": {"$gte": datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)}
            })
            
            # Yesterday's analyses for comparison
            yesterday_start = datetime.utcnow() - timedelta(days=1)
            yesterday_start = yesterday_start.replace(hour=0, minute=0, second=0, microsecond=0)
            yesterday_end = yesterday_start + timedelta(days=1)
            
            yesterday_analyses = await self.analysis_logs_collection.count_documents({
                "timestamp": {"$gte": yesterday_start, "$lt": yesterday_end}
            })
            
            # Total analyses
            total_analyses = await self.analysis_logs_collection.count_documents({})
            
            # Success rate (last 7 days)
            seven_days_analyses = await self.analysis_logs_collection.find({
                "timestamp": {"$gte": seven_days_ago}
            }).to_list(length=None)
            
            successful_7d = sum(1 for log in seven_days_analyses if log.get("success", False))
            success_rate = (successful_7d / len(seven_days_analyses) * 100) if seven_days_analyses else 0
            
            # Average response time (last 7 days)
            response_times = [log.get("processing_time", 0) for log in seven_days_analyses if log.get("processing_time")]
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            
            # Analysis type breakdown (last 7 days)
            analysis_breakdown = {}
            for analysis_type in AnalysisType:
                count = sum(1 for log in seven_days_analyses if log.get("analysis_type") == analysis_type.value)
                analysis_breakdown[analysis_type.value] = count
            
            # Recent activity (last 20 logs)
            recent_logs = await self.analysis_logs_collection.find({}).sort("timestamp", -1).limit(20).to_list(length=20)
            
            # Format recent activity
            recent_activity = []
            for log in recent_logs:
                recent_activity.append({
                    "user_id": log.get("user_id"),
                    "analysis_type": log.get("analysis_type"),
                    "success": log.get("success", False),
                    "processing_time": log.get("processing_time", 0),
                    "timestamp": log.get("timestamp", datetime.utcnow()).isoformat(),
                    "error_message": log.get("error_message")
                })
            
            # Calculate percentage changes
            analyses_change = ((today_analyses - yesterday_analyses) / yesterday_analyses * 100) if yesterday_analyses > 0 else 0
            
            return {
                "user_stats": {
                    "total_users": total_users,
                    "active_users": active_users,
                    "inactive_users": inactive_users,
                    "blocked_users": blocked_users,
                    "tier_breakdown": {
                        "basic": basic_users,
                        "premium": premium_users,
                        "vip": vip_users
                    }
                },
                "analysis_stats": {
                    "today_analyses": today_analyses,
                    "yesterday_analyses": yesterday_analyses,
                    "total_analyses": total_analyses,
                    "analyses_change_percent": round(analyses_change, 2),
                    "success_rate_7d": round(success_rate, 2),
                    "avg_response_time_7d": round(avg_response_time, 3),
                    "analysis_breakdown_7d": analysis_breakdown
                },
                "recent_activity": recent_activity,
                "last_updated": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get dashboard stats: {e}")
            return {
                "user_stats": {"total_users": 0, "active_users": 0, "inactive_users": 0, "blocked_users": 0},
                "analysis_stats": {"today_analyses": 0, "total_analyses": 0, "success_rate_7d": 0},
                "recent_activity": [],
                "error": str(e)
            }
    
    # Logging Functions
    
    async def log_analysis(self, user_id: int, analysis_type: AnalysisType, success: bool, 
                          processing_time: Optional[float] = None, error_message: Optional[str] = None,
                          gold_price: Optional[float] = None, tokens_used: Optional[int] = None,
                          user_tier: UserTier = UserTier.BASIC) -> bool:
        """Log an analysis request"""
        try:
            log_entry = AnalysisLog(
                user_id=user_id,
                analysis_type=analysis_type,
                success=success,
                processing_time=processing_time,
                error_message=error_message,
                user_tier=user_tier,
                gold_price_at_request=gold_price,
                tokens_used=tokens_used
            )
            
            # Insert log
            await self.analysis_logs_collection.insert_one(log_entry.to_dict())
            
            # Update daily summary
            await self._update_daily_summary(user_id, analysis_type, success, processing_time or 0)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to log analysis: {e}")
            return False
    
    async def _update_daily_summary(self, user_id: int, analysis_type: AnalysisType, 
                                   success: bool, processing_time: float):
        """Update daily summary for user"""
        try:
            today = datetime.utcnow().strftime("%Y-%m-%d")
            
            # Get or create daily summary
            summary_data = await self.daily_summaries_collection.find_one({
                "user_id": user_id,
                "date": today
            })
            
            if summary_data:
                summary = UserDailySummary(**summary_data)
            else:
                summary = UserDailySummary(user_id=user_id, date=today)
            
            # Update counters
            summary.total_requests += 1
            if success:
                summary.successful_analyses += 1
            else:
                summary.failed_analyses += 1
            
            # Update analysis type breakdown
            if analysis_type == AnalysisType.QUICK:
                summary.quick_analyses += 1
            elif analysis_type == AnalysisType.DETAILED:
                summary.detailed_analyses += 1
            elif analysis_type == AnalysisType.CHART:
                summary.chart_analyses += 1
            elif analysis_type == AnalysisType.NEWS:
                summary.news_analyses += 1
            elif analysis_type == AnalysisType.FORECAST:
                summary.forecast_analyses += 1
            
            # Update average response time
            if summary.total_requests > 1:
                # Running average
                total_time = summary.avg_response_time * (summary.total_requests - 1) + processing_time
                summary.avg_response_time = total_time / summary.total_requests
            else:
                summary.avg_response_time = processing_time
            
            # Upsert to database
            await self.daily_summaries_collection.replace_one(
                {"user_id": user_id, "date": today},
                summary.to_dict(),
                upsert=True
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to update daily summary: {e}")

# Global admin manager instance
admin_manager: Optional[AdminManager] = None

async def get_admin_manager() -> AdminManager:
    """Get global admin manager instance"""
    global admin_manager
    if admin_manager is None:
        db_manager = await get_database()
        admin_manager = AdminManager(db_manager)
        await admin_manager.initialize()
    return admin_manager

async def close_admin_manager():
    """Close global admin manager"""
    global admin_manager
    admin_manager = None