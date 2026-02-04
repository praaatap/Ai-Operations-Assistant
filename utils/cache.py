"""
Redis Cache Utility - Async caching layer for API responses
"""
import os
import json
import hashlib
import logging
from typing import Any, Optional
from functools import wraps

logger = logging.getLogger(__name__)

# Try to import redis, fall back to in-memory cache if unavailable
try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not available, using in-memory cache")


class CacheClient:
    """Async cache client with Redis support and in-memory fallback"""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self._memory_cache: dict = {}
        self._cache_stats = {"hits": 0, "misses": 0}
    
    async def connect(self) -> bool:
        """Connect to Redis server"""
        if not REDIS_AVAILABLE:
            logger.info("Redis not available, using in-memory cache")
            return False
        
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        try:
            self.redis_client = redis.from_url(
                redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            # Test connection
            await self.redis_client.ping()
            logger.info(f"Connected to Redis at {redis_url}")
            return True
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}. Using in-memory cache.")
            self.redis_client = None
            return False
    
    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Redis connection closed")
    
    @staticmethod
    def _generate_key(prefix: str, params: dict) -> str:
        """Generate a cache key from prefix and parameters"""
        param_str = json.dumps(params, sort_keys=True)
        param_hash = hashlib.md5(param_str.encode()).hexdigest()[:12]
        return f"{prefix}:{param_hash}"
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            if self.redis_client:
                value = await self.redis_client.get(key)
                if value:
                    self._cache_stats["hits"] += 1
                    logger.debug(f"Cache HIT: {key}")
                    return json.loads(value)
            else:
                if key in self._memory_cache:
                    self._cache_stats["hits"] += 1
                    logger.debug(f"Memory cache HIT: {key}")
                    return self._memory_cache[key]
        except Exception as e:
            logger.error(f"Cache get error: {e}")
        
        self._cache_stats["misses"] += 1
        logger.debug(f"Cache MISS: {key}")
        return None
    
    async def set(self, key: str, value: Any, ttl_seconds: int = 300) -> bool:
        """Set value in cache with TTL"""
        try:
            if self.redis_client:
                await self.redis_client.setex(key, ttl_seconds, json.dumps(value))
                logger.debug(f"Cache SET: {key} (TTL: {ttl_seconds}s)")
                return True
            else:
                self._memory_cache[key] = value
                logger.debug(f"Memory cache SET: {key}")
                return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete a key from cache"""
        try:
            if self.redis_client:
                await self.redis_client.delete(key)
            else:
                self._memory_cache.pop(key, None)
            return True
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False
    
    async def clear(self) -> bool:
        """Clear all cache"""
        try:
            if self.redis_client:
                await self.redis_client.flushdb()
            else:
                self._memory_cache.clear()
            self._cache_stats = {"hits": 0, "misses": 0}
            return True
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return False
    
    def get_stats(self) -> dict:
        """Get cache statistics"""
        total = self._cache_stats["hits"] + self._cache_stats["misses"]
        hit_rate = (self._cache_stats["hits"] / total * 100) if total > 0 else 0
        return {
            "hits": self._cache_stats["hits"],
            "misses": self._cache_stats["misses"],
            "hit_rate": f"{hit_rate:.1f}%",
            "backend": "redis" if self.redis_client else "memory"
        }


# Global cache instance
cache_client = CacheClient()


def cached(prefix: str, ttl_seconds: int = 300):
    """Decorator to cache async function results"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key from function parameters
            cache_params = {
                "args": str(args[1:]) if args else "",  # Skip 'self'
                "kwargs": kwargs
            }
            key = CacheClient._generate_key(prefix, cache_params)
            
            # Try to get from cache
            cached_value = await cache_client.get(key)
            if cached_value is not None:
                return cached_value
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            
            # Only cache successful results
            if isinstance(result, dict) and not result.get("error"):
                await cache_client.set(key, result, ttl_seconds)
            
            return result
        return wrapper
    return decorator
