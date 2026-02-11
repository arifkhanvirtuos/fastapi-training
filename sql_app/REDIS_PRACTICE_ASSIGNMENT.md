# Redis Caching Practice Assignment
## FastAPI + Redis Integration Challenge

**Duration:** 2-3 hours  
**Level:** Intermediate  
**Objective:** Implement Redis caching to optimize expensive database queries

---

## 📚 Background

You've learned about Redis caching patterns and strategies. Now it's time to apply them to a real FastAPI application. Your task is to add Redis caching to reduce database load and improve response times.

---

## 🎯 Phase 1: Setup (30 minutes)

### Task 1.1: Install Redis & Dependencies
```bash
# macOS
brew install redis
brew services start redis

# Linux
sudo apt-get install redis-server
sudo systemctl start redis-server

# Verify
redis-cli ping
# Expected output: PONG
```

### Task 1.2: Update requirements.txt
Add to `requirements.txt`:
```
redis==5.0.0
aioredis==2.0.1
```

Then install:
```bash
pip install -r requirements.txt
```

### Task 1.3: Test Redis Connection
```bash
redis-cli

# Try some commands
SET test_key "Hello Redis"
GET test_key
DEL test_key
EXIT
```

---

## 🎯 Phase 2: Create Redis Client (30 minutes)

### Task 2.1: Create `redis_client.py`

Create a reusable Redis client wrapper:

**File: `sql_app/redis_client.py`**

```python
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
            self.client = await aioredis.from_url(self.url, encoding="utf8", decode_responses=True)
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
        return await self.client.get(key)
    
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
        
        # Serialize to JSON if not string
        if not isinstance(value, str):
            value = json.dumps(value, default=str)
        
        await self.client.set(key, value, ex=ex)
    
    async def setex(self, key: str, seconds: int, value: Any):
        """Set key with expiration time"""
        await self.set(key, value, ex=seconds)
    
    async def delete(self, key: str) -> int:
        """Delete key, return number of keys deleted"""
        if not self.client:
            return 0
        return await self.client.delete(key)
    
    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern using SCAN"""
        if not self.client:
            return 0
        
        deleted = 0
        cursor = 0
        
        while True:
            cursor, keys = await self.client.scan(cursor, match=pattern)
            
            if keys:
                deleted += await self.client.delete(*keys)
            
            if cursor == 0:
                break
        
        return deleted
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        if not self.client:
            return False
        return await self.client.exists(key) > 0
    
    async def ttl(self, key: str) -> int:
        """
        Get time to live in seconds
        Returns: -1 if no expiration, -2 if doesn't exist
        """
        if not self.client:
            return -2
        return await self.client.ttl(key)
    
    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration on existing key"""
        if not self.client:
            return False
        return await self.client.expire(key, seconds)
    
    async def incr(self, key: str) -> int:
        """Increment counter"""
        if not self.client:
            return 0
        return await self.client.incr(key)
    
    async def incrby(self, key: str, amount: int) -> int:
        """Increment by amount"""
        if not self.client:
            return 0
        return await self.client.incrby(key, amount)
    
    async def hset(self, key: str, field: str, value: Any):
        """Set hash field"""
        if not self.client:
            return
        
        if not isinstance(value, str):
            value = json.dumps(value, default=str)
        
        await self.client.hset(key, field, value)
    
    async def hget(self, key: str, field: str) -> Optional[str]:
        """Get hash field"""
        if not self.client:
            return None
        return await self.client.hget(key, field)
    
    async def hgetall(self, key: str) -> dict:
        """Get all hash fields"""
        if not self.client:
            return {}
        return await self.client.hgetall(key) or {}
    
    async def hdel(self, key: str, field: str) -> int:
        """Delete hash field"""
        if not self.client:
            return 0
        return await self.client.hdel(key, field)
    
    async def lpush(self, key: str, *values: Any):
        """Push values to list"""
        if not self.client:
            return
        
        values = [json.dumps(v, default=str) if not isinstance(v, str) else v for v in values]
        await self.client.lpush(key, *values)
    
    async def lrange(self, key: str, start: int = 0, end: int = -1) -> list:
        """Get list range"""
        if not self.client:
            return []
        return await self.client.lrange(key, start, end) or []
    
    async def lpop(self, key: str, count: int = 1) -> Optional[Any]:
        """Pop from list"""
        if not self.client:
            return None
        return await self.client.lpop(key, count)
    
    async def flushdb(self):
        """Clear all keys in current database (use with caution!)"""
        if self.client:
            await self.client.flushdb()
    
    async def info(self, section: str = "all") -> dict:
        """Get Redis server info"""
        if not self.client:
            return {}
        return await self.client.info(section)
    
    async def ping(self) -> bool:
        """Check if Redis is responsive"""
        try:
            return await self.client.ping() if self.client else False
        except:
            return False
```

