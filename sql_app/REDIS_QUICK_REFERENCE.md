# Redis Caching - Quick Reference Guide

## 🚀 Quick Start (5 minutes)

```bash
# 1. Install Redis
brew install redis && brew services start redis

# 2. Verify
redis-cli ping  # Output: PONG

# 3. Install dependencies
pip install -r sql_app/requirements.txt

# 4. Start app
cd sql_app
python -m uvicorn main:app --reload
```

**Check startup logs:**

```
✅ Migrations completed successfully!
✅ Connected to Redis
```

---

## 📚 Key Concepts (30 seconds each)

### Cache-Aside Pattern

- Check cache first
- On miss: fetch from DB, then store in cache
- Simple, flexible, handles stale data

### Write-Through Pattern

- Update DB and cache simultaneously
- Cache always current
- Higher write latency

### TTL (Time-To-Live)

- Auto-expiration for cache keys
- Eventual consistency approach
- Balances freshness vs performance

### Cache Invalidation

- Explicit: Delete when data changes
- TTL-based: Automatic expiration
- Pattern-based: Delete multiple keys

---

## 🔧 Code Examples

### Basic Caching (1 minute)

```python
# In your endpoint
cache_key = f"user:{user_id}"

# Try cache
if redis:
    cached = await redis.get(cache_key)
    if cached:
        return cached

# Cache miss - get from DB
user = db.query(User).filter(User.id == user_id).first()

# Store in cache
if redis:
    await redis.set(cache_key, user.to_dict(), ex=3600)

return user
```

### Cache Invalidation (1 minute)

```python
# When updating data
db.update(...)
db.commit()

# Invalidate cache
if redis:
    await redis.delete(f"user:{user_id}")
    await redis.delete_pattern("users:list:*")
```

### Cache Metrics (30 seconds)

```python
# Get cache stats
metrics = CacheMetrics(redis)
stats = await metrics.get_stats()
print(f"Hit ratio: {stats['hit_ratio_percent']}%")
```

### Session Storage (1 minute)

```python
# Create session
manager = SessionManager(redis)
session_id = await manager.create_session(user_id)

# Get session
session = await manager.get_session(session_id)

# Update activity (extends TTL)
await manager.update_activity(session_id)

# Destroy session
await manager.destroy_session(session_id)
```

---

## 🔍 Testing Commands

```bash
# Test cached endpoint
curl http://localhost:8000/users-cached
# First call: slow (hits DB)
# Second call: fast (hits cache)

# Check cache stats
curl http://localhost:8000/admin/cache/stats | jq '.hit_ratio_percent'

# Warm cache
curl -X POST http://localhost:8000/admin/cache/warm

# Clear cache
curl -X POST "http://localhost:8000/admin/cache/clear?pattern=*"

# Monitor Redis in real-time
redis-cli monitor
```

---

## 📊 Performance Benchmarks

```
Operation              Time (no cache)    Time (cached)    Improvement
────────────────────────────────────────────────────────────────────
GET single user        80-100ms           2-5ms            20-30x
GET user list          100-150ms          3-8ms            15-25x
Repeated query         Linear (80ms each) Constant (3ms)   Infinite!
```

**Rule of thumb:** Cache saves 90%+ time on repeated requests

---

## 🛠️ API Endpoints Cheat Sheet

### User Caching

```
GET    /users-cached              # List users (cached, 30 min)
GET    /users-cached/{user_id}    # Get user (cached, 1 hour)
PUT    /users-cached/{user_id}    # Update & invalidate cache
```

### Admin Cache Management

```
POST   /admin/cache/warm          # Pre-load all active users
GET    /admin/cache/stats         # See hit/miss metrics
POST   /admin/cache/clear         # Delete cache by pattern
POST   /admin/cache/metrics/reset # Reset hit/miss counters
```

### Session Management

```
POST   /auth/login-with-session   # Create session
GET    /auth/session-info         # Get current session
POST   /auth/logout-session       # Destroy single session
POST   /auth/logout-everywhere    # Logout from all devices
```

---

## 🎯 Common TTL Values

```
Data Type              Freshness Requirement    TTL
────────────────────────────────────────────────────────────
User profiles          Medium                  1 hour
Product catalogs       Low                     4 hours
User lists             Medium                  30 minutes
Leaderboards          High                    5 minutes
Settings/config       Very low                8 hours
Session data          N/A                     24 hours
```

---

## 🐛 Troubleshooting Quick Fixes

### Redis Won't Connect

```bash
# Check if Redis is running
brew services list | grep redis

# Start it
brew services start redis

# Test
redis-cli ping
```

### Cache Not Working

```bash
# Verify you're using cached endpoints
curl http://localhost:8000/users-cached  # ✅ Uses cache
curl http://localhost:8000/users         # ❌ Doesn't use cache

# Check Redis directly
redis-cli keys "*"
redis-cli get "user:1"
```

### Memory Usage High

