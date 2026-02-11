# Redis Caching & FastAPI Integration - Complete Lecture

## Duration: 1 Hour

## Topics: Redis Basics, Caching Patterns, Cache Invalidation, FastAPI Integration, Session Storage

---

## 📋 Table of Contents

1. [Redis Fundamentals (10 min)](#1-redis-fundamentals)
2. [Caching Patterns (15 min)](#2-caching-patterns)
3. [Cache Invalidation Strategies (10 min)](#3-cache-invalidation-strategies)
4. [FastAPI + Redis Integration (15 min)](#4-fastapi--redis-integration)
5. [Session Storage (5 min)](#5-session-storage)
6. [Performance Benchmarks & Best Practices (5 min)](#6-performance-benchmarks--best-practices)

---

## 1. Redis Fundamentals

**Duration: 10 minutes**

### What is Redis?

Redis (Remote Dictionary Server) is an **in-memory data structure store** that provides:

- **Lightning-fast performance** (microsecond latency)
- **Data persistence** options (RDB snapshots, AOF logs)
- **Multiple data types** (strings, lists, sets, hashes, sorted sets)
- **Built-in expiration** (TTL support)
- **Atomic operations** (thread-safe)

### Why Redis for Caching?

```
Database Query: 50-100ms ❌
Disk I/O: 5-10ms ❌
Redis Lookup: 0.1-1ms ✅
```

### Redis Data Types for Caching

```
1. Strings (Basic caching)
   - Perfect for: Simple values, JSON, serialized objects
   - Example: Cache user profile data

2. Hashes (Object caching)
   - Perfect for: Multiple fields of one entity
   - Example: User ID → {name, email, role}

3. Lists (Queue/Timeline)
   - Perfect for: Message queues, activity feeds
   - Example: Recent user activity

4. Sets (Fast lookups)
   - Perfect for: Membership testing, unique items
   - Example: Active sessions, tags

5. Sorted Sets (Ranked data)
   - Perfect for: Leaderboards, time-series data
   - Example: Top users by score
```

### Redis Setup Overview

**Installation (macOS)**

```bash
brew install redis
redis-server  # Start Redis
redis-cli     # CLI access
```

**Installation (Linux)**

```bash
sudo apt-get install redis-server
sudo systemctl start redis-server
```

**Verification**

```bash
redis-cli ping
# Output: PONG
```

### Key Redis Commands

```bash
# String operations
SET key value EX 3600        # Set with 1-hour expiration
GET key                       # Retrieve value
INCR counter                  # Increment counter
APPEND key " more"            # Append to value

# Hash operations
HSET user:1 name "John"      # Set hash field
HGET user:1 name             # Get hash field
HGETALL user:1               # Get all hash fields

# Expiration
EXPIRE key 3600              # Set 1-hour expiration
TTL key                       # Check time-to-live
PERSIST key                   # Remove expiration

# Key management
DEL key                       # Delete key
EXISTS key                    # Check if exists
KEYS pattern                  # Find keys by pattern
FLUSHDB                       # Clear all keys (careful!)
```

---

## 2. Caching Patterns

**Duration: 15 minutes**

### Pattern 1: Cache-Aside (Lazy Loading)

**How it works:**

1. Application checks Redis first
2. If miss → fetch from database
3. Store result in Redis with TTL
4. Return to client

**Use case:** Non-critical data, user profiles, product info

```python
async def get_user_cached(user_id: str, db: Session, redis_client):
    # Step 1: Try cache
    cache_key = f"user:{user_id}"
    cached_user = await redis_client.get(cache_key)

    if cached_user:
        return json.loads(cached_user)  # Cache hit!

    # Step 2: Cache miss - fetch from database
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        return None

    # Step 3: Store in cache for 1 hour
    await redis_client.setex(
        cache_key,
        3600,
        json.dumps(user.to_dict())
    )

    return user
```

**Advantages:**

- ✅ Simple to implement
- ✅ Only caches accessed data
- ✅ No stale data issues initially
- ✅ Handles missing data gracefully

**Disadvantages:**

- ❌ Cache miss penalty on first request
- ❌ Stale data possible if not invalidated
- ❌ Cache stampede (thundering herd) problem

### Pattern 2: Write-Through

**How it works:**

1. Update database
2. Update cache simultaneously
3. Return success to client

**Use case:** Critical data consistency needed

```python
async def update_user_write_through(user_id: str, updates: dict, db: Session, redis_client):
    # Step 1: Update database
    user = db.query(User).filter(User.id == user_id).first()

    for field, value in updates.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)

    # Step 2: Update cache
    cache_key = f"user:{user_id}"
    await redis_client.setex(
        cache_key,
        3600,
        json.dumps(user.to_dict())
    )

    return user
```

**Advantages:**

- ✅ Cache always up-to-date
- ✅ No stale data
- ✅ Perfect for critical operations

**Disadvantages:**

- ❌ Write latency increases
- ❌ Extra cache operations
- ❌ Unused cache entries waste memory

### Pattern 3: Write-Behind (Write-Back)

**How it works:**

1. Write to cache immediately
2. Asynchronously write to database
3. Return to client immediately

**Use case:** Non-critical data, high-write scenarios

```python
from fastapi import BackgroundTasks

async def update_user_write_behind(
    user_id: str,
    updates: dict,
    db: Session,
    redis_client,
    background_tasks: BackgroundTasks
):
    # Step 1: Update cache immediately
    cache_key = f"user:{user_id}"
    current_data = json.loads(await redis_client.get(cache_key)) or {}
    current_data.update(updates)

    await redis_client.setex(cache_key, 3600, json.dumps(current_data))

    # Step 2: Schedule database update
    background_tasks.add_task(
        persist_to_database,
        user_id,
        current_data,
        db
    )

    return {"message": "Update queued"}

async def persist_to_database(user_id: str, data: dict, db: Session):
    """Run in background after response sent"""
    user = db.query(User).filter(User.id == user_id).first()

    for field, value in data.items():
        setattr(user, field, value)

    db.commit()
```

**Advantages:**

- ✅ Fastest response times
- ✅ Decouples database from API
- ✅ Good for write-heavy workloads

**Disadvantages:**

- ❌ Risk of data loss on crash
- ❌ Complexity in consistency
- ❌ Requires careful error handling

### Pattern 4: Refresh-Ahead

**How it works:**

1. Monitor cache expiration
2. Refresh before expiry
3. Extend TTL automatically

**Use case:** High-traffic critical data

```python
async def get_user_with_refresh_ahead(
    user_id: str,
    db: Session,
    redis_client,
    refresh_threshold: int = 300  # Refresh 5 min before expiry
):
    cache_key = f"user:{user_id}"

    # Check if exists and get TTL
    ttl = await redis_client.ttl(cache_key)

    if ttl == -1:  # No expiration
        return await redis_client.get(cache_key)

    if ttl < refresh_threshold:  # Close to expiry
        # Fetch fresh data
        user = db.query(User).filter(User.id == user_id).first()
        await redis_client.setex(cache_key, 3600, json.dumps(user.to_dict()))
        return user

    return await redis_client.get(cache_key)
```

**Advantages:**

- ✅ No stale data
- ✅ Continuous availability
- ✅ No cache misses for popular items

**Disadvantages:**

- ❌ Extra database load
- ❌ More complex logic
- ❌ Wasted refreshes on rarely used data

### Caching Pattern Comparison

| Pattern           | Consistency | Response Time | DB Load      | Complexity |
| ----------------- | ----------- | ------------- | ------------ | ---------- |
| **Cache-Aside**   | Eventual    | Moderate      | High on miss | Low        |
| **Write-Through** | Strong      | Moderate      | Moderate     | Low        |
| **Write-Behind**  | Eventual    | Very Fast     | Low          | High       |
| **Refresh-Ahead** | Strong      | Very Fast     | Moderate     | High       |

---

## 3. Cache Invalidation Strategies

**Duration: 10 minutes**

### The Hard Problem

> "There are only two hard problems in Computer Science: cache invalidation and naming things." - Phil Karlton

### Strategy 1: Time-Based Expiration (TTL)

**Concept:** Cache automatically expires after time period

```python
# Cache for 15 minutes
await redis_client.setex("user:1", 900, user_data)

# Cache for 1 hour
await redis_client.setex("user:1", 3600, user_data)

# No expiration (dangerous!)
await redis_client.set("user:1", user_data)
```

**Best for:**

- Non-critical data
- Data that changes infrequently
- Simple implementations

**TTL Guidelines:**

```
Frequently changing data: 5-15 minutes
User profiles: 1 hour
Product catalogs: 2-4 hours
Configuration: 1-8 hours
Leaderboards: 5-30 minutes
Session data: 24 hours
```

### Strategy 2: Event-Based Invalidation

**Concept:** Explicitly delete cache when data changes

```python
@app.put("/users/{user_id}")
async def update_user(user_id: str, updates: dict, db: Session, redis_client):
    # Update database
    user = db.query(User).filter(User.id == user_id).first()

    for field, value in updates.items():
        setattr(user, field, value)

    db.commit()

    # Invalidate cache
    await redis_client.delete(f"user:{user_id}")
    await redis_client.delete("users:all")  # Invalidate list too

    return user
```

**Best for:**

- Critical data that must be fresh
- Small cache sets
- Rare updates

**Granular Invalidation:**

```python
async def delete_user_cache(user_id: str, redis_client):
    """Delete all cache keys related to a user"""
    patterns = [
        f"user:{user_id}",
        f"user:{user_id}:posts",
        f"user:{user_id}:followers",
        "users:all",
        "leaderboard:*"
    ]

    for pattern in patterns:
        keys = await redis_client.keys(pattern)
        for key in keys:
            await redis_client.delete(key)
```

### Strategy 3: Tag-Based Invalidation

**Concept:** Group related cache keys with tags

```python
# Store mapping: tag → keys
# When tag invalidated, delete all keys

class TaggedCache:
    def __init__(self, redis_client):
        self.redis = redis_client

    async def set_with_tags(
        self,
        key: str,
        value: str,
        tags: list[str],
        ttl: int = 3600
    ):
        # Store the actual value
        await self.redis.setex(key, ttl, value)

        # Add key to each tag
        for tag in tags:
            tag_key = f"tag:{tag}"
            await self.redis.sadd(tag_key, key)
            await self.redis.expire(tag_key, ttl)

    async def invalidate_tag(self, tag: str):
        """Delete all keys with this tag"""
        tag_key = f"tag:{tag}"
        keys = await self.redis.smembers(tag_key)

        for key in keys:
            await self.redis.delete(key)

        await self.redis.delete(tag_key)

# Usage
await cache.set_with_tags(
    key="user:1",
    value=user_data,
    tags=["user", "user:1", "active_users"],
    ttl=3600
)

# Invalidate all user-related caches
await cache.invalidate_tag("user")
```

**Best for:**

- Complex relationships
- Cascading updates
- Related data sets

### Strategy 4: Conditional Invalidation

**Concept:** Check if invalidation needed before deleting

```python
async def smart_invalidate_user(user_id: str, changed_fields: list[str], redis_client):
    """Only invalidate if relevant fields changed"""

    # Fields that affect different caches
    profile_fields = {"full_name", "email", "phone_number"}
    role_fields = {"role", "permissions"}
    stats_fields = {"login_count", "last_login"}

    if any(field in profile_fields for field in changed_fields):
        await redis_client.delete(f"user:{user_id}")
        await redis_client.delete("users:list")

    if any(field in role_fields for field in changed_fields):
        await redis_client.delete(f"user:{user_id}:permissions")
        await redis_client.delete("users:by_role")

    if any(field in stats_fields for field in changed_fields):
        await redis_client.delete(f"user:{user_id}:stats")
```

**Best for:**

- Large cache sets
- Performance optimization
- Selective updates

### Cache Invalidation Best Practices

```
1. **Default to TTL**: Always set expiration
2. **Be Granular**: Invalidate only affected keys
3. **Document Dependencies**: Comment what keys depend on each other
4. **Monitor Hits/Misses**: Track cache effectiveness
5. **Test Invalidation**: Verify fresh data on updates
6. **Plan for Failures**: Redis crashes, network issues
```

---

## 4. FastAPI + Redis Integration

**Duration: 15 minutes**

### Setup & Configuration

**Install Dependencies**

```bash
pip install redis aioredis
```

**Redis Client Initialization**

```python
import aioredis
from typing import Optional

class RedisClient:
    def __init__(self, url: str = "redis://localhost:6379"):
        self.url = url
        self.client: Optional[aioredis.Redis] = None

    async def connect(self):
        """Establish connection"""
        self.client = await aioredis.from_url(self.url)

    async def disconnect(self):
        """Close connection"""
        await self.client.close()

    async def get(self, key: str):
        """Get value by key"""
        return await self.client.get(key)

    async def set(self, key: str, value: str, ex: int = None):
        """Set value with optional expiration"""
        await self.client.set(key, value, ex=ex)

    async def delete(self, key: str):
        """Delete key"""
        await self.client.delete(key)

    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        return await self.client.exists(key)

    async def ttl(self, key: str) -> int:
        """Get time to live in seconds"""
        return await self.client.ttl(key)
```

### FastAPI Dependency Injection

```python
from fastapi import Depends, FastAPI

app = FastAPI()
redis_client = RedisClient()

@app.on_event("startup")
async def startup():
    """Connect to Redis on app startup"""
    await redis_client.connect()

@app.on_event("shutdown")
async def shutdown():
    """Disconnect from Redis on app shutdown"""
    await redis_client.disconnect()

async def get_redis() -> RedisClient:
    return redis_client

# Usage in endpoints
@app.get("/users/{user_id}")
async def get_user(user_id: str, redis: RedisClient = Depends(get_redis)):
    # Use redis client
    cached = await redis.get(f"user:{user_id}")
    if cached:
        return json.loads(cached)
```

### Caching Decorator

**Create reusable cache decorator**

```python
from functools import wraps
from datetime import timedelta
import json

def cache(
    key_builder: callable,
    ttl: int = 3600,
    namespace: str = ""
):
    """
    Decorator for caching async function results

    Args:
        key_builder: Function to build cache key from arguments
        ttl: Time-to-live in seconds
        namespace: Prefix for cache keys
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, redis_client: RedisClient = None, **kwargs):
            if not redis_client:
                return await func(*args, **kwargs)

            # Build cache key
            cache_key = key_builder(*args, **kwargs)
            if namespace:
                cache_key = f"{namespace}:{cache_key}"

            # Try cache first
            cached = await redis_client.get(cache_key)
            if cached:
                return json.loads(cached)

            # Cache miss - execute function
            result = await func(*args, **kwargs)

            # Store in cache
            await redis_client.set(
                cache_key,
                json.dumps(result, default=str),
                ex=ttl
            )

            return result

        return wrapper
    return decorator

# Usage
@cache(
    key_builder=lambda user_id: f"user:{user_id}",
    ttl=3600,
    namespace="profile"
)
async def get_user_profile(user_id: str, db: Session):
    return db.query(User).filter(User.id == user_id).first()
```

### Complete Example: Caching User Queries

```python
@app.get("/users/{user_id}")
async def get_user(
    user_id: str,
    db: Session = Depends(get_db),
    redis: RedisClient = Depends(get_redis)
) -> UserResponse:
    """Get user with Redis caching (Cache-Aside pattern)"""
    cache_key = f"user:{user_id}"

    # Try cache first
    cached = await redis.get(cache_key)
    if cached:
        return UserResponse(**json.loads(cached))

    # Cache miss
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Store in cache
    await redis.set(
        cache_key,
        json.dumps(user.to_dict()),
        ex=3600  # 1 hour
    )

    return user

@app.get("/users")
async def list_users(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    redis: RedisClient = Depends(get_redis)
) -> list[UserResponse]:
    """List users with Redis caching"""
    cache_key = f"users:skip:{skip}:limit:{limit}"

    # Try cache
    cached = await redis.get(cache_key)
    if cached:
        return [UserResponse(**u) for u in json.loads(cached)]

    # Fetch from DB
    users = db.query(User).offset(skip).limit(limit).all()

    # Cache
    await redis.set(
        cache_key,
        json.dumps([u.to_dict() for u in users]),
        ex=1800  # 30 minutes
    )

    return users

@app.put("/users/{user_id}")
async def update_user(
    user_id: str,
    update: UserUpdate,
    db: Session = Depends(get_db),
    redis: RedisClient = Depends(get_redis)
) -> UserResponse:
    """Update user and invalidate cache (Write-Through pattern)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Update database
    for field, value in update.dict(exclude_unset=True).items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)

    # Invalidate cache
    await redis.delete(f"user:{user_id}")
    await redis.delete("users:*")  # Use SCAN to delete pattern

    return user
```

### Bulk Cache Operations

```python
async def cache_all_active_users(db: Session, redis: RedisClient):
    """Pre-warm cache with all active users"""
    users = db.query(User).filter(User.is_active == True).all()

    for user in users:
        await redis.set(
            f"user:{user.id}",
            json.dumps(user.to_dict()),
            ex=3600
        )

    return f"Cached {len(users)} users"

@app.post("/admin/warm-cache")
async def warm_cache(
    db: Session = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
    current_user = Depends(require_admin)
):
    """API endpoint to warm cache (admin-only)"""
    message = await cache_all_active_users(db, redis)
    return {"message": message}
```

---

## 5. Session Storage

**Duration: 5 minutes**

### Redis as Session Store

**Why Redis for sessions?**

- ✅ Extremely fast
- ✅ Perfect for temporary data
- ✅ Built-in expiration
- ✅ Atomic operations

### Session Storage Pattern

```python
import uuid
from datetime import datetime, timedelta

class SessionManager:
    def __init__(self, redis_client: RedisClient, session_ttl: int = 86400):
        self.redis = redis_client
        self.session_ttl = session_ttl

    async def create_session(self, user_id: str, data: dict = None):
        """Create new session"""
        session_id = str(uuid.uuid4())
        session_data = {
            "user_id": user_id,
            "created_at": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat(),
            **(data or {})
        }

        await self.redis.set(
            f"session:{session_id}",
            json.dumps(session_data),
            ex=self.session_ttl
        )

        return session_id

    async def get_session(self, session_id: str):
        """Retrieve session data"""
        data = await self.redis.get(f"session:{session_id}")
        if not data:
            return None
        return json.loads(data)

    async def update_activity(self, session_id: str):
        """Update last activity timestamp (extends TTL)"""
        session = await self.get_session(session_id)
        if not session:
            return False

        session["last_activity"] = datetime.now().isoformat()

        await self.redis.set(
            f"session:{session_id}",
            json.dumps(session),
            ex=self.session_ttl
        )

        return True

    async def destroy_session(self, session_id: str):
        """Delete session"""
        await self.redis.delete(f"session:{session_id}")

# Usage
session_manager = SessionManager(redis_client)

@app.post("/login-with-session")
async def login_with_session(
    credentials: LoginRequest,
    db: Session = Depends(get_db),
    redis: RedisClient = Depends(get_redis)
):
    """Login and store session in Redis"""
    user = authenticate_user(db, credentials.email, credentials.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Create session
    manager = SessionManager(redis)
    session_id = await manager.create_session(str(user.id))

    return {
        "session_id": session_id,
        "user_id": str(user.id),
        "expires_in": 86400
    }

@app.get("/protected-with-session")
async def protected_endpoint(
    session_id: str = Header(...),
    redis: RedisClient = Depends(get_redis)
):
    """Protected endpoint using Redis sessions"""
    manager = SessionManager(redis)
    session = await manager.get_session(session_id)

    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")

    # Update activity
    await manager.update_activity(session_id)

    return {
        "message": "Access granted",
        "user_id": session["user_id"]
    }
```

---

## 6. Performance Benchmarks & Best Practices

**Duration: 5 minutes**

### Performance Comparison

```
Operation              Time        vs Database
--------------------------------------------------
Redis GET            0.1-1ms     50-100x faster
Redis SET            0.1-1ms     50-100x faster
Database Query       50-100ms    Baseline
Disk Read           5-10ms       Variable

Scenario: 1000 concurrent requests for same data
Without Cache: 50-100 seconds
With Cache:    0.1-1 second
Improvement:   50-1000x faster!
```

### Memory Management

```python
# Monitor memory usage
@app.get("/admin/redis-stats")
async def redis_stats(redis: RedisClient = Depends(get_redis)):
    """Check Redis memory and stats"""
    info = await redis.client.info('memory')
    return {
        "used_memory_mb": info['used_memory'] / 1024 / 1024,
        "max_memory_mb": info.get('maxmemory', 'unlimited') / 1024 / 1024,
        "memory_usage_percent": (
            info['used_memory'] / info['maxmemory'] * 100
            if info.get('maxmemory') else 0
        )
    }

# Implement eviction policy in Redis config
# maxmemory 2gb
# maxmemory-policy allkeys-lru  # Delete least recently used
```

### Cache Metrics & Monitoring

```python
class CacheMetrics:
    def __init__(self, redis_client: RedisClient):
        self.redis = redis_client

    async def log_hit(self, key: str):
        """Record cache hit"""
        await self.redis.incr(f"metrics:hits")

    async def log_miss(self, key: str):
        """Record cache miss"""
        await self.redis.incr(f"metrics:misses")

    async def get_hit_ratio(self) -> float:
        """Calculate hit ratio"""
        hits = int(await self.redis.get("metrics:hits") or 0)
        misses = int(await self.redis.get("metrics:misses") or 0)
        total = hits + misses

        if total == 0:
            return 0

        return (hits / total) * 100

@app.get("/admin/cache-metrics")
async def cache_metrics(redis: RedisClient = Depends(get_redis)):
    """Get cache performance metrics"""
    metrics = CacheMetrics(redis)

    return {
        "hit_ratio_percent": await metrics.get_hit_ratio(),
        "hits": int(await redis.get("metrics:hits") or 0),
        "misses": int(await redis.get("metrics:misses") or 0)
    }
```

### Best Practices Checklist

```
✅ Cache Setup
  □ Test Redis connection on startup
  □ Add proper error handling for Redis failures
  □ Implement connection pooling
  □ Set appropriate max connections

✅ Cache Keys
  □ Use consistent naming: domain:object:id or domain:action:param
  □ Include version in key if schema changes
  □ Keep keys reasonably short
  □ Document key patterns

✅ Cache TTL
  □ Set TTL for all cached data
  □ Use shorter TTL for frequently changing data
  □ Use longer TTL for static data
  □ Never cache without expiration (except queues)

✅ Cache Invalidation
  □ Invalidate on write (Write-Through)
  □ Or use TTL for eventual consistency (Cache-Aside)
  □ Document what data invalidates what cache
  □ Test invalidation logic

✅ Error Handling
  □ Graceful degradation if Redis is down
  □ Fallback to database if cache fails
  □ Log cache errors separately
  □ Don't expose cache errors to clients

✅ Monitoring
  □ Track hit/miss ratios
  □ Monitor memory usage
  □ Alert on high memory usage
  □ Monitor connection count
  □ Track slow cache operations

✅ Security
  □ Use password-protected Redis
  □ Place Redis behind firewall
  □ Encrypt sensitive cached data
  □ Validate cached data before using
  □ Don't cache password hashes/tokens
```

### Common Pitfalls & Solutions

```
❌ Problem: Cache stampede (thundering herd)
✅ Solution: Lock mechanism during cache refresh
   await redis.set(f"{key}:lock", "1", ex=5)

❌ Problem: Stale data
✅ Solution: Combine TTL with event-based invalidation

❌ Problem: Redis memory grows unbounded
✅ Solution: Set maxmemory and eviction policy

❌ Problem: Expensive operations still run on cache miss
✅ Solution: Implement probabilistic early expiration

❌ Problem: Cache false positives
✅ Solution: Check database value after cache miss

❌ Problem: Hard to debug cached data issues
✅ Solution: Log all cache operations, include cache status in response headers
```

### Real-World Example: Complete User Cache

```python
class UserCache:
    def __init__(self, redis: RedisClient, ttl: int = 3600):
        self.redis = redis
        self.ttl = ttl

    async def get_user(self, user_id: str, db: Session) -> User:
        """Get user with automatic caching"""
        key = f"user:{user_id}"

        # Try cache
        cached = await self.redis.get(key)
        if cached:
            await self.redis.incr("metrics:cache_hits")
            return User(**json.loads(cached))

        # Cache miss
        await self.redis.incr("metrics:cache_misses")
        user = db.query(User).filter(User.id == user_id).first()

        if user:
            await self.redis.set(
                key,
                json.dumps(user.to_dict()),
                ex=self.ttl
            )

        return user

    async def update_user(self, user_id: str, data: dict, db: Session) -> User:
        """Update user and invalidate cache"""
        user = db.query(User).filter(User.id == user_id).first()

        # Update DB
        for field, value in data.items():
            setattr(user, field, value)
        db.commit()
        db.refresh(user)

        # Invalidate all user caches
        await self.redis.delete(f"user:{user_id}")
        await self.redis.delete(f"user:{user_id}:*")

        return user
```

---

## 📝 Summary

### Key Takeaways

1. **Redis is essential for performance** - Microsecond latency vs milliseconds
2. **Cache-Aside is safest pattern** - Simple, handles stale data well
3. **TTL + Invalidation is best approach** - Combines benefits of both
4. **Graceful degradation required** - Redis failures shouldn't break app
5. **Monitor your cache** - Hit ratio tells you if caching helps
6. **Organize your keys** - Consistent naming makes it manageable
7. **Think about consistency** - Choose appropriate pattern for your data

### When to Use Redis

✅ **Use Redis for:**

- User sessions
- Rate limiting counters
- Real-time counters (views, likes)
- Job queues
- Leaderboards
- Cache for expensive queries
- Pub/Sub messaging

❌ **Don't use Redis for:**

- Permanent data (no durability guarantee)
- Large binary files (memory inefficient)
- Complex queries
- Sensitive data without encryption

---

## 🎯 Practice Assignment

### Task: Add Redis Caching to Your FastAPI Application

**Requirements:**

1. Install Redis and connect to FastAPI
2. Implement Cache-Aside pattern for user queries
3. Add Write-Through pattern for user updates
4. Create cache warming endpoint for admin
5. Implement session storage in Redis
6. Add cache metrics tracking
7. Test cache invalidation
8. Add graceful degradation if Redis fails

**Deliverables:**

- ✅ `redis_client.py` - Redis client class
- ✅ `cache_utils.py` - Caching utilities and decorators
- ✅ Updated `main.py` - Integrated caching
- ✅ Session management implementation
- ✅ Cache metrics endpoints
- ✅ Test cache effectiveness with metrics

**Evaluation Criteria:**

- Cache hit ratio > 80% for repeated queries
- Response time improvement > 50x for cached data
- Proper cache invalidation on updates
- Graceful handling of Redis failures
- Code organization and documentation

See `REDIS_PRACTICE_ASSIGNMENT.md` for detailed instructions.

---

## 🔗 Reference Links

**Redis Documentation:** https://redis.io/documentation
**Python aioredis:** https://aioredis.readthedocs.io/
**FastAPI Caching:** https://fastapi.tiangolo.com/advanced/

---

**Duration Breakdown:**

- Fundamentals: 10 min
- Caching Patterns: 15 min
- Invalidation: 10 min
- FastAPI Integration: 15 min
- Session Storage: 5 min
- Best Practices: 5 min
- **Total: 60 minutes**
