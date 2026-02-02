# RBAC Visual Guide

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     FastAPI Application                       │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Authentication Layer                     │   │
│  │  (OAuth2 + JWT Tokens)                               │   │
│  └──────────────────────────────────────────────────────┘   │
│                          ↓                                    │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Authorization Layer                      │   │
│  │  (RBAC - Role & Permission Checks)                   │   │
│  └──────────────────────────────────────────────────────┘   │
│                          ↓                                    │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Protected Endpoints                      │   │
│  │  (Business Logic)                                     │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## Request Flow

```
Client Request
    ↓
[1] Extract JWT Token from Header
    ↓
[2] Verify Token Signature
    ↓
[3] Decode User ID from Token
    ↓
[4] Fetch User from Database
    ↓
[5] Check User is Active
    ↓
[6] Check User Role/Permission
    ↓
    ├─ ✅ Authorized → Execute Endpoint
    └─ ❌ Unauthorized → Return 403 Forbidden
```

---

## Role Hierarchy

```
        ┌─────────────┐
        │    ADMIN    │  Level 4
        │  (All Access)│
        └──────┬──────┘
               │ inherits all from below
        ┌──────▼──────┐
        │   MANAGER   │  Level 3
        │(Manage Users)│
        └──────┬──────┘
               │ inherits all from below
        ┌──────▼──────┐
        │    USER     │  Level 2
        │ (Own Data)  │
        └──────┬──────┘
               │ inherits all from below
        ┌──────▼──────┐
        │    GUEST    │  Level 1
        │ (Read Only) │
        └─────────────┘
```

---

## Permission Flow

```
┌──────────────┐
│ User Request │
└──────┬───────┘
       │
       ▼
┌──────────────────┐
│ Check User Role  │
└──────┬───────────┘
       │
       ▼
┌─────────────────────────┐
│ Get Role Permissions    │
│ from ROLE_PERMISSIONS   │
└──────┬──────────────────┘
       │
       ▼
┌──────────────────────────┐
│ Required Permission in   │
│ User's Permission List?  │
└──────┬─────────┬─────────┘
       │         │
      YES       NO
       │         │
       ▼         ▼
   ✅ Allow  ❌ Deny (403)
```

---

## Endpoint Protection Patterns

### Pattern 1: Role-Based (Simple)

```
@app.get("/admin/users")
def list_users(
    current_user: User = Depends(require_admin)
):
    ...
```

```
Request → require_admin()
              ↓
         Check role == ADMIN?
              ↓
         YES → Continue
         NO  → 403 Forbidden
```

### Pattern 2: Multiple Roles

```
@app.get("/reports")
def get_reports(
    current_user: User = Depends(
        require_role([UserRole.ADMIN, UserRole.MANAGER])
    )
):
    ...
```

```
Request → require_role([ADMIN, MANAGER])
              ↓
         User role in [ADMIN, MANAGER]?
              ↓
         YES → Continue
         NO  → 403 Forbidden
```

### Pattern 3: Permission-Based

```
@app.delete("/users/{id}")
def delete_user(
    current_user: User = Depends(
        require_permission(Permission.DELETE_USERS)
    )
):
    ...
```

```
Request → require_permission(DELETE_USERS)
              ↓
         Get user's role permissions
              ↓
         DELETE_USERS in permissions?
              ↓
         YES → Continue
         NO  → 403 Forbidden
```

### Pattern 4: Resource Ownership

```
@app.get("/users/{user_id}/profile")
def get_profile(
    user_id: UUID,
    current_user: User = Depends(get_current_active_user)
):
    if current_user.role in [ADMIN, MANAGER]:
        # Can access any profile
        return fetch_any_profile(user_id)
    elif current_user.id == user_id:
        # Can only access own profile
        return current_user
    else:
        raise HTTPException(403, "Access denied")
```

```
Request → Check Role
              ↓
         ┌────┴────┐
         │         │
      ADMIN/   Regular User
      MANAGER      │
         │         │
      Access    Check if
      Any       user_id ==
      Profile   current_user.id
         │         │
         │     ┌───┴───┐
         │    YES     NO
         │     │       │
         ▼     ▼       ▼
      ✅ Allow  ❌ Deny
```

---

## Permission Matrix Visual

```
┌──────────────────────────────────────────────────────────────┐
│                    PERMISSION MATRIX                          │
├────────────────┬──────┬──────┬─────────┬────────────────────┤
│   Permission   │Guest │ User │ Manager │       Admin        │
├────────────────┼──────┼──────┼─────────┼────────────────────┤
│ read:products  │  ✅  │  ✅  │   ✅    │        ✅          │
│ read:reports   │  ❌  │  ✅  │   ✅    │        ✅          │
│ read:users     │  ❌  │  ❌  │   ✅    │        ✅          │
│ create:products│  ❌  │  ❌  │   ✅    │        ✅          │
│ update:products│  ❌  │  ❌  │   ✅    │        ✅          │
│ update:users   │  ❌  │  ❌  │   ✅    │        ✅          │
│ export:data    │  ❌  │  ❌  │   ✅    │        ✅          │
│ create:users   │  ❌  │  ❌  │   ❌    │        ✅          │
│ delete:users   │  ❌  │  ❌  │   ❌    │        ✅          │
│ delete:products│  ❌  │  ❌  │   ❌    │        ✅          │
│ manage:roles   │  ❌  │  ❌  │   ❌    │        ✅          │
└────────────────┴──────┴──────┴─────────┴────────────────────┘
```

