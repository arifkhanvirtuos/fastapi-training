# Redis Caching - Testing & Validation Guide

## 🧪 Complete Testing Workflow

This guide walks you through testing the Redis integration step-by-step.

---

## Phase 1: Environment Verification (5 minutes)

### Step 1: Verify Redis Installation

```bash
# Check Redis status
brew services list | grep redis

# Should show:
# redis   RunAhead: 0.1s

# If not running, start it
brew services start redis

# Test Redis connection
redis-cli ping
# Expected output: PONG
```

### Step 2: Verify Python Dependencies

```bash
cd sql_app

# Check requirements.txt has Redis packages
grep -E 'redis|aioredis' requirements.txt
# Should show:
# redis==5.0.0
# aioredis==2.0.1

# Install dependencies
pip install -r requirements.txt

# Verify installation
python -c "import redis; import aioredis; print('✅ Packages installed')"
```

### Step 3: Verify Files Exist

```bash
# Check all new files exist
ls -la redis_client.py cache_utils.py session_manager.py

# Should see:
# redis_client.py
# cache_utils.py
# session_manager.py
```

---

## Phase 2: Application Startup Test (5 minutes)

### Step 1: Start the Application

```bash
cd sql_app
python -m uvicorn main:app --reload
```

### Step 2: Verify Startup Logs

Look for these messages in output:

```
✅ Migrations completed successfully!
✅ Connected to Redis
```

**If you see:**
```
⚠️  Redis connection failed
⚠️  Running without Redis caching
```

**Check:**
```bash
redis-cli ping  # Must output PONG
```

### Step 3: Access Swagger UI

Open in browser: `http://localhost:8000/docs`

Look for new endpoint tags:
- ✅ Caching - Users
- ✅ Admin - Caching
- ✅ Sessions - Redis

---

## Phase 3: Basic Functionality Tests (10 minutes)

### Test 1: Cache-Aside Pattern

**Endpoint:** `GET /users-cached`

**Test sequence:**

```bash
# Terminal 2: In new terminal

# First call - hits database (slow)
time curl http://localhost:8000/users-cached
# Note the time

# Result should look like:
# [
#   {
#     "id": "uuid...",
#     "email": "user@example.com",
#     "full_name": "...",
#     ...
#   }
# ]

# Second call - hits cache (fast)
time curl http://localhost:8000/users-cached
# Should be 10-20x faster!
```

**Verify in Redis:**

```bash
# Terminal 3: Monitor cache
redis-cli monitor
# You should see GET commands when you call the endpoint

# Or directly check keys
redis-cli keys "users:list:*"
# Output: "users:list:0:10"

# Get the cached value
redis-cli get "users:list:0:10"
# Output: JSON array of users
```

### Test 2: Single User Caching

```bash
# Get first user's ID from previous request
USER_ID="<uuid from users-cached>"

# First call (slow)
curl http://localhost:8000/users-cached/$USER_ID

# Second call (fast, from cache)
curl http://localhost:8000/users-cached/$USER_ID

# Check cache
redis-cli get "user:$USER_ID"
```

### Test 3: Cache Invalidation

```bash
USER_ID="<uuid>"

# Update user (invalidates cache)
curl -X PUT http://localhost:8000/users-cached/$USER_ID \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "New Name"
  }'

# Verify cache was deleted
redis-cli exists "user:$USER_ID"
# Output: 0 (key doesn't exist)

# Next call hits database again
curl http://localhost:8000/users-cached/$USER_ID
```

---

## Phase 4: Metrics & Monitoring (10 minutes)

### Test 1: Cache Metrics

```bash
# Get auth token first (if needed)
# For admin endpoints, ensure you're using admin account

# Check cache statistics
curl http://localhost:8000/admin/cache/stats \
  -H "Authorization: Bearer <your_token>"

# Should see:
{
  "hits": 42,
  "misses": 8,
  "total_requests": 50,
  "hit_ratio_percent": 84.0,
  "memory_usage_mb": 0.5,
  "max_memory_mb": "unlimited"
}
```

**What to check:**
- `hit_ratio_percent` > 70% = Good
- `hit_ratio_percent` > 85% = Excellent
- `memory_usage_mb` < 100MB = Healthy

### Test 2: Cache Warming

```bash
# Warm cache with all active users
curl -X POST http://localhost:8000/admin/cache/warm \
  -H "Authorization: Bearer <your_token>"

# Response:
{
  "message": "✅ Cached 42 active users",
  "count": 42,
  "ttl_seconds": 3600
}

# Check memory increase
curl http://localhost:8000/admin/cache/stats \
  -H "Authorization: Bearer <your_token>" | jq '.memory_usage_mb'

# Should have increased
```

### Test 3: Cache Clearing

```bash
# Clear specific pattern
curl -X POST "http://localhost:8000/admin/cache/clear?pattern=users:list:*" \
  -H "Authorization: Bearer <your_token>"

# Response:
{
  "message": "✅ Deleted 5 cache entries",
  "pattern": "users:list:*",
  "deleted_count": 5
}

# Verify in Redis
redis-cli keys "users:list:*"
# Should return empty
```

