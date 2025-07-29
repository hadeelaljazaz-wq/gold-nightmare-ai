"""
Gold Nightmare Bot Cache Manager
مدير التخزين المؤقت والذاكرة التخزينية
"""
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Union
from dataclasses import asdict
import hashlib

from .config import get_config
from .models import GoldPrice, Analysis, CacheKeys

logger = logging.getLogger(__name__)

class InMemoryCache:
    """In-memory cache implementation (fallback when Redis is not available)"""
    
    def __init__(self):
        self._data: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()
    
    async def get(self, key: str) -> Optional[str]:
        """Get value from cache"""
        async with self._lock:
            if key in self._data:
                item = self._data[key]
                if datetime.utcnow() < item["expires"]:
                    return item["value"]
                else:
                    # Expired, remove it
                    del self._data[key]
            return None
    
    async def set(self, key: str, value: str, expire_seconds: int):
        """Set value in cache with expiration"""
        async with self._lock:
            self._data[key] = {
                "value": value,
                "expires": datetime.utcnow() + timedelta(seconds=expire_seconds)
            }
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        async with self._lock:
            if key in self._data:
                del self._data[key]
                return True
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists and is not expired"""
        return await self.get(key) is not None
    
    async def cleanup_expired(self):
        """Remove expired entries"""
        async with self._lock:
            now = datetime.utcnow()
            expired_keys = [
                key for key, item in self._data.items()
                if now >= item["expires"]
            ]
            for key in expired_keys:
                del self._data[key]
            
            if expired_keys:
                logger.info(f"🧹 Cleaned up {len(expired_keys)} expired cache entries")

class CacheManager:
    """Cache manager with automatic Redis fallback to in-memory"""
    
    def __init__(self):
        self.config = get_config()
        self.redis_client = None
        self.memory_cache = InMemoryCache()
        self.use_redis = False
    
    async def initialize(self):
        """Initialize cache (try Redis first, fallback to in-memory)"""
        try:
            # Try to import and use Redis
            import redis.asyncio as redis
            
            self.redis_client = redis.Redis(
                host='localhost',
                port=6379,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            
            # Test Redis connection
            await self.redis_client.ping()
            self.use_redis = True
            logger.info("✅ Redis cache initialized")
            
        except ImportError:
            logger.warning("⚠️ Redis not available, using in-memory cache")
        except Exception as e:
            logger.warning(f"⚠️ Redis connection failed ({e}), using in-memory cache")
        
        # Start cleanup task for in-memory cache
        if not self.use_redis:
            asyncio.create_task(self._cleanup_task())
    
    async def close(self):
        """Close cache connections"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("🔚 Cache connections closed")
    
    async def _cleanup_task(self):
        """Background task to cleanup expired in-memory cache entries"""
        while True:
            try:
                await asyncio.sleep(300)  # Cleanup every 5 minutes
                await self.memory_cache.cleanup_expired()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Cache cleanup error: {e}")
    
    async def get(self, key: str) -> Optional[str]:
        """Get value from cache"""
        try:
            if self.use_redis and self.redis_client:
                return await self.redis_client.get(key)
            else:
                return await self.memory_cache.get(key)
        except Exception as e:
            logger.error(f"❌ Cache get error: {e}")
            return None
    
    async def set(self, key: str, value: str, expire_seconds: int = 3600):
        """Set value in cache with expiration"""
        try:
            if self.use_redis and self.redis_client:
                await self.redis_client.setex(key, expire_seconds, value)
            else:
                await self.memory_cache.set(key, value, expire_seconds)
        except Exception as e:
            logger.error(f"❌ Cache set error: {e}")
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        try:
            if self.use_redis and self.redis_client:
                result = await self.redis_client.delete(key)
                return result > 0
            else:
                return await self.memory_cache.delete(key)
        except Exception as e:
            logger.error(f"❌ Cache delete error: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        try:
            if self.use_redis and self.redis_client:
                return await self.redis_client.exists(key) > 0
            else:
                return await self.memory_cache.exists(key)
        except Exception as e:
            logger.error(f"❌ Cache exists error: {e}")
            return False
    
    # Specialized cache methods for gold data
    async def cache_gold_price(self, price: GoldPrice) -> bool:
        """Cache gold price data"""
        try:
            price_data = json.dumps(asdict(price), default=str)
            await self.set(
                CacheKeys.GOLD_PRICE,
                price_data,
                self.config.price_cache_ttl
            )
            logger.info(f"📦 Cached gold price: ${price.price_usd:.2f}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to cache gold price: {e}")
            return False
    
    async def get_gold_price(self) -> Optional[GoldPrice]:
        """Get cached gold price"""
        try:
            cached_data = await self.get(CacheKeys.GOLD_PRICE)
            if cached_data:
                price_dict = json.loads(cached_data)
                
                # Convert string timestamps back to datetime
                for key in ['timestamp', 'created_at']:
                    if key in price_dict and isinstance(price_dict[key], str):
                        price_dict[key] = datetime.fromisoformat(price_dict[key].replace('Z', '+00:00'))
                
                return GoldPrice(**price_dict)
            return None
            
        except Exception as e:
            logger.error(f"❌ Failed to get cached gold price: {e}")
            return None
    
    async def cache_analysis(self, user_id: int, analysis: Analysis, content_hash: str) -> bool:
        """Cache analysis result"""
        try:
            cache_key = CacheKeys.analysis_key(user_id, analysis.analysis_type, content_hash)
            analysis_data = json.dumps(asdict(analysis), default=str)
            
            await self.set(
                cache_key,
                analysis_data,
                self.config.analysis_cache_ttl
            )
            
            logger.info(f"📦 Cached analysis for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to cache analysis: {e}")
            return False
    
    async def get_cached_analysis(self, user_id: int, analysis_type: str, content_hash: str) -> Optional[Analysis]:
        """Get cached analysis"""
        try:
            from .models import AnalysisType
            analysis_type_enum = AnalysisType(analysis_type)
            cache_key = CacheKeys.analysis_key(user_id, analysis_type_enum, content_hash)
            
            cached_data = await self.get(cache_key)
            if cached_data:
                analysis_dict = json.loads(cached_data)
                
                # Convert timestamps
                for key in ['created_at']:
                    if key in analysis_dict and isinstance(analysis_dict[key], str):
                        analysis_dict[key] = datetime.fromisoformat(analysis_dict[key].replace('Z', '+00:00'))
                
                return Analysis.from_dict(analysis_dict)
            return None
            
        except Exception as e:
            logger.error(f"❌ Failed to get cached analysis: {e}")
            return None
    
    async def cache_user_session(self, user_id: int, session_data: Dict[str, Any]) -> bool:
        """Cache user session data"""
        try:
            cache_key = CacheKeys.USER_SESSION.format(user_id=user_id)
            session_json = json.dumps(session_data, default=str)
            
            await self.set(
                cache_key,
                session_json,
                self.config.session_timeout
            )
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to cache user session: {e}")
            return False
    
    async def get_user_session(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get cached user session"""
        try:
            cache_key = CacheKeys.USER_SESSION.format(user_id=user_id)
            cached_data = await self.get(cache_key)
            
            if cached_data:
                return json.loads(cached_data)
            return None
            
        except Exception as e:
            logger.error(f"❌ Failed to get user session: {e}")
            return None
    
    def generate_content_hash(self, content: str) -> str:
        """Generate hash for content to use as cache key"""
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    async def clear_user_cache(self, user_id: int):
        """Clear all cached data for a user"""
        try:
            # This would require pattern matching in Redis
            # For now, we'll just clear the session
            session_key = CacheKeys.USER_SESSION.format(user_id=user_id)
            await self.delete(session_key)
            
            logger.info(f"🧹 Cleared cache for user {user_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to clear user cache: {e}")
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            if self.use_redis and self.redis_client:
                info = await self.redis_client.info()
                return {
                    "type": "redis",
                    "connected_clients": info.get("connected_clients", 0),
                    "used_memory": info.get("used_memory_human", "unknown"),
                    "keyspace_hits": info.get("keyspace_hits", 0),
                    "keyspace_misses": info.get("keyspace_misses", 0)
                }
            else:
                return {
                    "type": "memory",
                    "cached_items": len(self.memory_cache._data),
                    "status": "active"
                }
                
        except Exception as e:
            logger.error(f"❌ Failed to get cache stats: {e}")
            return {"type": "unknown", "error": str(e)}

# Global cache manager instance
cache_manager: Optional[CacheManager] = None

async def get_cache_manager() -> CacheManager:
    """Get global cache manager instance"""
    global cache_manager
    if cache_manager is None:
        cache_manager = CacheManager()
        await cache_manager.initialize()
    return cache_manager

async def close_cache_manager():
    """Close global cache manager"""
    global cache_manager
    if cache_manager:
        await cache_manager.close()
        cache_manager = None