---

## User Journey: Admin Deletes User

```
Step 1: Admin Login
┌─────────────┐
│ POST /token │
│ username    │
│ password    │
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│ Authenticate User   │
│ Check credentials   │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ Create JWT Token    │
│ Include user_id     │
│ Include role: admin │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ Return Token        │
│ {access_token: ...} │
└─────────────────────┘

Step 2: Delete User Request
┌──────────────────────────┐
│ DELETE /admin/users/{id} │
│ Authorization: Bearer... │
└──────┬───────────────────┘
       │
       ▼
┌─────────────────────────────┐
│ Extract Token from Header   │
└──────┬──────────────────────┘
       │
       ▼
┌─────────────────────────────┐
│ Verify Token Signature      │
└──────┬──────────────────────┘
       │
       ▼
┌─────────────────────────────┐
│ Decode User ID from Token   │
└──────┬──────────────────────┘
       │
       ▼
┌─────────────────────────────┐
│ Fetch User from Database    │
└──────┬──────────────────────┘
       │
       ▼
┌─────────────────────────────┐
│ Check User is Active        │
└──────┬──────────────────────┘
       │
       ▼
┌──────────────────────────────────┐
│ require_permission(DELETE_USERS) │
└──────┬───────────────────────────┘
       │
       ▼
┌─────────────────────────────┐
│ Get User's Role Permissions │
│ Role: ADMIN                 │
└──────┬──────────────────────┘
       │
       ▼
┌─────────────────────────────────┐
│ Check DELETE_USERS in list     │
│ Admin has all permissions       │
└──────┬──────────────────────────┘
       │
       ▼
┌─────────────────────────────┐
│ ✅ Permission Granted        │
└──────┬──────────────────────┘
       │
       ▼
┌─────────────────────────────┐
│ Execute Endpoint Logic      │
│ - Find user by ID           │
│ - Prevent self-deletion     │
│ - Delete user from DB       │
│ - Log action                │
└──────┬──────────────────────┘
       │
       ▼
┌─────────────────────────────┐
│ Return Success Response     │
└─────────────────────────────┘
```

---

## User Journey: Regular User Tries to Delete User

```
Step 1: User Login
┌─────────────┐
│ POST /token │
│ username    │
│ password    │
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│ Create JWT Token    │
│ Include role: user  │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ Return Token        │
└─────────────────────┘

Step 2: Delete User Request (Unauthorized)
┌──────────────────────────┐
│ DELETE /admin/users/{id} │
│ Authorization: Bearer... │
└──────┬───────────────────┘
       │
       ▼
┌─────────────────────────────┐
│ Extract & Verify Token      │
└──────┬──────────────────────┘
       │
       ▼
┌─────────────────────────────┐
│ Fetch User from Database    │
│ Role: USER                  │
└──────┬──────────────────────┘
       │
       ▼
┌──────────────────────────────────┐
│ require_permission(DELETE_USERS) │
└──────┬───────────────────────────┘
       │
       ▼
┌─────────────────────────────┐
│ Get User's Role Permissions │
│ Role: USER                  │
│ Permissions: [              │
│   - read:products           │
│   - read:reports            │
│ ]                           │
└──────┬──────────────────────┘
       │
       ▼
┌─────────────────────────────────┐
│ Check DELETE_USERS in list     │
│ ❌ NOT FOUND                    │
└──────┬──────────────────────────┘
       │
       ▼
┌─────────────────────────────┐
│ ❌ Permission Denied         │
└──────┬──────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│ Raise HTTPException                 │
│ Status: 403 FORBIDDEN               │
│ Detail: "Permission denied.         │
│          Required: delete:users"    │
└─────────────────────────────────────┘
```

---

## Database Schema

```
┌────────────────────────────────────────┐
│              USERS TABLE               │
├─────────────┬───────────────┬──────────┤
│  Column     │     Type      │ Nullable │
├─────────────┼───────────────┼──────────┤
│ id          │ UUID          │    NO    │ 🔑 Primary Key
│ email       │ VARCHAR(100)  │    NO    │ 🔒 Unique
│ hashed_pw   │ VARCHAR(100)  │    NO    │
│ full_name   │ VARCHAR(100)  │   YES    │
│ phone       │ VARCHAR(15)   │   YES    │
│ role        │ ENUM(...)     │    NO    │ ⭐ NEW!
│ is_active   │ BOOLEAN       │    NO    │
│ address     │ VARCHAR(200)  │   YES    │
│ created_at  │ TIMESTAMP     │    NO    │
│ updated_at  │ TIMESTAMP     │    NO    │
└─────────────┴───────────────┴──────────┘

ENUM UserRole:
  - admin
  - manager
  - user
  - guest

Default: 'user'
```