### Task 2.2: Test the client

Create a quick test:

```python
# test_redis_client.py
import asyncio
from redis_client import RedisClient

async def test_redis():
    client = RedisClient()
    
    try:
        await client.connect()
        
        # Test basic operations
        await client.set("test_key", {"message": "Hello Redis"}, ex=3600)
        value = await client.get("test_key")
        print(f"Stored value: {value}")
        
        # Clean up
        await client.delete("test_key")
        print("✅ Redis client working!")
        
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(test_redis())
```

Run it:
```bash
python test_redis_client.py
```

---

## 🎯 Phase 3: Create Caching Utilities (30 minutes)

### Task 3.1: Create `cache_utils.py`

**File: `sql_app/cache_utils.py`**

Implement caching decorators and utilities:

```python
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
        tags: list[str],
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
    
    async def invalidate_tags(self, tags: list[str]) -> int:
        """Delete all keys with any of these tags"""
        total_deleted = 0
        for tag in tags:
            total_deleted += await self.invalidate_tag(tag)
        return total_deleted
```

---

## 🎯 Phase 4: Integrate with FastAPI (45 minutes)

### Task 4.1: Update `main.py`

Add Redis client initialization and integrate caching into endpoints.

Add to top of `main.py`:

```python
from redis_client import RedisClient
from cache_utils import CacheMetrics, cache_result, cache_evict
```

Add to lifespan (replace existing):

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting up...")
    
    # Initialize Redis
    app.state.redis = RedisClient()
    try:
        await app.state.redis.connect()
    except Exception as e:
        print(f"⚠️  Redis connection failed: {e}")
        app.state.redis = None
    
    yield
    
    # Shutdown
    print("🛑 Shutting down...")
    if app.state.redis:
        await app.state.redis.disconnect()
```

Add dependency:

```python
async def get_redis() -> Optional[RedisClient]:
    redis = getattr(app.state, 'redis', None)
    return redis
```

### Task 4.2: Cache User Queries

Replace or add these endpoints with caching:

```python
@app.get("/users/{user_id}", response_model=UserResponse, tags=["Users - Cached"])
async def get_user_cached(
    user_id: str,
    db: Session = Depends(get_db),
    redis: Optional[RedisClient] = Depends(get_redis)
) -> UserResponse:
    """
    Get single user with Redis caching (Cache-Aside pattern)
    
    - First request: Database query (~100ms)
    - Subsequent requests: Redis (~1ms)
    - Cache duration: 1 hour
    """
    cache_key = f"user:{user_id}"
    
    # Try cache first
    if redis:
        cached = await redis.get(cache_key)
        if cached:
            await CacheMetrics(redis).record_hit(cache_key)
            return UserResponse(**json.loads(cached))
    
    # Cache miss or no Redis
    if redis:
        await CacheMetrics(redis).record_miss(cache_key)
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Cache the result
    if redis:
        await redis.set(
            cache_key,
            user.to_dict(),
            ex=3600  # 1 hour
        )
    
    return user