```bash
# Clear all cache
curl -X POST "http://localhost:8000/admin/cache/clear?pattern=*"

# Or clear specific pattern
curl -X POST "http://localhost:8000/admin/cache/clear?pattern=users:list:*"

# Check current usage
curl http://localhost:8000/admin/cache/stats | jq '.memory_usage_mb'
```

### Hit Ratio Low

```bash
# Is data changing too fast (TTL too short)?
# → Increase TTL value

# Not enough cache keys?
# → Use /admin/cache/warm to pre-load

# Queries not actually cached?
# → Check you're using /users-cached endpoint

# Clear and rebuild cache
POST /admin/cache/clear?pattern=*
POST /admin/cache/warm
```

---

## 📋 Lazy Developer Copy-Paste

### Add cache to any endpoint (5 min)

**Before:**

```python
@app.get("/data")
async def get_data(db: Session = Depends(get_db)):
    return db.query(Data).all()
```

**After:**

```python
@app.get("/data-cached")
async def get_data_cached(
    db: Session = Depends(get_db),
    redis: Optional[RedisClient] = Depends(get_redis)
):
    # Try cache
    if redis:
        cached = await redis.get("data:list")
        if cached:
            await CacheMetrics(redis).record_hit("data:list")
            return json.loads(cached)
        await CacheMetrics(redis).record_miss("data:list")

    # Fetch data
    data = db.query(Data).all()

    # Cache it
    if redis:
        await redis.set("data:list", [d.to_dict() for d in data], ex=3600)

    return data
```

### Add invalidation (next 5 min)

**When updating:**

```python
# After update
if redis:
    await redis.delete("data:list")
    await redis.delete_pattern("data:*")
```

---

## 🎓 Learning Timeline

### Today (30 min)

- [ ] Read: Fundamentals section
- [ ] Read: Caching Patterns
- [ ] Test: Run `curl http://localhost:8000/users-cached`

### This Week (2 hours)

- [ ] Read: Cache Invalidation
- [ ] Read: FastAPI Integration
- [ ] Implement: One cached endpoint yourself
- [ ] Monitor: Check cache stats

### This Month (5 hours)

- [ ] Complete: Full Practice Assignment
- [ ] Optimize: Adjust TTL values
- [ ] Implement: Caching for all endpoints
- [ ] Monitor: Maintain >80% hit ratio

---

## 🚨 Safety Checklist

- [ ] Never cache sensitive data (passwords, tokens) without encryption
- [ ] Always set TTL (except for queues)
- [ ] Monitor memory usage
- [ ] Test invalidation logic
- [ ] Have fallback if Redis fails
- [ ] Document what data is cached
- [ ] Plan for Redis persistence (RDB/AOF)

---

## 📞 When to Use Redis Caching

### ✅ Perfect For

- Read-heavy applications
- Expensive database queries
- User session data
- Rate limiting counters
- Leaderboards / rankings
- Real-time counters

### ❌ Don't Use For

- Sensitive data (without encryption)
- Large binary files
- Data requiring transactions
- Primary data store (use DB)
- Infrequently accessed data

---

## 🔗 Key Files Reference

| File                           | Lines | Purpose              |
| ------------------------------ | ----- | -------------------- |
| `redis_client.py`              | 250+  | Redis client wrapper |
| `cache_utils.py`               | 200+  | Utilities & metrics  |
| `session_manager.py`           | 200+  | Session storage      |
| `main.py`                      | +450  | Endpoints integrated |
| `REDIS_CACHING_LECTURE.md`     | 1000+ | Full lecture         |
| `REDIS_PRACTICE_ASSIGNMENT.md` | 500+  | Hands-on practice    |

---

## ⚡ Pro Tips

1. **Use cache warming** for popular data

   ```bash
   curl -X POST http://localhost:8000/admin/cache/warm
   ```

2. **Monitor hit ratio** - Aim for >80%

   ```bash
   curl http://localhost:8000/admin/cache/stats
   ```

3. **Different TTLs** for different data
   - Stable data: 4-8 hours
   - Changing data: 5-30 minutes
   - Hot data: 1-5 minutes

4. **Invalidate strategically**
   - Only when necessary
   - Use patterns to delete related keys
   - Log invalidations for debugging

5. **Test cache-agnostic**
   - App should work without Redis
   - Graceful degradation built-in
   - No client-facing errors

---

## 📈 Goal: 80% Cache Hit Ratio

**Week 1:** 40-50% (baseline)
↓
**Week 2:** 60-70% (warmed cache)
↓
**Week 3:** 75-85% (optimized TTL)
↓
**Week 4:** 85%+ (production-ready)

**Track with:**

```bash
watch -n 5 'curl -s http://localhost:8000/admin/cache/stats | jq .hit_ratio_percent'
```

---

**Remember:** The best cache is the one closest to the data! Redis sits between your app and database, making everything faster.

Happy caching! 🚀
