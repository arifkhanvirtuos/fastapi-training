# OAuth2 Password Bearer Authentication in FastAPI

## Duration: 1 Hour

## Topics Covered

- OAuth2PasswordBearer
- OAuth2PasswordRequestForm
- FastAPI security utilities
- Token endpoint standards
- Integration with Swagger UI

## Key Takeaways

Learn how to implement OAuth2-compliant authentication in FastAPI that seamlessly integrates with Swagger UI's "Authorize" button and follows industry standards.

---

## Table of Contents

1. [Introduction to OAuth2](#introduction-to-oauth2)
2. [Architecture Overview](#architecture-overview)
3. [Implementation Guide](#implementation-guide)
4. [OAuth2 Components](#oauth2-components)
5. [Swagger UI Integration](#swagger-ui-integration)
6. [Testing the API](#testing-the-api)
7. [Security Best Practices](#security-best-practices)
8. [Practice Assignment](#practice-assignment)

---

## Introduction to OAuth2

OAuth2 is an industry-standard authorization protocol that provides secure delegated access. The **Password Flow** (also called Resource Owner Password Credentials) is one of several OAuth2 grant types.

### Why OAuth2 with FastAPI?

1. **Industry Standard**: OAuth2 is widely recognized and understood
2. **Automatic Swagger Integration**: FastAPI's Swagger UI automatically provides an "Authorize" button
3. **Security**: Built-in token-based authentication with proper HTTP status codes
4. **Flexibility**: Easy to extend for additional security layers

---

## Architecture Overview

```
┌─────────────┐      1. POST /register        ┌──────────────┐
│             │ ──────────────────────────────>│              │
│   Client    │                                │   FastAPI    │
│   (Browser/ │      2. POST /token           │   Server     │
│    App)     │ ──────────────────────────────>│              │
│             │    (OAuth2PasswordRequestForm) │              │
│             │                                └──────────────┘
│             │<─────────────────────────────┐        │
│             │  access_token + refresh_token         │
│             │                                        │
│             │      3. GET /users/me                 │
│             │    Authorization: Bearer <token>      │
│             │ ──────────────────────────────>       │
│             │                                        │
│             │<─────────────────────────────┐        │
│             │      User data                        │
└─────────────┘                                       │
                                                      │
                                            ┌─────────▼────────┐
                                            │                  │
                                            │   PostgreSQL     │
                                            │   Database       │
                                            │                  │
                                            └──────────────────┘
```

---

## Implementation Guide

### File Structure

```
sql_app/
├── main.py              # FastAPI app with endpoints
├── auth.py              # OAuth2 authentication utilities
├── schemas.py           # Pydantic models
├── models.py            # SQLAlchemy models
├── database.py          # Database configuration
└── requirements.txt     # Dependencies
```

### Step 1: Install Dependencies

```bash
cd sql_app
pip install -r requirements.txt
```

**Required packages** (added to requirements.txt):

- `python-jose[cryptography]` - JWT token creation/validation
- `passlib[bcrypt]` - Password hashing
- `python-multipart` - Form data parsing (required for OAuth2PasswordRequestForm)

### Step 2: Understanding the Components

#### **auth.py** - OAuth2 Utilities

```python
from fastapi.security import OAuth2PasswordBearer

# This tells FastAPI where the token endpoint is
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
```

**Key Functions:**

1. **Password Hashing**

   ```python
   pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

   def get_password_hash(password: str) -> str:
       return pwd_context.hash(password)

   def verify_password(plain_password: str, hashed_password: str) -> bool:
       return pwd_context.verify(plain_password, hashed_password)
   ```

2. **Token Creation**

   ```python
   def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
       to_encode = data.copy()
       expire = datetime.now(timezone.utc) + timedelta(minutes=30)
       to_encode.update({"exp": expire, "type": "access"})
       return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
   ```

3. **User Authentication**
   ```python
   async def get_current_user(
       token: str = Depends(oauth2_scheme),  # Automatically extracts token
       db: Session = Depends(get_db)
   ) -> User:
       # Validates token and returns user
   ```

#### **schemas.py** - Pydantic Models

```python
class Token(BaseModel):
    """OAuth2 standard token response"""
    access_token: str
    token_type: str
    refresh_token: Optional[str] = None

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
```

#### **main.py** - OAuth2 Endpoints

---

## OAuth2 Components

### 1. OAuth2PasswordBearer

```python
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
```

**What it does:**

- Automatically extracts the token from the `Authorization: Bearer <token>` header
- Provides the "Authorize" button in Swagger UI
- Points to the `/token` endpoint for authentication

**Usage in endpoints:**

```python
async def protected_endpoint(token: str = Depends(oauth2_scheme)):
    # token is automatically extracted from Authorization header
    pass
```

### 2. OAuth2PasswordRequestForm

```python
from fastapi.security import OAuth2PasswordRequestForm

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # form_data.username - email in our case
    # form_data.password - password
    # form_data.scope - optional scopes
```

**Important:** OAuth2 standard uses `username` field, but you can use it for email!

**Form fields:**

- `username` (string) - Use this for email
- `password` (string) - User's password
- `scope` (string) - Optional space-separated scopes
- `grant_type` (string) - Should be "password"
- `client_id` (string) - Optional
- `client_secret` (string) - Optional

### 3. Token Endpoint

```python
@app.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    # 1. Authenticate user
    user = authenticate_user(db, form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 2. Create tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    # 3. Return OAuth2 compliant response
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": refresh_token
    }
```

**Why this format?**

- `access_token`: The JWT token for API access
- `token_type`: Must be "bearer" (lowercase) per OAuth2 spec
- `refresh_token`: Optional, for getting new access tokens

### 4. Protected Endpoints

```python
@app.get("/users/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user
```

**Dependency chain:**

1. `oauth2_scheme` extracts token from Authorization header
2. `get_current_user` validates token and fetches user from database
3. `get_current_active_user` checks if user is active
4. Your endpoint receives the authenticated user

---

## Swagger UI Integration

### How the "Authorize" Button Works

1. **Configuration in OAuth2PasswordBearer**

   ```python
   oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
   ```

   The `tokenUrl` parameter tells Swagger where to send login credentials.

2. **User Experience:**
   - User clicks "Authorize" button (🔒 icon)
   - Modal appears asking for username and password
   - Credentials are sent to `/token` endpoint
   - Token is stored and automatically added to all subsequent requests

3. **Authorization Header:**
   ```
   Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   ```

### Testing with Swagger UI

1. **Start the server:**

   ```bash
   cd sql_app
   uvicorn main:app --reload
   ```

2. **Open Swagger UI:**

   ```
   http://localhost:8000/docs
   ```

3. **Register a user:**
   - Find `POST /register` endpoint
   - Click "Try it out"
   - Enter user details:
     ```json
     {
       "email": "test@example.com",
       "password": "testpassword123",
       "full_name": "Test User"
     }
     ```
   - Click "Execute"

4. **Login (Authorize):**
   - Click the "Authorize" button at the top right
   - Username: `test@example.com` (use email)
   - Password: `testpassword123`
   - Click "Authorize"
   - Close the modal

5. **Access protected endpoints:**
   - Find `GET /users/me`
   - Click "Try it out" → "Execute"
   - You should see your user data!

---

## Testing the API

### Using cURL

#### 1. Register a user

```bash
curl -X POST "http://localhost:8000/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "securepass123",
    "full_name": "John Doe",
    "phone_number": "+1234567890"
  }'
```

**Response:**

```json
{
  "message": "User registered successfully. User ID: 550e8400-e29b-41d4-a716-446655440000"
}
```

#### 2. Login (Get Token)

```bash
curl -X POST "http://localhost:8000/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=john@example.com&password=securepass123"
```

**Response:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1NTBlODQwMC1lMjliLTQxZDQtYTcxNi00NDY2NTU0NDAwMDAiLCJleHAiOjE3MDYxMjM0NTYsInR5cGUiOiJhY2Nlc3MifQ.signature",
  "token_type": "bearer",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1NTBlODQwMC1lMjliLTQxZDQtYTcxNi00NDY2NTU0NDAwMDAiLCJleHAiOjE3MDY3MjgyNTYsInR5cGUiOiJyZWZyZXNoIn0.signature"
}
```

#### 3. Access Protected Endpoint

```bash
curl -X GET "http://localhost:8000/users/me" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**Response:**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "john@example.com",
  "full_name": "John Doe",
  "phone_number": "+1234567890",
  "is_active": true
}
```

#### 4. Refresh Token

```bash
curl -X POST "http://localhost:8000/refresh" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }'
```

**Response:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.new_token...",
  "token_type": "bearer"
}
```

### Using Python Requests

```python
import requests

BASE_URL = "http://localhost:8000"

# 1. Register
response = requests.post(
    f"{BASE_URL}/register",
    json={
        "email": "alice@example.com",
        "password": "alicepass123",
        "full_name": "Alice Smith"
    }
)
print(response.json())

# 2. Login
response = requests.post(
    f"{BASE_URL}/token",
    data={
        "username": "alice@example.com",
        "password": "alicepass123"
    }
)
tokens = response.json()
access_token = tokens["access_token"]

# 3. Access protected endpoint
headers = {"Authorization": f"Bearer {access_token}"}
response = requests.get(f"{BASE_URL}/users/me", headers=headers)
print(response.json())

# 4. Update user
response = requests.put(
    f"{BASE_URL}/users/me",
    headers=headers,
    json={"full_name": "Alice Johnson"}
)
print(response.json())
```

---

## Security Best Practices

### 1. Secret Key Management

**❌ Bad:**

```python
SECRET_KEY = "my-secret-key"  # Hardcoded in source code
```

**✅ Good:**

```python
import os
from dotenv import load_dotenv

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable is not set")
```

**Create .env file:**

```bash
SECRET_KEY=your-super-secret-key-change-this-in-production
DATABASE_URL=postgresql://user:pass@localhost/dbname
```

### 2. Token Expiration

```python
# Short-lived access tokens
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # 30 minutes

# Longer-lived refresh tokens
REFRESH_TOKEN_EXPIRE_DAYS = 7  # 7 days
```

**Why?**

- Access tokens are used frequently → shorter expiration reduces risk
- Refresh tokens are used rarely → can have longer expiration

### 3. Password Requirements

```python
from pydantic import validator, BaseModel

class UserCreate(BaseModel):
    email: EmailStr
    password: str

    @validator('password')
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain uppercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain digit')
        return v
```

### 4. HTTPS in Production

**Always use HTTPS in production:**

- Tokens are sent in Authorization header
- Without HTTPS, tokens can be intercepted
- Use Let's Encrypt for free SSL certificates

### 5. Rate Limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/token")
@limiter.limit("5/minute")  # Max 5 login attempts per minute
async def login_for_access_token(...):
    ...
```

### 6. Token Blacklisting (Optional)

For logout functionality, maintain a blacklist of revoked tokens:

```python
# In-memory (for demo) - use Redis in production
revoked_tokens = set()

def revoke_token(token: str):
    revoked_tokens.add(token)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    if token in revoked_tokens:
        raise HTTPException(status_code=401, detail="Token has been revoked")
    # ... rest of validation
```

---

## Practice Assignment

### Convert Existing Auth to OAuth2 Standard

**Objective:** Take a non-OAuth2 authentication system and convert it to use OAuth2PasswordBearer and OAuth2PasswordRequestForm.

#### Requirements:

1. **Create New Files:**
   - [ ] `auth.py` with OAuth2 utilities
   - [ ] `schemas.py` with Pydantic models
   - [ ] `.env` file with SECRET_KEY

2. **Implement Endpoints:**
   - [ ] `POST /register` - User registration
   - [ ] `POST /token` - OAuth2 token endpoint
   - [ ] `POST /refresh` - Refresh access token
   - [ ] `GET /users/me` - Get current user
   - [ ] `PUT /users/me` - Update current user
   - [ ] `GET /protected/data` - Example protected endpoint

3. **Security Features:**
   - [ ] Password hashing with bcrypt
   - [ ] JWT token creation with expiration
   - [ ] Token validation and user extraction
   - [ ] Active user check
   - [ ] Proper HTTP status codes (401, 403, etc.)

4. **Testing:**
   - [ ] Register 3 different users
   - [ ] Login with each user via Swagger UI
   - [ ] Access protected endpoints
   - [ ] Try accessing without token (should get 401)
   - [ ] Try with invalid token (should get 401)
   - [ ] Refresh token before expiration
   - [ ] Update user information

5. **Bonus Challenges:**
   - [ ] Add password strength validation
   - [ ] Implement rate limiting on /token endpoint
   - [ ] Add logout functionality with token blacklist
   - [ ] Create admin-only endpoints with role-based access
   - [ ] Add email verification flow
   - [ ] Implement "forgot password" functionality

#### Evaluation Criteria:

| Criteria                               | Points  |
| -------------------------------------- | ------- |
| OAuth2PasswordBearer integration       | 20      |
| OAuth2PasswordRequestForm usage        | 15      |
| Proper token creation/validation       | 20      |
| Password hashing                       | 10      |
| Swagger UI "Authorize" button works    | 15      |
| Protected endpoints function correctly | 15      |
| Error handling (401, 403)              | 5       |
| **Total**                              | **100** |

---

## Common Issues and Solutions

### Issue 1: "Not authenticated" error in Swagger

**Symptoms:**

```json
{
  "detail": "Not authenticated"
}
```

**Solutions:**

1. Make sure you clicked "Authorize" button
2. Check that tokenUrl matches your endpoint
3. Verify token is being sent: Check browser DevTools → Network → Headers

### Issue 2: OAuth2PasswordRequestForm not working

**Error:**

```
ImportError: cannot import name 'OAuth2PasswordRequestForm'
```

**Solution:**

```bash
pip install python-multipart
```

### Issue 3: Token validation fails

**Error:**

```json
{
  "detail": "Could not validate credentials"
}
```

**Check:**

1. SECRET_KEY matches between token creation and validation
2. Token hasn't expired (check `exp` claim)
3. Token structure is correct (should have 3 parts separated by dots)

### Issue 4: Password hashing error

**Error:**

```
ValueError: Invalid salt
```

**Solution:**

```bash
pip install passlib[bcrypt]
```

---

## Additional Resources

### Official Documentation

- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [OAuth2 with Password (and hashing), Bearer with JWT tokens](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/)
- [OAuth2 RFC Specification](https://tools.ietf.org/html/rfc6749)

### Libraries

- [python-jose](https://python-jose.readthedocs.io/) - JWT implementation
- [passlib](https://passlib.readthedocs.io/) - Password hashing
- [FastAPI Security Utilities](https://fastapi.tiangolo.com/tutorial/security/first-steps/)

### Video Tutorials

- FastAPI Official Tutorial on YouTube
- OAuth2 Explained (by OktaDev)

---

## Summary

### What You Learned

1. **OAuth2PasswordBearer**: Automatic token extraction and Swagger integration
2. **OAuth2PasswordRequestForm**: Standard form for login credentials
3. **Token endpoint**: Creating OAuth2-compliant authentication
4. **Protected endpoints**: Using dependencies to secure routes
5. **Swagger UI**: Automatic "Authorize" button integration

### Key Code Snippets

```python
# 1. Define OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# 2. Token endpoint
@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(db, form_data.username, form_data.password)
    return {"access_token": create_access_token(...), "token_type": "bearer"}

# 3. Protected endpoint
@app.get("/users/me")
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user
```

### Next Steps

1. Implement the practice assignment
2. Add role-based access control (RBAC)
3. Integrate with a frontend application
4. Deploy to production with HTTPS
5. Add monitoring and logging

---

## Changelog

- **v1.0** (2026-01-30): Initial documentation for OAuth2 implementation
  - OAuth2PasswordBearer setup
  - OAuth2PasswordRequestForm integration
  - Token endpoint implementation
  - Swagger UI integration guide
  - Practice assignment

---

**Happy Coding! 🚀**

For questions or issues, refer to the FastAPI documentation or open an issue in the repository.