---

## Code Structure

```
sql_app/
├── models.py
│   ├── UserRole Enum ⭐
│   └── User Model (with role field) ⭐
│
├── auth.py
│   ├── OAuth2 Functions (existing)
│   ├── Permission Enum ⭐
│   ├── ROLE_PERMISSIONS Mapping ⭐
│   ├── has_permission() ⭐
│   ├── require_admin() ⭐
│   ├── require_manager_or_admin() ⭐
│   ├── require_role() ⭐
│   └── require_permission() ⭐
│
├── schemas.py
│   ├── UserCreate (with role) ⭐
│   └── UserResponse (with role) ⭐
│
├── main.py
│   ├── Registration (role support) ⭐
│   └── RBAC Endpoints ⭐
│       ├── GET /admin/users
│       ├── DELETE /admin/users/{id}
│       ├── POST /admin/users/{id}/activate
│       ├── POST /admin/users/{id}/deactivate
│       ├── PUT /admin/users/{id}/role
│       ├── GET /reports/user-statistics
│       ├── GET /my-profile
│       ├── GET /users/{id}/profile
│       ├── GET /permissions/check
│       └── POST /admin/create-admin
│
└── alembic/versions/
    └── 803697d6f77b_add_role_to_users.py ⭐

⭐ = New or Modified for RBAC
```

---

## Decision Tree: Endpoint Access

```
                      User Makes Request
                             │
                             ▼
                    Has Valid JWT Token?
                             │
                    ┌────────┴────────┐
                   NO                YES
                    │                 │
                    ▼                 ▼
              401 Unauthorized   Decode Token
                                      │
                                      ▼
                                 User Active?
                                      │
                              ┌───────┴───────┐
                             NO              YES
                              │               │
                              ▼               ▼
                      400 Inactive     Check Required Role
                                              │
                                   ┌──────────┼──────────┐
                                   │          │          │
                              No Role    Specific   Permission
                              Check       Role       Required
                                   │          │          │
                                   ▼          ▼          ▼
                               ✅ Allow  Has Role?  Has Permission?
                                          │          │
                                   ┌──────┴───┐  ┌───┴───┐
                                  YES        NO YES     NO
                                   │          │  │       │
                                   ▼          ▼  ▼       ▼
                               ✅ Allow  ❌ 403  ✅ Allow ❌ 403
```

---

## Testing Flow

```
1. CREATE TEST USERS
   ├── Guest User
   ├── Regular User
   ├── Manager User
   └── Admin User

2. LOGIN EACH USER
   ├── Get access_token for guest
   ├── Get access_token for user
   ├── Get access_token for manager
   └── Get access_token for admin

3. TEST ENDPOINTS
   ├── Test /my-profile (all should work)
   ├── Test /permissions/check (all should work)
   ├── Test /admin/users (only admin works)
   ├── Test /reports/user-statistics (manager+ works)
   ├── Test DELETE /admin/users/{id} (only admin works)
   └── Test /users/{id}/profile (ownership rules apply)

4. VERIFY RESULTS
   ├── ✅ Expected 200 responses
   ├── ❌ Expected 403 responses
   └── 📊 Verify returned data
```

---

## Error Responses

### 401 Unauthorized

```json
{
  "detail": "Could not validate credentials"
}
```

**When**: No token, invalid token, expired token

### 403 Forbidden (Role-based)

```json
{
  "detail": "Admin access required"
}
```

**When**: User doesn't have required role

### 403 Forbidden (Permission-based)

```json
{
  "detail": "Permission denied. Required: delete:users"
}
```

**When**: User's role doesn't have required permission

### 403 Forbidden (Resource-based)

```json
{
  "detail": "You can only access your own profile"
}
```

**When**: User trying to access resource they don't own

---

## Summary

```
┌────────────────────────────────────────────────────────┐
│              RBAC IMPLEMENTATION COMPLETE               │
├────────────────────────────────────────────────────────┤
│                                                         │
│  ✅ 4 User Roles: Guest, User, Manager, Admin          │
│  ✅ 12 Permissions across 4 categories                 │
│  ✅ 11 New Protected Endpoints                         │
│  ✅ 3 Protection Patterns: Role, Permission, Resource  │
│  ✅ Database Migration Ready                           │
│  ✅ Complete Documentation                             │
│  ✅ Testing Guide Included                             │
│  ✅ Practice Assignment Provided                       │
│                                                         │
│           Ready for Production Use! 🚀                 │
└────────────────────────────────────────────────────────┘
```