@app.get("/users", response_model=list[UserResponse], tags=["Users - Cached"])
async def list_users_cached(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    redis: Optional[RedisClient] = Depends(get_redis)
) -> list[UserResponse]:
    """
    List users with Redis caching
    
    - Cache key: users:list:{skip}:{limit}
    - Duration: 30 minutes
    """
    cache_key = f"users:list:{skip}:{limit}"
    
    # Try cache
    if redis:
        cached = await redis.get(cache_key)
        if cached:
            await CacheMetrics(redis).record_hit(cache_key)
            return [UserResponse(**u) for u in json.loads(cached)]
    
    # Database query
    if redis:
        await CacheMetrics(redis).record_miss(cache_key)
    
    users = db.query(User).offset(skip).limit(limit).all()
    
    # Cache results
    if redis and users:
        await redis.set(
            cache_key,
            [u.to_dict() for u in users],
            ex=1800  # 30 minutes
        )
    
    return users


@app.put("/users/{user_id}", response_model=UserResponse, tags=["Users - Cached"])
async def update_user_invalidate(
    user_id: str,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    redis: Optional[RedisClient] = Depends(get_redis),
    current_user: User = Depends(get_current_active_user)
) -> UserResponse:
    """
    Update user and invalidate cache (Write-Through pattern)
    
    - Updates database
    - Invalidates all related cache entries
    - Returns fresh data
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update database
    for field, value in user_update.dict(exclude_unset=True).items():
        setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    
    # Invalidate cache
    if redis:
        await redis.delete(f"user:{user_id}")
        await redis.delete_pattern("users:list:*")
    
    return user


@app.delete("/users/{user_id}", tags=["Users - Cached"])
async def delete_user_invalidate(
    user_id: str,
    db: Session = Depends(get_db),
    redis: Optional[RedisClient] = Depends(get_redis),
    current_user: User = Depends(require_admin)
):
    """Delete user and invalidate cache"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Delete from database
    db.delete(user)
    db.commit()
    
    # Invalidate cache
    if redis:
        await redis.delete(f"user:{user_id}")
        await redis.delete_pattern("users:list:*")
    
    return {"message": "User deleted"}
```

### Task 4.3: Add Admin Cache Management Endpoints

```python
@app.post("/admin/cache/warm", tags=["Admin - Cache"])
async def warm_cache(
    db: Session = Depends(get_db),
    redis: Optional[RedisClient] = Depends(get_redis),
    current_user: User = Depends(require_admin)
):
    """
    Warm cache with all active users
    Pre-populate Redis with frequently accessed data
    """
    if not redis:
        raise HTTPException(
            status_code=503,
            detail="Redis not available"
        )
    
    users = db.query(User).filter(User.is_active == True).all()
    
    for user in users:
        await redis.set(
            f"user:{user.id}",
            user.to_dict(),
            ex=3600
        )
    
    return {
        "message": f"Cached {len(users)} users",
        "count": len(users)
    }


@app.get("/admin/cache/stats", tags=["Admin - Cache"])
async def get_cache_stats(
    redis: Optional[RedisClient] = Depends(get_redis),
    current_user: User = Depends(require_admin)
):
    """Get cache performance statistics"""
    if not redis:
        raise HTTPException(
            status_code=503,
            detail="Redis not available"
        )
    
    metrics = CacheMetrics(redis)
    stats = await metrics.get_stats()
    
    # Also get Redis info
    info = await redis.info("memory")
    
    return {
        **stats,
        "memory_usage_mb": info.get("used_memory", 0) / 1024 / 1024,
        "max_memory_mb": info.get("maxmemory", 0) / 1024 / 1024 if info.get("maxmemory") else "unlimited"
    }


@app.post("/admin/cache/clear", tags=["Admin - Cache"])
async def clear_cache(
    pattern: str = "*",
    redis: Optional[RedisClient] = Depends(get_redis),
    current_user: User = Depends(require_admin)
):
    """Clear cache entries matching pattern"""
    if not redis:
        raise HTTPException(
            status_code=503,
            detail="Redis not available"
        )
    
    deleted = await redis.delete_pattern(pattern)
    
    return {"message": f"Deleted {deleted} cache entries", "deleted_count": deleted}


@app.post("/admin/cache/metrics/reset", tags=["Admin - Cache"])
async def reset_metrics(
    redis: Optional[RedisClient] = Depends(get_redis),
    current_user: User = Depends(require_admin)
):
    """Reset cache metrics"""
    if not redis:
        raise HTTPException(
            status_code=503,
            detail="Redis not available"
        )
    
    metrics = CacheMetrics(redis)
    await metrics.reset()
    
    return {"message": "Metrics reset"}
