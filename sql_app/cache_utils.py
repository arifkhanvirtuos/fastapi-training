"""
Caching utilities and decorators for FastAPI
Provides cache metrics, decorators, and tag-based invalidation
"""

import json
import functools
from typing import Callable, Optional, Any
from datetime import datetime
from redis_client import RedisClient


class CacheMetrics:
    """Track cache hit/miss statistics"""
    
    def __init__(self, redis: RedisClient):
        self.redis = redis
    
    async def record_hit(self, key: str):
        """Record a cache hit"""
        await self.redis.incr("cache:hits")
    
    async def record_miss(self, key: str):
        """Record a cache miss"""
        await self.redis.incr("cache:misses")
    
    async def get_stats(self) -> dict:
        """Get cache statistics"""
        hits = int(await self.redis.get("cache:hits") or 0)
        misses = int(await self.redis.get("cache:misses") or 0)
        total = hits + misses
        
        hit_ratio = (hits / total * 100) if total > 0 else 0
        
        return {
            "hits": hits,
            "misses": misses,
            "total_requests": total,
            "hit_ratio_percent": round(hit_ratio, 2)
        }
    
    async def reset(self):
        """Reset metrics"""
        await self.redis.delete("cache:hits")
        await self.redis.delete("cache:misses")


def cache_key_builder(*args, **kwargs) -> str:
    """Build cache key from function arguments"""
    key_parts = []
    
    for arg in args:
        if hasattr(arg, 'id'):
            key_parts.append(str(arg.id))
        elif isinstance(arg, str):
            key_parts.append(arg)
        else:
            key_parts.append(str(arg))
    
    for k, v in kwargs.items():
        key_parts.append(f"{k}={v}")
    
    return ":".join(key_parts)


def cache_result(
    ttl: int = 3600,
    namespace: str = "",
    key_builder: Optional[Callable] = None,
):
    """
    Decorator to cache async function results
    
    Args:
        ttl: Time-to-live in seconds
        namespace: Prefix for cache key
        key_builder: Custom function to build cache key
    
    Example:
        @cache_result(ttl=1800, namespace="users")
        async def get_user(user_id: str):
            return await db.get_user(user_id)
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, redis: RedisClient = None, **kwargs):
            if not redis:
                # Redis not available, just call function
                return await func(*args, **kwargs)
            
            # Build cache key
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                cache_key = cache_key_builder(*args, **kwargs)
            
            if namespace:
                cache_key = f"{namespace}:{cache_key}"
            
            # Try cache first
            cached = await redis.get(cache_key)
            if cached:
                await CacheMetrics(redis).record_hit(cache_key)
                try:
                    return json.loads(cached)
                except:
                    return cached
            
            # Cache miss - execute function
            await CacheMetrics(redis).record_miss(cache_key)
            result = await func(*args, **kwargs)
            
            # Store in cache
            if result is not None:
                try:
                    await redis.set(cache_key, result, ex=ttl)
                except Exception as e:
                    print(f"Cache set failed: {e}")
            
            return result
        
        return wrapper
    return decorator


async def cache_evict(redis: RedisClient, pattern: str):
    """Evict cache entries matching pattern"""
    if redis:
        deleted = await redis.delete_pattern(pattern)
        return deleted
    return 0


class TaggedCache:
    """Cache with tag-based invalidation"""
    
    def __init__(self, redis: RedisClient):
        self.redis = redis
    
    async def set_with_tags(
        self,
        key: str,
        value: Any,
        tags: list,
        ttl: int = 3600
    ):
        """Set value with associated tags for grouped invalidation"""
        # Store the value
        await self.redis.set(key, value, ex=ttl)
        
        # Track key with each tag
        for tag in tags:
            tag_key = f"tag:{tag}"
            await self.redis.lpush(tag_key, key)
            await self.redis.expire(tag_key, ttl)
    
    async def invalidate_tag(self, tag: str) -> int:
        """Delete all keys with this tag"""
        tag_key = f"tag:{tag}"
        keys = await self.redis.lrange(tag_key, 0, -1)
        
        deleted = 0
        for key in keys:
            if await self.redis.delete(key):
                deleted += 1
        
        await self.redis.delete(tag_key)
        return deleted
    
    async def invalidate_tags(self, tags: list) -> int:
        """Delete all keys with any of these tags"""
        total_deleted = 0
        for tag in tags:
            total_deleted += await self.invalidate_tag(tag)
        return total_deleted


class CacheWarmer:
    """Utility for warming up cache with popular data"""
    
    def __init__(self, redis: RedisClient):
        self.redis = redis
    
    async def warm_keys(self, keys_data: dict, ttl: int = 3600):
        """
        Warm cache with provided data
        
        Args:
            keys_data: Dictionary of {cache_key: value}
            ttl: Time-to-live for all keys
        """
        count = 0
        for key, value in keys_data.items():
            await self.redis.set(key, value, ex=ttl)
            count += 1
        
        return count
    
    async def get_cache_size(self) -> dict:
        """Get information about current cache"""
        info = await self.redis.info("memory")
        
        return {
            "used_memory_mb": info.get("used_memory", 0) / 1024 / 1024,
            "max_memory_mb": info.get("maxmemory", 0) / 1024 / 1024,
            "memory_usage_percent": (
                (info.get("used_memory", 0) / info.get("maxmemory", 1) * 100)
                if info.get("maxmemory") else 0
            )
        }
