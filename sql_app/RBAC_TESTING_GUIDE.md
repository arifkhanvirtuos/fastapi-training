# RBAC Testing Guide

## Quick Start Testing Guide for Role-Based Access Control

### 1. Run the Migration

First, apply the database migration to add the role column:

```bash
cd /Users/virtuosdigital/Arif/fastapilearning/sql_app
# Using your virtual environment
/Users/virtuosdigital/Arif/fastapilearning/venv/bin/python -m alembic upgrade head
```

### 2. Start the Server

```bash
cd /Users/virtuosdigital/Arif/fastapilearning/sql_app
/Users/virtuosdigital/Arif/fastapilearning/venv/bin/python -m uvicorn main:app --reload
```

Open your browser: `http://localhost:8000/docs`

---

## Test Scenarios

### Scenario 1: Create Users with Different Roles

#### 1.1 Create a Regular User
```bash
curl -X POST "http://localhost:8000/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "userpass123",
    "full_name": "Regular User",
    "role": "user"
  }'
```

#### 1.2 Create a Manager
```bash
curl -X POST "http://localhost:8000/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "manager@example.com",
    "password": "managerpass123",
    "full_name": "Manager User",
    "role": "manager"
  }'
```

#### 1.3 Create an Admin
```bash
curl -X POST "http://localhost:8000/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "adminpass123",
    "full_name": "Admin User",
    "role": "admin"
  }'
```

#### 1.4 Create a Guest
```bash
curl -X POST "http://localhost:8000/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "guest@example.com",
    "password": "guestpass123",
    "full_name": "Guest User",
    "role": "guest"
  }'
```

---

### Scenario 2: Login and Get Tokens

#### 2.1 Login as Regular User
```bash
curl -X POST "http://localhost:8000/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=userpass123"
```

**Save the access_token from the response!**

#### 2.2 Login as Manager
```bash
curl -X POST "http://localhost:8000/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=manager@example.com&password=managerpass123"
```

#### 2.3 Login as Admin
```bash
curl -X POST "http://localhost:8000/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=adminpass123"
```

---

### Scenario 3: Test Role-Based Access

Replace `<TOKEN>` with the actual token you received from login.

#### 3.1 Test Regular User Access

**✅ Should work - View own profile:**
```bash
curl -X GET "http://localhost:8000/my-profile" \
  -H "Authorization: Bearer <USER_TOKEN>"
```

**✅ Should work - Check permissions:**
```bash
curl -X GET "http://localhost:8000/permissions/check" \
  -H "Authorization: Bearer <USER_TOKEN>"
```

**❌ Should fail (403 Forbidden) - List all users:**
```bash
curl -X GET "http://localhost:8000/admin/users" \
  -H "Authorization: Bearer <USER_TOKEN>"
```

**Expected response:**
```json
{
  "detail": "Admin access required"
}
```

#### 3.2 Test Manager Access

**✅ Should work - View user statistics:**
```bash
curl -X GET "http://localhost:8000/reports/user-statistics" \
  -H "Authorization: Bearer <MANAGER_TOKEN>"
```

**✅ Should work - Activate a user:**
```bash
curl -X POST "http://localhost:8000/admin/users/<USER_ID>/activate" \
  -H "Authorization: Bearer <MANAGER_TOKEN>"
```

**❌ Should fail (403 Forbidden) - Delete user:**
```bash
curl -X DELETE "http://localhost:8000/admin/users/<USER_ID>" \
  -H "Authorization: Bearer <MANAGER_TOKEN>"
```

**Expected response:**
```json
{
  "detail": "Permission denied. Required: delete:users"
}
```

#### 3.3 Test Admin Access

**✅ Should work - List all users:**
```bash
curl -X GET "http://localhost:8000/admin/users" \
  -H "Authorization: Bearer <ADMIN_TOKEN>"
```

**✅ Should work - Delete a user:**
```bash
curl -X DELETE "http://localhost:8000/admin/users/<USER_ID>" \
  -H "Authorization: Bearer <ADMIN_TOKEN>"
```

**✅ Should work - Change user role:**
```bash
curl -X PUT "http://localhost:8000/admin/users/<USER_ID>/role?new_role=manager" \
  -H "Authorization: Bearer <ADMIN_TOKEN>"
```