```

---

## 🎯 Phase 5: Session Storage (30 minutes)

### Task 5.1: Create `session_manager.py`

**File: `sql_app/session_manager.py`**

```python
import uuid
import json
from datetime import datetime
from typing import Optional, Dict, Any
from redis_client import RedisClient

class SessionManager:
    """Manage user sessions in Redis"""
    
    def __init__(self, redis: RedisClient, session_ttl: int = 86400):
        """
        Initialize session manager
        
        Args:
            redis: Redis client
            session_ttl: Session time-to-live in seconds (default: 24 hours)
        """
        self.redis = redis
        self.session_ttl = session_ttl
    
    async def create_session(
        self,
        user_id: str,
        data: Dict[str, Any] = None
    ) -> str:
        """
        Create new session
        
        Args:
            user_id: User ID
            data: Additional session data
        
        Returns:
            session_id: Unique session identifier
        """
        session_id = str(uuid.uuid4())
        
        session_data = {
            "user_id": user_id,
            "session_id": session_id,
            "created_at": datetime.utcnow().isoformat(),
            "last_activity": datetime.utcnow().isoformat(),
            "ip_address": None,
            "user_agent": None,
            **(data or {})
        }
        
        await self.redis.set(
            f"session:{session_id}",
            session_data,
            ex=self.session_ttl
        )
        
        # Also index by user_id for quick user lookup
        await self.redis.lpush(f"user_sessions:{user_id}", session_id)
        await self.redis.expire(f"user_sessions:{user_id}", self.session_ttl)
        
        return session_id
    
    async def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session data"""
        data = await self.redis.get(f"session:{session_id}")
        if not data:
            return None
        
        # Parse if JSON string
        if isinstance(data, str):
            try:
                return json.loads(data)
            except:
                return None
        
        return data
    
    async def update_activity(self, session_id: str) -> bool:
        """Update last activity timestamp (extends TTL)"""
        session = await self.get_session(session_id)
        if not session:
            return False
        
        session["last_activity"] = datetime.utcnow().isoformat()
        
        await self.redis.set(
            f"session:{session_id}",
            session,
            ex=self.session_ttl
        )
        
        return True
    
    async def destroy_session(self, session_id: str) -> bool:
        """Delete session"""
        session = await self.get_session(session_id)
        if not session:
            return False
        
        await self.redis.delete(f"session:{session_id}")
        
        # Remove from user sessions
        user_id = session.get("user_id")
        if user_id:
            await self.redis.lpop(f"user_sessions:{user_id}")
        
        return True
    
    async def get_user_sessions(self, user_id: str) -> list[Dict]:
        """Get all sessions for a user"""
        session_ids = await self.redis.lrange(f"user_sessions:{user_id}", 0, -1)
        
        sessions = []
        for session_id in session_ids:
            session = await self.get_session(session_id)
            if session:
                sessions.append(session)
        
        return sessions
    
    async def destroy_all_user_sessions(self, user_id: str) -> int:
        """Destroy all sessions for a user (logout everywhere)"""
        session_ids = await self.redis.lrange(f"user_sessions:{user_id}", 0, -1)
        
        deleted = 0
        for session_id in session_ids:
            if await self.destroy_session(session_id):
                deleted += 1
        
        await self.redis.delete(f"user_sessions:{user_id}")
        
        return deleted
    
    async def set_session_data(
        self,
        session_id: str,
        key: str,
        value: Any
    ) -> bool:
        """Set custom data in session"""
        session = await self.get_session(session_id)
        if not session:
            return False
        
        session[key] = value
        await self.redis.set(
            f"session:{session_id}",
            session,
            ex=self.session_ttl
        )
        
        return True
    
    async def get_session_data(self, session_id: str, key: str) -> Any:
        """Get custom data from session"""
        session = await self.get_session(session_id)
        if not session:
            return None
        
        return session.get(key)
```

### Task 5.2: Add Session Endpoints to `main.py`

```python
from session_manager import SessionManager

@app.post("/auth/login-with-session", tags=["Sessions"])
async def login_with_session(
    credentials: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
    redis: Optional[RedisClient] = Depends(get_redis),
    request: Request = None
):
    """
    Login and create Redis session
    
    Returns session_id to be used in subsequent requests
    """
    if not redis:
        raise HTTPException(
            status_code=503,
            detail="Session service not available"
        )
    
    # Authenticate user
    user = authenticate_user(db, credentials.username, credentials.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create session
    manager = SessionManager(redis)
    
    session_data = {
        "ip_address": request.client.host if request else None,
        "user_agent": request.headers.get("user-agent") if request else None,
    }
    
    session_id = await manager.create_session(str(user.id), session_data)
    
    return {
        "session_id": session_id,
        "user_id": str(user.id),
        "user_email": user.email,
        "expires_in_seconds": 86400,
        "message": "Session created successfully"
    }


@app.post("/auth/logout-session", tags=["Sessions"])
async def logout_session(
    session_id: str = Header(...),
    redis: Optional[RedisClient] = Depends(get_redis)
):
    """Logout and destroy session"""
    if not redis:
        raise HTTPException(
            status_code=503,
            detail="Session service not available"
        )
    
    manager = SessionManager(redis)
    if await manager.destroy_session(session_id):
        return {"message": "Logged out successfully"}
    
    raise HTTPException(status_code=404, detail="Session not found")


@app.get("/auth/session-info", tags=["Sessions"])
async def get_session_info(
    session_id: str = Header(...),
    redis: Optional[RedisClient] = Depends(get_redis)
):
    """Get current session information"""
    if not redis:
        raise HTTPException(
            status_code=503,
            detail="Session service not available"
        )
    
    manager = SessionManager(redis)
    session = await manager.get_session(session_id)
    
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    # Update activity
    await manager.update_activity(session_id)
    
    return session


@app.post("/auth/logout-everywhere", tags=["Sessions"])
async def logout_everywhere(
    current_user: User = Depends(get_current_active_user),
    redis: Optional[RedisClient] = Depends(get_redis)
):
    """Logout from all devices (destroy all sessions)"""
    if not redis:
        raise HTTPException(
            status_code=503,
            detail="Session service not available"
        )
    
    manager = SessionManager(redis)
    destroyed = await manager.destroy_all_user_sessions(str(current_user.id))
    
    return {
        "message": f"Logged out from {destroyed} session(s)",
        "sessions_destroyed": destroyed
    }
```

---

## 🎯 Phase 6: Testing & Validation (30 minutes)

### Task 6.1: Test Cache Performance

Create `test_cache_performance.py`:

```python
import asyncio
import time
import json
from sqlalchemy.orm import Session
from database import SessionLocal
from models import User
from redis_client import RedisClient

async def test_cache_performance():
    """Measure cache performance improvement"""
    db = SessionLocal()
    redis = RedisClient()
    
    try:
        await redis.connect()
        
        # Get a random user ID
        user = db.query(User).first()
        if not user:
            print("No users in database")
            return
        
        user_id = str(user.id)
        
        # Test 1: Direct database query
        print("\n📊 Performance Test: User Query")
        print("-" * 50)
        
        start = time.time()
        for _ in range(10):
            user = db.query(User).filter(User.id == user_id).first()
        db_time = time.time() - start
        print(f"Database (10 queries): {db_time*1000:.2f}ms")
        print(f"Per query: {db_time*100:.2f}ms")
        
        # Test 2: Redis cache
        print("\nWarming cache...")
        await redis.set(f"user:{user_id}", user.to_dict(), ex=3600)
        
        start = time.time()
        for _ in range(10):
            cached = await redis.get(f"user:{user_id}")
            data = json.loads(cached)
        cache_time = time.time() - start
        print(f"Redis cache (10 queries): {cache_time*1000:.2f}ms")
        print(f"Per query: {cache_time*100:.2f}ms")
        
        # Calculate improvement
        improvement = db_time / cache_time if cache_time > 0 else 0
        print(f"\n✅ Performance improvement: {improvement:.1f}x faster")
        print(f"Time saved: {(db_time - cache_time)*1000:.2f}ms")
        
    finally:
        await redis.disconnect()
        db.close()

if __name__ == "__main__":
    asyncio.run(test_cache_performance())
```

Run it:
```bash
python test_cache_performance.py
```

### Task 6.2: Test Invalidation

```python
import asyncio
from redis_client import RedisClient
from cache_utils import cache_evict

async def test_cache_invalidation():
    """Test cache invalidation strategies"""
    redis = RedisClient()
    
    try:
        await redis.connect()
        
        print("\n🧪 Testing Cache Invalidation")
        print("-" * 50)
        
        # Set some cache entries
        print("Setting cache entries...")
        await redis.set("user:1", '{"name": "Alice"}', ex=3600)
        await redis.set("user:2", '{"name": "Bob"}', ex=3600)
        await redis.set("users:list:0:10", '[]', ex=1800)
        
        # Verify they exist
        exists_1 = await redis.exists("user:1")
        exists_2 = await redis.exists("user:2")
        exists_list = await redis.exists("users:list:0:10")
        print(f"Cache entries set: user:1={exists_1}, user:2={exists_2}, list={exists_list}")
        
        # Invalidate pattern
        print("\nInvalidating users:list:* pattern...")
        deleted = await cache_evict(redis, "users:list:*")
        print(f"Deleted {deleted} entries")
        
        exists_list = await redis.exists("users:list:0:10")
        print(f"users:list:0:10 still exists: {exists_list}")
        
        # Specific invalidation
        print("\nInvalidating user:1...")
        await redis.delete("user:1")
        exists_1 = await redis.exists("user:1")
        print(f"user:1 still exists: {exists_1}")
        
        print("\n✅ Invalidation tests complete")
        
    finally:
        await redis.disconnect()

if __name__ == "__main__":
    asyncio.run(test_cache_invalidation())
```

---

## 📝 Deliverables Checklist

Create or verify these files exist:

- [ ] `sql_app/redis_client.py` - Redis client wrapper
- [ ] `sql_app/cache_utils.py` - Caching utilities and decorators
- [ ] `sql_app/session_manager.py` - Session management
- [ ] Updated `sql_app/main.py` - Integrated caching in endpoints
- [ ] Updated `sql_app/requirements.txt` - Redis dependencies
- [ ] `test_cache_performance.py` - Performance testing
- [ ] `test_cache_invalidation.py` - Invalidation testing
- [ ] Documentation of cache patterns used

---

## ✅ Evaluation Criteria

**Functionality (40%)**
- [ ] Redis connects on startup
- [ ] Cache-Aside pattern working for user queries
- [ ] Write-Through pattern for updates
- [ ] Cache invalidation on updates
- [ ] Session management complete

**Performance (30%)**
- [ ] Cache hit ratio > 70%
- [ ] Response time improvement > 50x for cached data
- [ ] Memory usage reasonable
- [ ] No N+1 queries when cache hits

**Code Quality (20%)**
- [ ] Error handling for Redis failures
- [ ] Graceful degradation without Redis
- [ ] Proper async/await usage
- [ ] Reusable caching utilities
- [ ] Clear code organization

**Testing (10%)**
- [ ] Tests demonstrate cache effectiveness
- [ ] Invalidation tested
- [ ] Edge cases handled
- [ ] Documentation clear

---

## 🚀 Bonus Challenges

1. **Implement cache warming scheduler** - Pre-warm cache with popular data at regular intervals
2. **Add cache visualization dashboard** - Show hit/miss stats in real-time
3. **Implement LRU eviction** - Automatically remove least-recently-used items
4. **Add Redis Pub/Sub** - Cross-instance cache invalidation
5. **Implement circuit breaker** - Gracefully handle Redis unavailability
6. **Cache compression** - Compress large cached objects
7. **Implement cache preloading** - Load from database on startup

---

## 📚 Resources

- [Redis Commands Reference](https://redis.io/commands)
- [Aioredis Documentation](https://aioredis.readthedocs.io/)
- [FastAPI Dependencies](https://fastapi.tiangolo.com/tutorial/dependencies/)
- [Cache Patterns](https://docs.microsoft.com/en-us/azure/architecture/patterns/cache-aside)

---

**Good luck! 🎉**
