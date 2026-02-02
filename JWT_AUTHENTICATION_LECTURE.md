# JWT Authentication - Complete Guide

**Duration:** 90+ minutes  
**Level:** Intermediate  
**Prerequisites:** Basic Python, HTTP concepts, FastAPI fundamentals

---

## Table of Contents

1. [Introduction to JWT](#1-introduction-to-jwt)
2. [Understanding Authentication vs Authorization](#2-understanding-authentication-vs-authorization)
3. [What is JWT?](#3-what-is-jwt)
4. [JWT Token Structure](#4-jwt-token-structure)
5. [How JWT Works - The Flow](#5-how-jwt-works---the-flow)
6. [Setting Up Python Environment](#6-setting-up-python-environment)
7. [Creating JWT Tokens with python-jose](#7-creating-jwt-tokens-with-python-jose)
8. [Verifying JWT Tokens](#8-verifying-jwt-tokens)
9. [Token Expiration and Refresh Tokens](#9-token-expiration-and-refresh-tokens)
10. [Implementing JWT in FastAPI](#10-implementing-jwt-in-fastapi)
11. [Security Best Practices](#11-security-best-practices)
12. [Common Pitfalls and How to Avoid Them](#12-common-pitfalls-and-how-to-avoid-them)
13. [Practice Assignments](#13-practice-assignments)
14. [Additional Resources](#14-additional-resources)

---

## 1. Introduction to JWT

### What Problem Does JWT Solve?

Before JWT, traditional session-based authentication worked like this:
- User logs in
- Server creates a session and stores it in memory/database
- Server sends session ID to client (usually in a cookie)
- Client sends session ID with each request
- Server looks up session in storage to verify user

**Problems with Session-Based Auth:**
- ❌ Server must store all sessions (memory/database overhead)
- ❌ Difficult to scale horizontally (session sharing between servers)
- ❌ Not ideal for microservices architecture
- ❌ CORS complications with cookies

**How JWT Solves These Issues:**
- ✅ Stateless - no server-side storage needed
- ✅ Self-contained - all user info in the token
- ✅ Easy to scale - any server can verify the token
- ✅ Perfect for microservices and mobile apps
- ✅ Works seamlessly with CORS

---

## 2. Understanding Authentication vs Authorization

### Authentication
**"Who are you?"** - Verifying the identity of a user.
```
User: "I'm John Doe"
System: "Prove it" (login with password)
User: Provides credentials
System: "OK, you are John Doe" (issues JWT)
```

### Authorization
**"What can you do?"** - Verifying what a user is allowed to access.
```
User: "I want to delete this post"
System: Checks JWT → "You are John Doe"
System: Checks permissions → "John can only delete his own posts"
System: "Access granted" or "Access denied"
```

**Key Takeaway:** JWT handles both - it authenticates (verifies who you are) and can help authorize (contains role/permission info).

---

## 3. What is JWT?

### Definition
**JWT (JSON Web Token)** is an open standard (RFC 7519) that defines a compact and self-contained way for securely transmitting information between parties as a JSON object.

### Key Characteristics

1. **Compact:** Small size, can be sent via URL, POST parameter, or HTTP header
2. **Self-Contained:** Contains all necessary information about the user
3. **Digitally Signed:** Ensures the token hasn't been tampered with

### When to Use JWT

✅ **Good Use Cases:**
- API authentication
- Single Sign-On (SSO)
- Mobile applications
- Microservices communication
- Short-lived access tokens

❌ **Not Ideal For:**
- Long-term storage of sensitive data
- Storing large amounts of data (tokens get big)
- Scenarios requiring immediate token revocation

---

## 4. JWT Token Structure

A JWT consists of three parts separated by dots (`.`):

```
xxxxx.yyyyy.zzzzz
```

### Structure Breakdown

```
HEADER.PAYLOAD.SIGNATURE
```

### Example JWT Token

```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c
```

Let's decode each part:

---

### 4.1 Header (Red Part)

The header typically consists of two parts:
- `typ`: Token type (JWT)
- `alg`: Hashing algorithm (e.g., HS256, RS256)

**Encoded:**
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9
```

**Decoded (Base64):**
```json
{
  "alg": "HS256",
  "typ": "JWT"
}
```

**Common Algorithms:**
- **HS256** (HMAC + SHA256): Symmetric, uses secret key
- **RS256** (RSA + SHA256): Asymmetric, uses private/public key pair
- **ES256** (ECDSA + SHA256): Asymmetric, elliptic curve

---

### 4.2 Payload (Green Part)

The payload contains the **claims** - statements about an entity (usually the user) and additional data.

**Encoded:**
```
eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ
```

**Decoded (Base64):**
```json
{
  "sub": "1234567890",
  "name": "John Doe",
  "iat": 1516239022
}
```

**Types of Claims:**

1. **Registered Claims** (standardized, optional but recommended):
   - `iss` (issuer): Who created the token
   - `sub` (subject): Who the token is about (user ID)
   - `aud` (audience): Who the token is intended for
   - `exp` (expiration): When token expires (Unix timestamp)
   - `nbf` (not before): Token not valid before this time
   - `iat` (issued at): When token was created
   - `jti` (JWT ID): Unique identifier for the token

2. **Public Claims**: Custom claims that should be collision-resistant
   - `email`: user@example.com
   - `roles`: ["admin", "user"]

3. **Private Claims**: Custom claims agreed upon between parties
   - `department`: "Engineering"
   - `employee_id`: "E12345"

**⚠️ Important:** Payload is only Base64 encoded, NOT encrypted. Anyone can decode and read it. Never put sensitive data (passwords, credit card numbers) in the payload!

---

### 4.3 Signature (Blue Part)

The signature ensures the token hasn't been tampered with.

**How it's created:**
```javascript
HMACSHA256(
  base64UrlEncode(header) + "." + base64UrlEncode(payload),
  secret
)
```

**Example with HS256:**
```python
import hmac
import hashlib
import base64

header = base64.urlsafe_b64encode(b'{"alg":"HS256","typ":"JWT"}')
payload = base64.urlsafe_b64encode(b'{"sub":"1234567890","name":"John Doe"}')
secret = "your-256-bit-secret"

signature = hmac.new(
    secret.encode(),
    f"{header}.{payload}".encode(),
    hashlib.sha256
).digest()

signature_encoded = base64.urlsafe_b64encode(signature)
```

**Result:**
```
SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c
```

**Key Point:** To verify the signature, you need the secret key. This proves:
1. The token was created by someone with the secret
2. The token hasn't been modified

---

## 5. How JWT Works - The Flow

### Complete Authentication Flow

```
┌─────────┐                                          ┌─────────┐
│         │  1. POST /login {username, password}     │         │
│         │─────────────────────────────────────────>│         │
│         │                                          │         │
│ Client  │  2. Verify credentials                   │ Server  │
│         │     Generate JWT                         │         │
│         │                                          │         │
│         │<─────────────────────────────────────────│         │
│         │  3. Return JWT token                     │         │
│         │     {access_token: "eyJhbG..."}          │         │
│         │                                          │         │
│         │  4. GET /protected                       │         │
│         │     Header: Authorization: Bearer eyJ... │         │
│         │─────────────────────────────────────────>│         │
│         │                                          │         │
│         │  5. Verify JWT signature                 │         │
│         │     Extract user info from payload       │         │
│         │     Check expiration                     │         │
│         │                                          │         │
│         │<─────────────────────────────────────────│         │
│         │  6. Return protected data                │         │
└─────────┘                                          └─────────┘
```

### Step-by-Step Explanation

**Step 1-3: Login & Token Generation**
1. User submits credentials (username/password)
2. Server verifies credentials against database
3. If valid, server creates JWT with user info
4. Server signs JWT with secret key
5. Server sends JWT back to client

**Step 4-6: Accessing Protected Resources**
1. Client stores JWT (localStorage, memory, etc.)
2. Client includes JWT in Authorization header for subsequent requests
3. Server verifies JWT signature
4. Server extracts user info from payload
5. Server checks token expiration
6. If valid, server processes request and returns data

---

## 6. Setting Up Python Environment

### Install Required Packages

```bash
pip install python-jose[cryptography]
pip install passlib[bcrypt]
pip install python-multipart
pip install fastapi
pip install uvicorn
```

### Package Breakdown

- **python-jose**: JWT encoding/decoding library
- **passlib**: Password hashing utilities
- **python-multipart**: For form data handling
- **cryptography**: Cryptographic primitives (used by jose)

### Create requirements.txt

```txt
fastapi==0.104.1
uvicorn==0.24.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
```

---

## 7. Creating JWT Tokens with python-jose

### 7.1 Basic Token Creation

```python
from jose import jwt
from datetime import datetime, timedelta
from typing import Optional

# Configuration
SECRET_KEY = "your-secret-key-keep-it-secret"  # In production, use environment variable
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    Create a JWT access token
    
    Args:
        data: Dictionary containing claims to encode in the token
        expires_delta: Optional timedelta for token expiration
        
    Returns:
        Encoded JWT token as string
    """
    to_encode = data.copy()
    
    # Set expiration time
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Add expiration claim
    to_encode.update({"exp": expire})
    
    # Create the token
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
```

### 7.2 Using the Function

```python
# Example 1: Simple token with user ID
token_data = {"sub": "user123"}
access_token = create_access_token(data=token_data)
print(f"Access Token: {access_token}")

# Example 2: Token with custom expiration (15 minutes)
token_data = {"sub": "user123", "email": "user@example.com"}
custom_expiration = timedelta(minutes=15)
access_token = create_access_token(data=token_data, expires_delta=custom_expiration)

# Example 3: Token with roles/permissions
token_data = {
    "sub": "user123",
    "email": "admin@example.com",
    "roles": ["admin", "user"],
    "permissions": ["read", "write", "delete"]
}
access_token = create_access_token(data=token_data)
```

### 7.3 Understanding the Output

When you create a token, you get something like:
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyMTIzIiwiZW1haWwiOiJ1c2VyQGV4YW1wbGUuY29tIiwiZXhwIjoxNzA2MzY0MDAwfQ.abc123xyz...
```

You can decode this at [jwt.io](https://jwt.io) to see:
```json
{
  "sub": "user123",
  "email": "user@example.com",
  "exp": 1706364000
}
```

---

## 8. Verifying JWT Tokens

### 8.1 Basic Token Verification

```python
from jose import jwt, JWTError
from typing import Optional

def verify_token(token: str) -> Optional[dict]:
    """
    Verify and decode a JWT token
    
    Args:
        token: The JWT token string to verify
        
    Returns:
        Decoded payload if valid, None if invalid
    """
    try:
        # Decode and verify the token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        print(f"Token verification failed: {e}")
        return None
```

### 8.2 Enhanced Verification with Error Handling

```python
from jose import jwt, JWTError, ExpiredSignatureError
from datetime import datetime

def verify_token_detailed(token: str) -> dict:
    """
    Verify token with detailed error information
    
    Returns:
        Dictionary with 'valid' boolean and 'payload' or 'error'
    """
    try:
        # Decode the token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Additional validation - check if token has required claims
        if "sub" not in payload:
            return {
                "valid": False,
                "error": "Token missing 'sub' claim"
            }
        
        return {
            "valid": True,
            "payload": payload
        }
        
    except ExpiredSignatureError:
        return {
            "valid": False,
            "error": "Token has expired"
        }
    except JWTError as e:
        return {
            "valid": False,
            "error": f"Invalid token: {str(e)}"
        }
```

### 8.3 Using Token Verification

```python
# Create a token
token = create_access_token(data={"sub": "user123", "email": "user@example.com"})

# Verify the token
result = verify_token_detailed(token)

if result["valid"]:
    print("Token is valid!")
    print(f"User ID: {result['payload']['sub']}")
    print(f"Email: {result['payload']['email']}")
    print(f"Expires at: {datetime.fromtimestamp(result['payload']['exp'])}")
else:
    print(f"Token verification failed: {result['error']}")
```

### 8.4 What Can Go Wrong?

```python
# Test 1: Expired Token
expired_token = create_access_token(
    data={"sub": "user123"},
    expires_delta=timedelta(seconds=-1)  # Already expired
)
result = verify_token_detailed(expired_token)
# Output: {"valid": False, "error": "Token has expired"}

# Test 2: Modified Token (tampered)
parts = token.split('.')
tampered_token = parts[0] + '.' + parts[1] + '.fakesignature'
result = verify_token_detailed(tampered_token)
# Output: {"valid": False, "error": "Invalid token: Signature verification failed"}

# Test 3: Malformed Token
result = verify_token_detailed("not.a.jwt.token")
# Output: {"valid": False, "error": "Invalid token: ..."}
```

---

## 9. Token Expiration and Refresh Tokens

### 9.1 Understanding Token Expiration

**Why do tokens expire?**
- **Security**: Limits damage if token is stolen
- **Fresh data**: Forces re-authentication to get updated user info
- **Logout enforcement**: Expired tokens can't be used

**Typical Expiration Times:**
- Access Token: 15-60 minutes (short-lived)
- Refresh Token: 7-30 days (long-lived)

### 9.2 Access Token vs Refresh Token

| Aspect | Access Token | Refresh Token |
|--------|-------------|---------------|
| **Purpose** | Access protected resources | Get new access token |
| **Lifetime** | Short (15-60 min) | Long (7-30 days) |
| **Storage** | Memory (or secure storage) | Secure HTTP-only cookie |
| **Exposure** | Sent with every request | Sent only to refresh endpoint |
| **Risk if stolen** | Limited (expires soon) | Higher (long-lived) |

### 9.3 Implementing Refresh Tokens

```python
from datetime import timedelta

# Configuration
REFRESH_TOKEN_EXPIRE_DAYS = 7

def create_refresh_token(data: dict):
    """
    Create a long-lived refresh token
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({
        "exp": expire,
        "type": "refresh"  # Mark as refresh token
    })
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_refresh_token(token: str) -> Optional[dict]:
    """
    Verify a refresh token and ensure it's the correct type
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Verify it's actually a refresh token
        if payload.get("type") != "refresh":
            return None
            
        return payload
    except JWTError:
        return None
```

### 9.4 Complete Token Flow with Refresh

```python
from typing import Tuple

def login_user(username: str, password: str) -> Tuple[str, str]:
    """
    Simulate user login - returns access and refresh tokens
    
    In real implementation, verify password against database
    """
    # After verifying credentials...
    user_data = {"sub": username, "email": f"{username}@example.com"}
    
    # Create both tokens
    access_token = create_access_token(data=user_data)
    refresh_token = create_refresh_token(data={"sub": username})
    
    return access_token, refresh_token

def refresh_access_token(refresh_token: str) -> Optional[str]:
    """
    Use a refresh token to get a new access token
    """
    # Verify the refresh token
    payload = verify_refresh_token(refresh_token)
    
    if not payload:
        return None
    
    # Create new access token with fresh expiration
    user_data = {"sub": payload["sub"]}
    new_access_token = create_access_token(data=user_data)
    
    return new_access_token
```

### 9.5 Token Refresh Example

```python
# User logs in
access_token, refresh_token = login_user("john_doe", "password123")
print(f"Access Token: {access_token[:50]}...")
print(f"Refresh Token: {refresh_token[:50]}...")

# ... time passes, access token expires ...

# Use refresh token to get new access token
new_access_token = refresh_access_token(refresh_token)
if new_access_token:
    print(f"New Access Token: {new_access_token[:50]}...")
else:
    print("Failed to refresh - user must log in again")
```

---

## 10. Implementing JWT in FastAPI

### 10.1 Complete Authentication System

```python
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext

app = FastAPI()

# Security Configuration
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Models
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None

class UserInDB(User):
    hashed_password: str

# Fake database
fake_users_db = {
    "johndoe": {
        "username": "johndoe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # "secret"
        "disabled": False,
    }
}

# Utility Functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

def get_user(db, username: str):
    """Retrieve user from database"""
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)

def authenticate_user(fake_db, username: str, password: str):
    """Authenticate a user"""
    user = get_user(fake_db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Dependency to get current user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    
    user = get_user(fake_users_db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    """Dependency to get current active user"""
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# Routes
@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login endpoint - returns JWT token"""
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """Get current user - protected route"""
    return current_user

@app.get("/items/")
async def read_items(current_user: User = Depends(get_current_active_user)):
    """Example protected route"""
    return {"items": ["item1", "item2"], "owner": current_user.username}
```

### 10.2 Testing the API

```bash
# Start the server
uvicorn main:app --reload

# Test login (using curl)
curl -X POST "http://localhost:8000/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=johndoe&password=secret"

# Response:
# {
#   "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
#   "token_type": "bearer"
# }

# Test protected endpoint
curl -X GET "http://localhost:8000/users/me" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# Response:
# {
#   "username": "johndoe",
#   "email": "johndoe@example.com",
#   "full_name": "John Doe",
#   "disabled": false
# }
```

---

## 11. Security Best Practices

### 11.1 Secret Key Management

❌ **DON'T:**
```python
SECRET_KEY = "mysecret"  # Too simple
SECRET_KEY = "secret123"  # Predictable
# Hardcoded in source code
```

✅ **DO:**
```python
import os
import secrets

# Generate a secure secret key (do this once)
print(secrets.token_hex(32))
# Output: 09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7

# Use environment variables
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable not set")
```

### 11.2 Token Storage (Client-Side)

| Storage Method | Pros | Cons | Recommendation |
|----------------|------|------|----------------|
| **LocalStorage** | Persistent, easy to use | Vulnerable to XSS | ❌ Avoid |
| **SessionStorage** | Cleared on tab close | Still vulnerable to XSS | ❌ Avoid |
| **Memory (JS variable)** | Not persistent (XSS-safe) | Lost on refresh | ✅ Best for access tokens |
| **HTTP-only Cookie** | XSS-proof | Vulnerable to CSRF | ✅ Best for refresh tokens |

**Recommended Approach:**
- Store **access token** in memory (JavaScript variable)
- Store **refresh token** in HTTP-only, Secure, SameSite cookie

### 11.3 Token Expiration Guidelines

```python
# Production-ready expiration times
ACCESS_TOKEN_EXPIRE_MINUTES = 15    # 15 minutes
REFRESH_TOKEN_EXPIRE_DAYS = 7       # 7 days

# For high-security applications
ACCESS_TOKEN_EXPIRE_MINUTES = 5     # 5 minutes
REFRESH_TOKEN_EXPIRE_DAYS = 1       # 1 day

# For low-security/convenience
ACCESS_TOKEN_EXPIRE_MINUTES = 60    # 1 hour
REFRESH_TOKEN_EXPIRE_DAYS = 30      # 30 days
```

### 11.4 HTTPS Only

```python
# In production, enforce HTTPS
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

app.add_middleware(HTTPSRedirectMiddleware)
```

### 11.5 Additional Security Headers

```python
from fastapi.middleware.cors import CORSMiddleware

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Specific origins only
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)
```

### 11.6 Don't Put Sensitive Data in Payload

❌ **NEVER include:**
- Passwords (even hashed)
- Credit card numbers
- Social security numbers
- API keys or secrets

✅ **Safe to include:**
- User ID
- Username
- Email
- Roles/permissions
- Non-sensitive user preferences

---

## 12. Common Pitfalls and How to Avoid Them

### 12.1 Pitfall: Not Validating Token Expiration

❌ **Wrong:**
```python
def verify_token(token: str):
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    return payload  # Doesn't check expiration!
```

✅ **Correct:**
```python
def verify_token(token: str):
    try:
        # jwt.decode automatically checks expiration
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

### 12.2 Pitfall: Using Weak Secret Keys

❌ **Wrong:**
```python
SECRET_KEY = "secret"
SECRET_KEY = "12345"
SECRET_KEY = "password"
```

✅ **Correct:**
```python
import secrets
# Generate once, store in environment variable
SECRET_KEY = secrets.token_urlsafe(32)
# Use at least 256 bits (32 bytes)
```

### 12.3 Pitfall: Not Handling Token Refresh

❌ **Wrong:**
```python
# Access token expires after 15 minutes
# User gets logged out and has to login again
# Poor user experience!
```

✅ **Correct:**
```python
# Implement refresh token mechanism
# Silently refresh access token before expiration
# User stays logged in for days/weeks
```

### 12.4 Pitfall: Storing Tokens in LocalStorage

❌ **Wrong:**
```javascript
// Client-side
localStorage.setItem('token', accessToken);  // Vulnerable to XSS
```

✅ **Correct:**
```javascript
// Store in memory or HTTP-only cookie
let accessToken = null;  // Memory

// Or use HTTP-only cookie set by server
// Client can't access it via JavaScript
```

### 12.5 Pitfall: Not Validating Algorithm

❌ **Wrong:**
```python
# Could be vulnerable to algorithm substitution attack
payload = jwt.decode(token, SECRET_KEY)
```

✅ **Correct:**
```python
# Always specify allowed algorithms
payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
```

### 12.6 Pitfall: Not Revoking Compromised Tokens

**The Problem:** JWTs are stateless - you can't "delete" them from the server.

**Solutions:**
1. **Keep tokens short-lived** (15-30 min)
2. **Token blacklist** (store revoked tokens in Redis with expiration)
3. **Token versioning** (increment user's token version on logout)

```python
# Token blacklist example
from fastapi import HTTPException
import redis

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def revoke_token(token: str, expires_in: int):
    """Add token to blacklist"""
    redis_client.setex(f"blacklist:{token}", expires_in, "1")

def is_token_blacklisted(token: str) -> bool:
    """Check if token is blacklisted"""
    return redis_client.exists(f"blacklist:{token}")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    if is_token_blacklisted(token):
        raise HTTPException(status_code=401, detail="Token has been revoked")
    # ... rest of verification
```

---

## 13. Practice Assignments

### Assignment 1: Basic Token Utilities (30 minutes)

Create a file called `jwt_utils.py` with the following functions:

**Requirements:**
1. `generate_secret_key()`: Generate a secure random secret key
2. `create_token(user_id: str, expires_in: int = 3600)`: Create a token with user_id that expires in specified seconds
3. `decode_token(token: str)`: Decode and return token payload or None if invalid
4. `is_token_expired(token: str)`: Check if token is expired (return True/False)

**Test cases:**
```python
# Test 1: Create and decode token
token = create_token("user123")
payload = decode_token(token)
assert payload["sub"] == "user123"

# Test 2: Check expiration
short_token = create_token("user123", expires_in=1)
time.sleep(2)
assert is_token_expired(short_token) == True

# Test 3: Invalid token
assert decode_token("invalid.token.here") is None
```

---

### Assignment 2: User Authentication System (45 minutes)

Build a complete authentication system with the following features:

**Requirements:**
1. User registration endpoint (`POST /register`)
   - Accept username, email, password
   - Hash password before storing
   - Return success message

2. Login endpoint (`POST /login`)
   - Verify credentials
   - Return access token and refresh token

3. Protected profile endpoint (`GET /profile`)
   - Require valid access token
   - Return user information

4. Token refresh endpoint (`POST /refresh`)
   - Accept refresh token
   - Return new access token

**Database Schema (use dict for simplicity):**
```python
users_db = {
    "user_id": {
        "username": str,
        "email": str,
        "hashed_password": str,
        "created_at": datetime,
    }
}
```

**Expected API Flow:**
```
1. POST /register {"username": "alice", "email": "alice@test.com", "password": "pass123"}
   → Response: {"message": "User created successfully"}

2. POST /login {"username": "alice", "password": "pass123"}
   → Response: {"access_token": "...", "refresh_token": "..."}

3. GET /profile
   Header: Authorization: Bearer <access_token>
   → Response: {"username": "alice", "email": "alice@test.com"}

4. POST /refresh {"refresh_token": "..."}
   → Response: {"access_token": "..."}
```

---

### Assignment 3: Role-Based Access Control (60 minutes)

Extend Assignment 2 to implement role-based access control (RBAC).

**Requirements:**
1. Add `roles` field to user (e.g., ["user"], ["user", "admin"])
2. Include roles in JWT token payload
3. Create role-checking dependencies:
   - `require_role(role: str)`: Check if user has specific role
   - `require_any_role(roles: List[str])`: Check if user has any of the roles

4. Create protected endpoints:
   - `GET /admin/users` - Only accessible by "admin" role
   - `POST /admin/delete-user/{user_id}` - Only accessible by "admin" role
   - `GET /user/dashboard` - Accessible by any authenticated user

**Example:**
```python
@app.get("/admin/users")
async def list_users(current_user: User = Depends(require_role("admin"))):
    return {"users": users_db}

@app.get("/user/dashboard")
async def dashboard(current_user: User = Depends(get_current_user)):
    return {"message": f"Welcome {current_user.username}"}
```

**Test Cases:**
```python
# Test 1: Admin can access /admin/users
admin_token = create_token_with_role("admin_user", ["admin"])
# Should succeed

# Test 2: Regular user cannot access /admin/users
user_token = create_token_with_role("regular_user", ["user"])
# Should return 403 Forbidden

# Test 3: Both can access /user/dashboard
# Both should succeed
```

---

### Assignment 4: Token Blacklist System (45 minutes)

Implement a token revocation system using an in-memory blacklist.

**Requirements:**
1. Create a `TokenBlacklist` class:
   - `add_token(token: str, expires_at: datetime)`: Add token to blacklist
   - `is_blacklisted(token: str) -> bool`: Check if token is blacklisted
   - `cleanup_expired()`: Remove expired tokens from blacklist

2. Add logout endpoint:
   - `POST /logout` - Blacklist current token

3. Modify `get_current_user` dependency:
   - Check if token is blacklisted before processing

**Implementation:**
```python
class TokenBlacklist:
    def __init__(self):
        self.blacklist = {}  # {token: expires_at}
    
    def add_token(self, token: str, expires_at: datetime):
        # TODO: Implement
        pass
    
    def is_blacklisted(self, token: str) -> bool:
        # TODO: Implement
        pass
    
    def cleanup_expired(self):
        # TODO: Implement
        pass

blacklist = TokenBlacklist()

@app.post("/logout")
async def logout(token: str = Depends(oauth2_scheme)):
    # TODO: Implement
    pass
```

---

### Assignment 5: Complete JWT Authentication Module (90 minutes)

Create a production-ready JWT authentication module.

**File Structure:**
```
jwt_auth/
├── __init__.py
├── config.py          # Configuration settings
├── models.py          # Pydantic models
├── security.py        # Password hashing, token creation
├── dependencies.py    # FastAPI dependencies
└── routes.py          # Authentication routes
```

**Requirements:**

**config.py:**
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    class Config:
        env_file = ".env"
```

**Features to implement:**
1. Environment-based configuration
2. Password hashing with bcrypt
3. Access and refresh token generation
4. Token verification with detailed error handling
5. User registration with validation
6. Login with username/email
7. Protected route examples
8. Token refresh mechanism
9. Logout (token revocation)
10. Password reset flow (bonus)

**Testing:**
Write tests for all endpoints using `pytest` and `httpx`:
```python
def test_register_user():
    # TODO: Test user registration
    pass

def test_login_success():
    # TODO: Test successful login
    pass

def test_login_wrong_password():
    # TODO: Test login with wrong password
    pass

def test_access_protected_route():
    # TODO: Test accessing protected route with valid token
    pass

def test_refresh_token():
    # TODO: Test token refresh
    pass
```

---

## 14. Additional Resources

### Documentation
- [RFC 7519 - JSON Web Token (JWT)](https://tools.ietf.org/html/rfc7519)
- [python-jose Documentation](https://python-jose.readthedocs.io/)
- [FastAPI Security Documentation](https://fastapi.tiangolo.com/tutorial/security/)

### Tools
- [JWT.io Debugger](https://jwt.io/) - Decode and verify JWTs
- [mkjwk.org](https://mkjwk.org/) - Generate JSON Web Keys

### Further Reading
- [OWASP JWT Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Token_for_Java_Cheat_Sheet.html)
- [Auth0 JWT Handbook](https://auth0.com/resources/ebooks/jwt-handbook)

### Video Tutorials
- FastAPI JWT Authentication (Tech With Tim)
- Understanding JWT (Traversy Media)

---

## Summary and Key Takeaways

### What We Learned

1. **JWT Basics**
   - Self-contained tokens for stateless authentication
   - Three parts: Header, Payload, Signature
   - Signed, not encrypted (don't put secrets in payload)

2. **Token Creation**
   - Use strong secret keys (256+ bits)
   - Set appropriate expiration times
   - Include necessary claims (sub, exp, iat)

3. **Token Verification**
   - Always verify signature
   - Check expiration
   - Validate required claims

4. **Security Best Practices**
   - Use HTTPS
   - Short-lived access tokens + long-lived refresh tokens
   - Don't store tokens in localStorage
   - Keep secrets in environment variables

5. **Common Patterns**
   - Login → Issue tokens
   - Protected routes → Verify token
   - Token expired → Refresh token
   - Logout → Blacklist token (optional)

### Next Steps

1. Complete all practice assignments
2. Build a real project using JWT authentication
3. Learn about OAuth2 and OpenID Connect
4. Explore advanced topics: token rotation, introspection, revocation
5. Study different algorithms (RS256, ES256)

---

## Quiz - Test Your Understanding

### Questions

1. What are the three parts of a JWT token?
2. Why should you never put passwords in the JWT payload?
3. What's the difference between an access token and a refresh token?
4. How does the server verify that a JWT hasn't been tampered with?
5. What happens when a JWT expires?
6. Why is it recommended to use short-lived access tokens?
7. What's the purpose of the `sub` claim in a JWT?
8. How would you revoke a JWT before it expires?
9. What's the difference between HS256 and RS256 algorithms?
10. Where should you store the SECRET_KEY in production?

### Answers

1. Header, Payload, Signature
2. Payload is only Base64 encoded, not encrypted - anyone can decode it
3. Access token is short-lived for API access; refresh token is long-lived to get new access tokens
4. By verifying the signature using the secret key
5. Token becomes invalid and cannot be used for authentication
6. Limits the window of opportunity if a token is compromised
7. Subject - identifies who the token is about (usually user ID)
8. Use a token blacklist or token versioning system
9. HS256 uses symmetric key; RS256 uses asymmetric public/private key pair
10. Environment variable, never hardcoded in source code

---

**Congratulations!** You now have a solid understanding of JWT authentication. Practice the assignments and build real-world applications to reinforce your learning.

**Remember:** Security is not a feature, it's a requirement. Always follow best practices when implementing authentication systems.

---

*Last Updated: January 2026*  
*Author: [Your Name]*  
*Version: 1.0*