**✅ Should work - Create new admin:**
```bash
curl -X POST "http://localhost:8000/admin/create-admin" \
  -H "Authorization: Bearer <ADMIN_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newadmin@example.com",
    "password": "newadminpass123",
    "full_name": "New Admin"
  }'
```

---

### Scenario 4: Cross-User Access Tests

#### 4.1 User Tries to Access Another User's Profile

**Get two user IDs first, then:**

**❌ User A tries to view User B's profile (should fail):**
```bash
curl -X GET "http://localhost:8000/users/<USER_B_ID>/profile" \
  -H "Authorization: Bearer <USER_A_TOKEN>"
```

**Expected response:**
```json
{
  "detail": "You can only access your own profile"
}
```

#### 4.2 Admin Can Access Any Profile

**✅ Admin views any user's profile (should work):**
```bash
curl -X GET "http://localhost:8000/users/<ANY_USER_ID>/profile" \
  -H "Authorization: Bearer <ADMIN_TOKEN>"
```

---

## Testing in Swagger UI

### Using the Interactive Docs

1. Go to `http://localhost:8000/docs`

2. **Authenticate:**
   - Click the **"Authorize"** button (lock icon) at the top
   - Enter username: `admin@example.com`
   - Enter password: `adminpass123`
   - Click "Authorize"

3. **Test Protected Endpoints:**
   - Try the `/admin/users` endpoint - should work ✅
   - Logout and login as `user@example.com`
   - Try the `/admin/users` endpoint again - should fail ❌

---

## Permission Matrix

| Endpoint | Guest | User | Manager | Admin |
|----------|-------|------|---------|-------|
| GET /my-profile | ✅ | ✅ | ✅ | ✅ |
| GET /permissions/check | ✅ | ✅ | ✅ | ✅ |
| GET /users/{id}/profile (own) | ✅ | ✅ | ✅ | ✅ |
| GET /users/{id}/profile (other) | ❌ | ❌ | ✅ | ✅ |
| GET /admin/users | ❌ | ❌ | ❌ | ✅ |
| GET /reports/user-statistics | ❌ | ❌ | ✅ | ✅ |
| POST /admin/users/{id}/activate | ❌ | ❌ | ✅ | ✅ |
| POST /admin/users/{id}/deactivate | ❌ | ❌ | ✅ | ✅ |
| PUT /admin/users/{id}/role | ❌ | ❌ | ❌ | ✅ |
| DELETE /admin/users/{id} | ❌ | ❌ | ❌ | ✅ |
| POST /admin/create-admin | ❌ | ❌ | ❌ | ✅ |

---

## Expected Errors

### 401 Unauthorized
```json
{
  "detail": "Could not validate credentials"
}
```
**Cause:** No token provided or invalid token

### 403 Forbidden
```json
{
  "detail": "Admin access required"
}
```
**Cause:** User doesn't have required role

```json
{
  "detail": "Permission denied. Required: delete:users"
}
```
**Cause:** User doesn't have required permission

---

## Verification Checklist

- [ ] Migration ran successfully
- [ ] Server starts without errors
- [ ] Can create users with different roles
- [ ] Can login and receive tokens
- [ ] Admin can access all endpoints
- [ ] Manager can access manager/admin endpoints
- [ ] User cannot access admin endpoints
- [ ] User can only view own profile
- [ ] Admin can change user roles
- [ ] Proper error messages for unauthorized access

---

## Troubleshooting

### Issue: "Column 'role' does not exist"
**Solution:** Run the migration:
```bash
/Users/virtuosdigital/Arif/fastapilearning/venv/bin/python -m alembic upgrade head
```

### Issue: All roles work the same
**Solution:** Check that you're using the correct token for each user

### Issue: Import errors
**Solution:** Make sure all imports are correct in models.py, auth.py, schemas.py

---

## Next Steps

After testing the basic RBAC implementation:

1. ✅ Complete the **Practice Assignment** in the RBAC_AUTHORIZATION_GUIDE.md
2. Add audit logging for sensitive operations
3. Implement email notifications for role changes
4. Add more fine-grained permissions
5. Create custom role combinations
6. Implement resource-based access control (e.g., users can edit their own posts)

---

## Notes

- The first admin must be created manually or through the registration endpoint
- In production, consider:
  - Creating the first admin via environment variables
  - Requiring email verification before activation
  - Adding rate limiting to sensitive endpoints
  - Implementing audit logs for all admin actions
  - Using more complex password requirements
  - Adding two-factor authentication for admin accounts