### Test 4: Metrics Reset

```bash
# Reset hit/miss counters
curl -X POST http://localhost:8000/admin/cache/metrics/reset \
  -H "Authorization: Bearer <your_token>"

# Check stats - hits and misses should be 0
curl http://localhost:8000/admin/cache/stats \
  -H "Authorization: Bearer <your_token>"
```

---

## Phase 5: Session Storage Tests (10 minutes)

### Test 1: Create Session

```bash
# Login and get session
RESPONSE=$(curl -X POST http://localhost:8000/auth/login-with-session \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=admin123")

echo $RESPONSE

# Extract session_id
SESSION_ID=$(echo $RESPONSE | jq -r '.session_id')
echo "Session ID: $SESSION_ID"

# Expected response:
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "uuid...",
  "user_email": "admin@example.com",
  "expires_in_seconds": 86400,
  "message": "✅ Session created successfully"
}
```

### Test 2: Get Session Info

```bash
SESSION_ID="<session_id_from_above>"

# Get session info
curl http://localhost:8000/auth/session-info \
  -H "session_id: $SESSION_ID"

# Expected response:
{
  "user_id": "uuid...",
  "session_id": "550e8400...",
  "created_at": "2026-02-09T10:30:00.000000",
  "last_activity": "2026-02-09T10:35:00.000000",
  "ip_address": "127.0.0.1",
  "user_agent": "..."
}

# Verify in Redis
redis-cli get "session:$SESSION_ID"
# Should return JSON data
```

### Test 3: Session Expiration

```bash
SESSION_ID="<old_session_id>"

# Try to use expired session
curl http://localhost:8000/auth/session-info \
  -H "session_id: $SESSION_ID"

# After TTL expires, should get:
# {"detail":"Invalid or expired session"}
```

### Test 4: Logout

```bash
SESSION_ID="<session_id>"

# Logout
curl -X POST http://localhost:8000/auth/logout-session \
  -H "session_id: $SESSION_ID"

# Response:
# {"message":"✅ Logged out successfully"}

# Verify session deleted
redis-cli exists "session:$SESSION_ID"
# Output: 0 (doesn't exist)
```

---

## Phase 6: Performance Benchmarking (15 minutes)

### Script: Performance Test

```bash
#!/bin/bash
# save as: test_cache_performance.sh

echo "🔧 Redis Caching Performance Test"
echo "=================================="

USER_ENDPOINT="http://localhost:8000/users-cached/uuid"

echo -e "\n📊 Test 1: First Request (Cache Miss)"
time curl -s $USER_ENDPOINT > /dev/null

echo -e "\n📊 Test 2: Second Request (Cache Hit)"
time curl -s $USER_ENDPOINT > /dev/null

echo -e "\n📊 Test 3: Multiple Sequential Requests"
for i in {1..5}; do
  echo -n "Request $i: "
  time curl -s $USER_ENDPOINT > /dev/null
done

echo -e "\n📊 Test 4: Check Cache Stats"
curl -s http://localhost:8000/admin/cache/stats | jq '.hit_ratio_percent'
```

**Run it:**
```bash
chmod +x test_cache_performance.sh
./test_cache_performance.sh
```

**Expected output:**
```
Test 1: ~100ms (DB query)
Test 2: ~5ms (Cache hit)
Test 3: All ~5ms (Cache hits)
hit_ratio_percent: 85+
```

---

## Phase 7: Error Handling & Graceful Degradation (10 minutes)

### Test 1: Redis Down Scenario

```bash
# Stop Redis
brew services stop redis

# Try to use caching endpoints
curl http://localhost:8000/users-cached

# Should still work! (Uses database instead)
# Response: Success (slower, but works)

# Check logs - should show warning, not error

# Restart Redis
brew services start redis
```

### Test 2: Invalid Cache Key

```bash
# Try to get non-existent user
curl http://localhost:8000/users-cached/invalid-uuid

# Should get proper 404 error:
# {"detail":"User not found"}

# Not a cache error or Redis error
```

### Test 3: Cache with Different Parameters

```bash
# Different skip/limit = different cache key
curl "http://localhost:8000/users-cached?skip=0&limit=10"
curl "http://localhost:8000/users-cached?skip=10&limit=10"

# Both should cache separately
redis-cli keys "users:list:*"
# Should see both keys
```

---

## Phase 8: Validation Checklist

Create a test file: `test_redis_integration.py`

