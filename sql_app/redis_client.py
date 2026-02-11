"""
Redis Client Wrapper for FastAPI
Provides async Redis operations with error handling and connection management
"""

import aioredis
from typing import Optional, Any
import json
from datetime import timedelta


class RedisClient:
    """
    Async Redis client wrapper for FastAPI
    Handles connection management and common operations
    """
    
    def __init__(self, url: str = "redis://localhost:6379", db: int = 0):
        """
        Initialize Redis client
        
        Args:
            url: Redis connection URL
            db: Database number (0-15)
        """
        self.url = f"{url}/{db}" if "/" not in url else url
        self.client: Optional[aioredis.Redis] = None
    
    async def connect(self):
        """Establish Redis connection"""
        try:
            self.client = await aioredis.from_url(
                self.url,
                encoding="utf8",
                decode_responses=True
            )
            # Test connection
            await self.client.ping()
            print("✅ Connected to Redis")
        except Exception as e:
            print(f"❌ Failed to connect to Redis: {e}")
            raise
    
    async def disconnect(self):
        """Close Redis connection"""
        if self.client:
            await self.client.close()
            print("✅ Disconnected from Redis")
    
    async def get(self, key: str) -> Optional[str]:
        """Get value by key"""
        if not self.client:
            return None
        try:
            return await self.client.get(key)
        except Exception as e:
            print(f"❌ Redis GET error: {e}")
            return None
    
    async def set(self, key: str, value: Any, ex: Optional[int] = None):
        """
        Set key-value pair with optional expiration
        
        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ex: Expiration time in seconds
        """
        if not self.client:
            return
        
        try:
            # Serialize to JSON if not string
            if not isinstance(value, str):
                value = json.dumps(value, default=str)
            
            await self.client.set(key, value, ex=ex)
        except Exception as e:
            print(f"❌ Redis SET error: {e}")
    
    async def setex(self, key: str, seconds: int, value: Any):
        """Set key with expiration time"""
        await self.set(key, value, ex=seconds)
    
    async def delete(self, key: str) -> int:
        """Delete key, return number of keys deleted"""
        if not self.client:
            return 0
        try:
            return await self.client.delete(key)
        except Exception as e:
            print(f"❌ Redis DELETE error: {e}")
            return 0
    
    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern using SCAN"""
        if not self.client:
            return 0
        
        try:
            deleted = 0
            cursor = 0
            
            while True:
                cursor, keys = await self.client.scan(cursor, match=pattern)
                
                if keys:
                    deleted += await self.client.delete(*keys)
                
                if cursor == 0:
                    break
            
            return deleted
        except Exception as e:
            print(f"❌ Redis SCAN/DELETE error: {e}")
            return 0
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        if not self.client:
            return False
        try:
            return await self.client.exists(key) > 0
        except Exception as e:
            print(f"❌ Redis EXISTS error: {e}")
            return False
    
    async def ttl(self, key: str) -> int:
        """
        Get time to live in seconds
        Returns: -1 if no expiration, -2 if doesn't exist
        """
        if not self.client:
            return -2
        try:
            return await self.client.ttl(key)
        except Exception as e:
            print(f"❌ Redis TTL error: {e}")
            return -2
    
    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration on existing key"""
        if not self.client:
            return False
        try:
            return await self.client.expire(key, seconds)
        except Exception as e:
            print(f"❌ Redis EXPIRE error: {e}")
            return False
    
    async def incr(self, key: str) -> int:
        """Increment counter"""
        if not self.client:
            return 0
        try:
            return await self.client.incr(key)
        except Exception as e:
            print(f"❌ Redis INCR error: {e}")
            return 0
    
    async def incrby(self, key: str, amount: int) -> int:
        """Increment by amount"""
        if not self.client:
            return 0
        try:
            return await self.client.incrby(key, amount)
        except Exception as e:
            print(f"❌ Redis INCRBY error: {e}")
            return 0
    
    async def hset(self, key: str, field: str, value: Any):
        """Set hash field"""
        if not self.client:
            return
        
        try:
            if not isinstance(value, str):
                value = json.dumps(value, default=str)
            
            await self.client.hset(key, field, value)
        except Exception as e:
            print(f"❌ Redis HSET error: {e}")
    
    async def hget(self, key: str, field: str) -> Optional[str]:
        """Get hash field"""
        if not self.client:
            return None
        try:
            return await self.client.hget(key, field)
        except Exception as e:
            print(f"❌ Redis HGET error: {e}")
            return None
    
    async def hgetall(self, key: str) -> dict:
        """Get all hash fields"""
        if not self.client:
            return {}
        try:
            return await self.client.hgetall(key) or {}
        except Exception as e:
            print(f"❌ Redis HGETALL error: {e}")
            return {}
    
    async def hdel(self, key: str, field: str) -> int:
        """Delete hash field"""
        if not self.client:
            return 0
        try:
            return await self.client.hdel(key, field)
        except Exception as e:
            print(f"❌ Redis HDEL error: {e}")
            return 0
    
    async def lpush(self, key: str, *values: Any):
        """Push values to list"""
        if not self.client:
            return
        
        try:
            values = [
                json.dumps(v, default=str) if not isinstance(v, str) else v
                for v in values
            ]
            await self.client.lpush(key, *values)
        except Exception as e:
            print(f"❌ Redis LPUSH error: {e}")
    
    async def lrange(self, key: str, start: int = 0, end: int = -1) -> list:
        """Get list range"""
        if not self.client:
            return []
        try:
            return await self.client.lrange(key, start, end) or []
        except Exception as e:
            print(f"❌ Redis LRANGE error: {e}")
            return []
    
    async def lpop(self, key: str, count: int = 1) -> Optional[Any]:
        """Pop from list"""
        if not self.client:
            return None
        try:
            return await self.client.lpop(key, count)
        except Exception as e:
            print(f"❌ Redis LPOP error: {e}")
            return None
    
    async def flushdb(self):
        """Clear all keys in current database (use with caution!)"""
        if self.client:
            try:
                await self.client.flushdb()
                print("⚠️  Redis database flushed")
            except Exception as e:
                print(f"❌ Redis FLUSHDB error: {e}")
    
    async def info(self, section: str = "all") -> dict:
        """Get Redis server info"""
        if not self.client:
            return {}
        try:
            return await self.client.info(section)
        except Exception as e:
            print(f"❌ Redis INFO error: {e}")
            return {}
    
    async def ping(self) -> bool:
        """Check if Redis is responsive"""
        try:
            return await self.client.ping() if self.client else False
        except Exception:
            return False