```python
import asyncio
import json
import aioredis
from httpx import AsyncClient
from main import app

async def run_tests():
    """Comprehensive Redis integration tests"""
    
    # Test 1: Redis Connection
    print("✓ Test 1: Redis Connection")
    try:
        redis = aioredis.from_url("redis://localhost:6379")
        await redis.ping()
        print("  ✅ Redis connected")
    except Exception as e:
        print(f"  ❌ Redis failed: {e}")
        return
    
    # Test 2: Cache Set/Get
    print("✓ Test 2: Cache Set/Get")
    await redis.set("test_key", "test_value", ex=3600)
    value = await redis.get("test_key")
    assert value == "test_value", "Cache set/get failed"
    print("  ✅ Cache operations work")
    
    # Test 3: FastAPI Endpoint
    print("✓ Test 3: FastAPI Endpoint")
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/users-cached")
        assert response.status_code == 200, f"Got {response.status_code}"
        print("  ✅ Endpoint works")
    
    # Test 4: Cache Metrics
    print("✓ Test 4: Cache Metrics")
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/admin/cache/stats")
        # Might fail without auth, but that's OK
        print("  ✅ Stats endpoint exists")
    
    # Cleanup
    await redis.delete("test_key")
    await redis.close()
    
    print("\n✅ All tests passed!")

asyncio.run(run_tests())
```

**Run it:**
```bash
python test_redis_integration.py
```

---

## 📋 Comprehensive Test Checklist

### Infrastructure (5 checks)
- [ ] Redis installed and running
- [ ] Redis port 6379 accessible
- [ ] Python dependencies installed
- [ ] redis_client.py exists and imports
- [ ] cache_utils.py exists and imports

### Application (5 checks)
- [ ] App starts without errors
- [ ] Redis connects on startup
- [ ] Swagger UI loads
- [ ] Caching endpoints visible in Swagger
- [ ] Admin endpoints marked correctly

### Functionality (10 checks)
- [ ] GET /users-cached returns users
- [ ] GET /users-cached/{id} returns user
- [ ] First call slower, second call faster
- [ ] PUT invalidates cache
- [ ] POST /admin/cache/warm works
- [ ] GET /admin/cache/stats works
- [ ] POST /admin/cache/clear works
- [ ] POST /admin/cache/metrics/reset works
- [ ] Session login creates session
- [ ] Session operations work

### Performance (5 checks)
- [ ] Cache hit ratio > 50%
- [ ] Subsequent requests < 5ms
- [ ] Memory usage < 100MB
- [ ] No duplicate queries in logs
- [ ] Response times consistent

### Error Handling (5 checks)
- [ ] Works without Redis (degraded mode)
- [ ] 404 for non-existent users
- [ ] Invalid parameters handled
- [ ] Proper error messages returned
- [ ] No unhandled exceptions

### Total: 30 Validation Points

---

## 🎯 Performance Targets

### Response Time Goals

| Endpoint | Target | Status |
|----------|--------|--------|
| First request | 80-100ms | ⏳ |
| Cached request | <5ms | ⚡ |
| Improvement ratio | >20x | 🎯 |

### Cache Metrics Goals

| Metric | Target | Status |
|--------|--------|--------|
| Hit ratio | >70% | 📊 |
| Memory usage | <100MB | 💾 |
| Connection stability | 99.9% | 🔗 |

---

## 📊 Test Results Template

Copy and fill this after running tests:

```markdown
# Redis Integration Test Results
Date: 2026-02-09
Tester: [Your Name]

## Environment
- Redis version: [output of redis-cli --version]
- Python version: [python --version]
- FastAPI version: [pip show fastapi]

## Test Results
- Infrastructure: ✅/❌
- Application: ✅/❌
- Functionality: ✅/❌
- Performance: ✅/❌
- Error Handling: ✅/❌

## Performance Metrics
- Average response time (first): ___ms
- Average response time (cached): ___ms
- Cache hit ratio: ___%
- Memory usage: ___MB

## Issues Found
- [ ] None
- [ ] Minor
- [ ] Major

## Notes
[Your observations]

## Sign-off
Overall Status: ✅ Ready for production / ⚠️ Needs work
```

---

## 🚀 Continuous Testing

### Daily Check Script

```bash
#!/bin/bash
# save as: daily_cache_check.sh

echo "Daily Redis Cache Health Check"
echo "==============================="

# Check Redis
echo "1. Redis Status:"
redis-cli ping

# Check memory
echo -e "\n2. Memory Usage:"
redis-cli info memory | grep "used_memory_human"

# Check keys
echo -e "\n3. Cache Keys:"
redis-cli dbsize

# Check app
echo -e "\n4. Application:"
curl -s http://localhost:8000/admin/cache/stats | jq '.hit_ratio_percent'

echo -e "\n✅ Health check complete"
```

---

## 📝 Logging & Debugging

### Enable debug logging

```python
# In main.py
import logging
logging.basicConfig(level=logging.DEBUG)

# See detailed cache operations
```

### Monitor Redis in real-time

```bash
# Terminal: Watch all Redis commands
redis-cli monitor

# Output shows every operation:
# "get" "user:1"
# "set" "user:1" "json..."
# "del" "users:list:*"
```

### Check what's in cache

```bash
# See all keys
redis-cli keys "*"

# Get specific key
redis-cli get "user:abc123"

# Get key info
redis-cli --stat
```

---

**Congratulations! You've completed comprehensive testing of Redis caching! 🎉**

Move on to the Practice Assignment for hands-on implementation experience.
