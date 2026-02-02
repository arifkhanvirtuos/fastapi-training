# JWT Authentication Complete Guide - FastAPI
## Duration: 1 Hour

---

## Table of Contents
1. [Introduction & Prerequisites](#introduction--prerequisites)
2. [JWT Basics](#jwt-basics)
3. [User Registration](#user-registration)
4. [Login Endpoint & Token Generation](#login-endpoint--token-generation)
5. [Token Validation Dependency](#token-validation-dependency)
6. [Getting Current User from Token](#getting-current-user-from-token)
7. [Refresh Token Basics](#refresh-token-basics)
8. [Complete Auth Flow](#complete-auth-flow)
9. [Practice Assignment](#practice-assignment)

---

## Introduction & Prerequisites

### What You'll Learn
- How JWT (JSON Web Tokens) work
- Implementing secure user registration with password hashing
- Creating login endpoints that generate access tokens
- Validating tokens and protecting routes
- Extracting user information from tokens
- Implementing refresh tokens for extended sessions

### Prerequisites
You should already have:
- FastAPI basics
- SQLAlchemy models (User model)
- Database setup
- Understanding of HTTP authentication

### Required Packages
```bash
pip install python-jose[cryptography]
pip install passlib[bcrypt]
pip install python-multipart
```

---

## JWT Basics

### What is JWT?
A JWT is a compact, URL-safe token format consisting of three parts:
1. **Header**: Algorithm & token type
2. **Payload**: Claims (user data)
3. **Signature**: Verification signature

**Structure**: `header.payload.signature`

**Example**:
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.
eyJzdWIiOiJ1c2VyQGV4YW1wbGUuY29tIiwiZXhwIjoxNjQwOTk1MjAwfQ.
SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c
```

### Why JWT?
- **Stateless**: No server-side session storage needed
- **Scalable**: Works across multiple servers
- **Secure**: Cryptographically signed
- **Portable**: Can be used across different domains

### JWT Claims
- **sub** (subject): User identifier (usually email or user_id)
- **exp** (expiration): Token expiration timestamp
- **iat** (issued at): Token creation timestamp
- **jti** (JWT ID): Unique token identifier (for refresh tokens)

---

## User Registration

### Step 1: Password Hashing Configuration

**File**: `auth_utils.py`

Create utility functions for password hashing:

```python
from passlib.context import CryptContext

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """
    Hash a plain password using bcrypt
    
    Args:
        password: Plain text password
    
    Returns:
        Hashed password string
    """
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password
    
    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password from database
    
    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)
```

**Why bcrypt?**
- Industry standard for password hashing
- Adaptive (cost factor can be increased)
- Built-in salting
- Resistant to rainbow table attacks

### Step 2: Pydantic Schemas

**File**: `schemas.py`

```python
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime
import uuid

class UserCreate(BaseModel):
    """Schema for user registration"""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    full_name: Optional[str] = Field(None, max_length=100)
    phone_number: Optional[str] = Field(None, max_length=15)
    
    @validator('password')
    def validate_password_strength(cls, v):
        """Ensure password has minimum strength requirements"""
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(char.islower() for char in v):
            raise ValueError('Password must contain at least one lowercase letter')
        return v

class UserResponse(BaseModel):
    """Schema for user response (no password)"""
    id: uuid.UUID
    email: str
    full_name: Optional[str]
    phone_number: Optional[str]
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True  # Pydantic v2 (was orm_mode in v1)

class UserInDB(UserResponse):
    """Schema for user with hashed password (internal use)"""
    hashed_password: str
```

### Step 3: User Registration Endpoint

**File**: `auth_routes.py`

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from database import get_db
from models import User
from schemas import UserCreate, UserResponse
from auth_utils import hash_password

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user
    
    Steps:
    1. Check if user already exists
    2. Hash the password
    3. Create user in database
    4. Return user data (without password)
    """
    
    # Check if user with email already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    # Create new user with hashed password
    try:
        new_user = User(
            email=user_data.email,
            hashed_password=hash_password(user_data.password),
            full_name=user_data.full_name,
            phone_number=user_data.phone_number,
            is_active=True  # Auto-activate (or set to False for email verification)
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        return new_user
        
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User registration failed due to database constraint"
        )
```

**Key Points**:
- Never store plain passwords
- Check for existing users before creating
- Use proper HTTP status codes (201 for creation)
- Handle database integrity errors
- Don't return the hashed password in response

---

## Login Endpoint & Token Generation

### Step 1: JWT Configuration

**File**: `auth_config.py`

```python
from datetime import timedelta

# JWT Configuration
SECRET_KEY = "your-secret-key-here-change-in-production-use-openssl-rand-hex-32"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Token configuration
class TokenConfig:
    SECRET_KEY = SECRET_KEY
    ALGORITHM = ALGORITHM
    ACCESS_TOKEN_EXPIRE_MINUTES = ACCESS_TOKEN_EXPIRE_MINUTES
    REFRESH_TOKEN_EXPIRE_DAYS = REFRESH_TOKEN_EXPIRE_DAYS
```

**⚠️ Security Best Practices**:
- Generate SECRET_KEY using: `openssl rand -hex 32`
- Store SECRET_KEY in environment variables (`.env` file)
- Never commit SECRET_KEY to version control
- Use different keys for development and production

### Step 2: Token Creation Functions

**File**: `auth_utils.py` (add to existing file)

```python
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import uuid

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token
    
    Args:
        data: Dictionary containing claims (usually {"sub": user_email})
        expires_delta: Optional custom expiration time
    
    Returns:
        Encoded JWT token string
    """
    from auth_config import TokenConfig
    
    to_encode = data.copy()
    
    # Set expiration time
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=TokenConfig.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Add standard JWT claims
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })
    
    # Encode the token
    encoded_jwt = jwt.encode(
        to_encode, 
        TokenConfig.SECRET_KEY, 
        algorithm=TokenConfig.ALGORITHM
    )
    
    return encoded_jwt

def create_refresh_token(data: dict) -> str:
    """
    Create a JWT refresh token with longer expiration
    
    Args:
        data: Dictionary containing claims
    
    Returns:
        Encoded JWT refresh token string
    """
    from auth_config import TokenConfig
    
    to_encode = data.copy()
    
    # Refresh tokens have longer expiration
    expire = datetime.utcnow() + timedelta(days=TokenConfig.REFRESH_TOKEN_EXPIRE_DAYS)
    
    # Add unique identifier and type
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "jti": str(uuid.uuid4()),  # Unique token ID
        "type": "refresh"
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        TokenConfig.SECRET_KEY,
        algorithm=TokenConfig.ALGORITHM
    )
    
    return encoded_jwt

def decode_token(token: str) -> Dict[str, Any]:
    """
    Decode and validate a JWT token
    
    Args:
        token: JWT token string
    
    Returns:
        Decoded payload dictionary
    
    Raises:
        JWTError: If token is invalid or expired
    """
    from auth_config import TokenConfig
    
    try:
        payload = jwt.decode(
            token,
            TokenConfig.SECRET_KEY,
            algorithms=[TokenConfig.ALGORITHM]
        )
        return payload
    except JWTError as e:
        raise JWTError(f"Token validation failed: {str(e)}")
```

### Step 3: Authentication Function

**File**: `auth_utils.py` (add to existing file)

```python
from typing import Optional
from sqlalchemy.orm import Session

def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """
    Authenticate a user by email and password
    
    Args:
        db: Database session
        email: User email
        password: Plain text password
    
    Returns:
        User object if authentication successful, None otherwise
    """
    from models import User
    
    # Find user by email
    user = db.query(User).filter(User.email == email).first()
    
    # Verify user exists and password is correct
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    
    return user
```

### Step 4: Token Response Schema

**File**: `schemas.py` (add to existing file)

```python
class Token(BaseModel):
    """Schema for token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    """Schema for data extracted from token"""
    email: Optional[str] = None
    user_id: Optional[uuid.UUID] = None
```

### Step 5: Login Endpoint

**File**: `auth_routes.py` (add to existing file)

```python
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from schemas import Token
from auth_utils import authenticate_user, create_access_token, create_refresh_token
from auth_config import TokenConfig

@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Login endpoint that returns access and refresh tokens
    
    OAuth2PasswordRequestForm expects:
    - username: User's email (field name is 'username' but we use it for email)
    - password: User's password
    
    Returns:
    - access_token: Short-lived token for API access
    - refresh_token: Long-lived token for getting new access tokens
    - token_type: "bearer"
    """
    
    # Authenticate user
    user = authenticate_user(db, form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is not active"
        )
    
    # Create access token
    access_token = create_access_token(
        data={"sub": user.email, "user_id": str(user.id)}
    )
    
    # Create refresh token
    refresh_token = create_refresh_token(
        data={"sub": user.email, "user_id": str(user.id)}
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }
```

**Key Points**:
- Use `OAuth2PasswordRequestForm` for standard OAuth2 compatibility
- The form's `username` field is used for email
- Return both access and refresh tokens
- Always check if user is active
- Use proper HTTP status codes (401 for unauthorized)
- Include "WWW-Authenticate" header for OAuth2 compliance

---

## Token Validation Dependency

### Step 1: OAuth2 Scheme Setup

**File**: `dependencies.py`

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session
from database import get_db
from auth_utils import decode_token
from models import User
from schemas import TokenData
from typing import Optional

# OAuth2 scheme - tells FastAPI where to look for the token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")
```

**What is OAuth2PasswordBearer?**
- Extracts token from the `Authorization` header
- Expected format: `Authorization: Bearer <token>`
- `tokenUrl` is the relative path to the login endpoint
- Makes the endpoint show a lock icon in OpenAPI docs

### Step 2: Token Validation Dependency

**File**: `dependencies.py` (continued)

```python
async def get_current_user_token(token: str = Depends(oauth2_scheme)) -> TokenData:
    """
    Validate token and extract user data
    
    This dependency:
    1. Extracts token from Authorization header
    2. Decodes and validates the token
    3. Extracts user information from token claims
    4. Returns TokenData with user info
    
    Args:
        token: JWT token from Authorization header
    
    Returns:
        TokenData object with user information
    
    Raises:
        HTTPException: If token is invalid or expired
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode the token
        payload = decode_token(token)
        
        # Extract user email from 'sub' claim
        email: str = payload.get("sub")
        user_id: str = payload.get("user_id")
        token_type: str = payload.get("type")
        
        if email is None:
            raise credentials_exception
        
        # Verify it's an access token (not refresh)
        if token_type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type. Please use access token.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        token_data = TokenData(email=email, user_id=user_id)
        return token_data
        
    except JWTError:
        raise credentials_exception
```

**Key Points**:
- Always raise HTTP 401 for authentication failures
- Include "WWW-Authenticate" header
- Validate token type (access vs refresh)
- Extract email from "sub" claim (standard JWT practice)
- Handle JWT decoding errors gracefully

---

## Getting Current User from Token

### Step 1: Get Current User Dependency

**File**: `dependencies.py` (continued)

```python
async def get_current_user(
    token_data: TokenData = Depends(get_current_user_token),
    db: Session = Depends(get_db)
) -> User:
    """
    Get the current user from database using token data
    
    This dependency:
    1. Uses get_current_user_token to validate token
    2. Queries database for user by email
    3. Verifies user exists and is active
    4. Returns full User object
    
    Args:
        token_data: Token data from get_current_user_token dependency
        db: Database session
    
    Returns:
        User object from database
    
    Raises:
        HTTPException: If user not found or inactive
    """
    user = db.query(User).filter(User.email == token_data.email).first()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Convenience dependency that ensures user is active
    
    This is a wrapper around get_current_user that explicitly
    checks the active status. Use this for endpoints that
    require an active user.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user
```

**Dependency Chain**:
```
oauth2_scheme (extract token)
    ↓
get_current_user_token (validate & decode token)
    ↓
get_current_user (fetch user from database)
    ↓
get_current_active_user (verify user is active)
```

### Step 2: Using Dependencies in Protected Routes

**File**: `protected_routes.py`

```python
from fastapi import APIRouter, Depends
from dependencies import get_current_user, get_current_active_user
from models import User
from schemas import UserResponse

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """
    Get current logged-in user's information
    
    This endpoint:
    - Requires valid access token
    - Returns current user's data
    - Only active users can access
    """
    return current_user

@router.get("/profile")
async def get_my_profile(current_user: User = Depends(get_current_user)):
    """
    Get current user's detailed profile
    """
    return {
        "email": current_user.email,
        "full_name": current_user.full_name,
        "phone_number": current_user.phone_number,
        "created_at": current_user.created_at,
        "is_active": current_user.is_active
    }

@router.put("/me", response_model=UserResponse)
async def update_user_me(
    full_name: Optional[str] = None,
    phone_number: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update current user's information
    """
    if full_name:
        current_user.full_name = full_name
    if phone_number:
        current_user.phone_number = phone_number
    
    db.commit()
    db.refresh(current_user)
    
    return current_user
```

**How to Use Protected Routes**:

1. **Client sends request with token**:
   ```http
   GET /users/me
   Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   ```

2. **FastAPI automatically**:
   - Extracts token from header (oauth2_scheme)
   - Validates token (get_current_user_token)
   - Fetches user from database (get_current_user)
   - Injects user into endpoint function

3. **Endpoint receives authenticated user**:
   ```python
   current_user: User  # Full user object from database
   ```

---

## Refresh Token Basics

### Why Refresh Tokens?

**Problem**: Short-lived access tokens expire frequently, requiring users to re-login.

**Solution**: Use refresh tokens to get new access tokens without re-authentication.

**Security Model**:
- **Access Token**: Short-lived (15-30 minutes), used for API requests
- **Refresh Token**: Long-lived (7-30 days), used only to get new access tokens

### Step 1: Refresh Token Endpoint

**File**: `auth_routes.py` (add to existing file)

```python
@router.post("/refresh", response_model=Token)
def refresh_access_token(
    refresh_token: str,
    db: Session = Depends(get_db)
):
    """
    Get new access token using refresh token
    
    Flow:
    1. Validate refresh token
    2. Extract user information
    3. Verify user still exists and is active
    4. Generate new access token
    5. Optionally rotate refresh token (best practice)
    
    Args:
        refresh_token: The refresh token
    
    Returns:
        New access and refresh tokens
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode refresh token
        payload = decode_token(refresh_token)
        
        # Verify it's a refresh token
        token_type: str = payload.get("type")
        if token_type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type. Please use refresh token."
            )
        
        # Extract user data
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        
        # Verify user still exists and is active
        user = db.query(User).filter(User.email == email).first()
        if not user or not user.is_active:
            raise credentials_exception
        
        # Create new tokens
        new_access_token = create_access_token(
            data={"sub": user.email, "user_id": str(user.id)}
        )
        
        # Optional: Rotate refresh token (create new one)
        new_refresh_token = create_refresh_token(
            data={"sub": user.email, "user_id": str(user.id)}
        )
        
        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer"
        }
        
    except JWTError:
        raise credentials_exception
```

### Step 2: Token Rotation (Advanced)

**Why Rotate Refresh Tokens?**
- If refresh token is stolen, it can only be used once
- Detects token theft (both legitimate and stolen refresh become invalid)

**Implementation Strategy**:

1. **Store used refresh tokens in database**:
```python
# models.py - Add to User model or create separate table
class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    jti = Column(String(36), unique=True, nullable=False)  # JWT ID
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    revoked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", backref="refresh_tokens")
```

2. **Check token on refresh**:
```python
# In refresh endpoint, before creating new token:
token_jti = payload.get("jti")
stored_token = db.query(RefreshToken).filter(
    RefreshToken.jti == token_jti,
    RefreshToken.revoked == False
).first()

if not stored_token:
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Refresh token has been revoked or does not exist"
    )

# Mark old token as revoked
stored_token.revoked = True
db.commit()
```

### Step 3: Logout (Token Revocation)

**File**: `auth_routes.py` (add to existing file)

```python
@router.post("/logout")
def logout(
    refresh_token: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Logout user by revoking refresh token
    
    Note: Access tokens cannot be revoked (they expire naturally).
    This endpoint revokes the refresh token so no new access
    tokens can be issued.
    """
    try:
        payload = decode_token(refresh_token)
        token_jti = payload.get("jti")
        
        if token_jti:
            # Mark token as revoked in database
            token = db.query(RefreshToken).filter(
                RefreshToken.jti == token_jti,
                RefreshToken.user_id == current_user.id
            ).first()
            
            if token:
                token.revoked = True
                db.commit()
        
        return {"message": "Successfully logged out"}
        
    except JWTError:
        # Even if token is invalid, consider logout successful
        return {"message": "Successfully logged out"}
```

---

## Complete Auth Flow

### Registration → Login → Protected Access Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    COMPLETE AUTH FLOW                        │
└─────────────────────────────────────────────────────────────┘

1. USER REGISTRATION
   Client                          Server                     Database
     │                                │                           │
     │  POST /auth/register           │                           │
     │  {email, password, ...}        │                           │
     ├───────────────────────────────>│                           │
     │                                │  Hash password            │
     │                                │  Create user              │
     │                                ├──────────────────────────>│
     │                                │<──────────────────────────┤
     │  201 Created                   │  User saved               │
     │  {id, email, ...}              │                           │
     │<───────────────────────────────┤                           │
     │                                │                           │

2. USER LOGIN
     │  POST /auth/login              │                           │
     │  {username, password}          │                           │
     ├───────────────────────────────>│                           │
     │                                │  Query user               │
     │                                ├──────────────────────────>│
     │                                │<──────────────────────────┤
     │                                │  Verify password          │
     │                                │  Generate tokens          │
     │  200 OK                        │  (access + refresh)       │
     │  {access_token, refresh_token} │                           │
     │<───────────────────────────────┤                           │
     │  Store tokens                  │                           │
     │                                │                           │

3. ACCESSING PROTECTED ROUTE
     │  GET /users/me                 │                           │
     │  Authorization: Bearer <token> │                           │
     ├───────────────────────────────>│                           │
     │                                │  Extract token            │
     │                                │  Validate token           │
     │                                │  Decode payload           │
     │                                │  Query user by email      │
     │                                ├──────────────────────────>│
     │                                │<──────────────────────────┤
     │  200 OK                        │  Return user data         │
     │  {user data}                   │                           │
     │<───────────────────────────────┤                           │
     │                                │                           │

4. TOKEN REFRESH (Access token expired)
     │  POST /auth/refresh            │                           │
     │  {refresh_token}               │                           │
     ├───────────────────────────────>│                           │
     │                                │  Validate refresh token   │
     │                                │  Verify user active       │
     │                                ├──────────────────────────>│
     │                                │<──────────────────────────┤
     │                                │  Generate new tokens      │
     │  200 OK                        │                           │
     │  {access_token, refresh_token} │                           │
     │<───────────────────────────────┤                           │
     │  Update stored tokens          │                           │
     │                                │                           │

5. LOGOUT
     │  POST /auth/logout             │                           │
     │  Authorization: Bearer <token> │                           │
     │  {refresh_token}               │                           │
     ├───────────────────────────────>│                           │
     │                                │  Revoke refresh token     │
     │                                ├──────────────────────────>│
     │                                │<──────────────────────────┤
     │  200 OK                        │                           │
     │  {message: "Logged out"}       │                           │
     │<───────────────────────────────┤                           │
     │  Clear stored tokens           │                           │
     │                                │                           │
```

### File Structure Summary

```
sql_app/
├── models.py                    # User and RefreshToken models
├── database.py                  # Database setup
├── schemas.py                   # Pydantic schemas
├── auth_config.py              # JWT configuration
├── auth_utils.py               # Password & token utilities
├── dependencies.py             # Auth dependencies
├── auth_routes.py              # Auth endpoints (register, login, refresh)
├── protected_routes.py         # Protected user endpoints
└── main.py                     # FastAPI app with router includes
```

### Main App Setup

**File**: `main.py`

```python
from fastapi import FastAPI
from auth_routes import router as auth_router
from protected_routes import router as protected_router
from database import init_db

app = FastAPI(title="JWT Authentication API")

# Initialize database
@app.on_event("startup")
def startup():
    init_db()

# Include routers
app.include_router(auth_router)
app.include_router(protected_router)

@app.get("/")
def read_root():
    return {"message": "JWT Authentication API"}
```

---

## Practice Assignment

### Assignment: Build a Complete Task Management System with Authentication

**Objective**: Apply JWT authentication to create a secure task management API.

### Requirements

#### 1. User Authentication (30 minutes)
Implement the following endpoints:

- **POST /auth/register**
  - Register new user
  - Validate email format and password strength
  - Return user data (no password)

- **POST /auth/login**
  - Authenticate user
  - Return access and refresh tokens
  - Handle invalid credentials

- **POST /auth/refresh**
  - Get new access token using refresh token
  - Validate refresh token type

- **POST /auth/logout**
  - Revoke refresh token
  - Require valid access token

#### 2. Protected Task Endpoints (30 minutes)

Create a Task model:
```python
class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    completed = Column(Boolean, default=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", backref="tasks")
```

Implement these endpoints (all require authentication):

- **GET /tasks**
  - List current user's tasks
  - Support pagination (skip, limit)
  - Filter by completed status

- **POST /tasks**
  - Create new task for current user
  - Validate task data

- **GET /tasks/{task_id}**
  - Get specific task
  - Only return if task belongs to current user

- **PUT /tasks/{task_id}**
  - Update task
  - Only allow updating own tasks

- **DELETE /tasks/{task_id}**
  - Delete task
  - Only allow deleting own tasks

- **PATCH /tasks/{task_id}/complete**
  - Mark task as complete
  - Toggle completion status

### Testing Checklist

Test your implementation using these scenarios:

#### Registration Tests
- [ ] Register new user with valid data
- [ ] Try registering with existing email (should fail)
- [ ] Try weak password (should fail validation)
- [ ] Try invalid email format (should fail)

#### Login Tests
- [ ] Login with correct credentials
- [ ] Login with wrong password (should fail)
- [ ] Login with non-existent email (should fail)
- [ ] Verify both tokens are returned

#### Protected Route Tests
- [ ] Access protected route without token (should get 401)
- [ ] Access protected route with valid token (should succeed)
- [ ] Access protected route with expired token (should get 401)
- [ ] Access protected route with malformed token (should get 401)

#### Task CRUD Tests
- [ ] Create task as authenticated user
- [ ] List only current user's tasks
- [ ] Try accessing another user's task (should fail)
- [ ] Update own task
- [ ] Delete own task
- [ ] Mark task as complete

#### Refresh Token Tests
- [ ] Use refresh token to get new access token
- [ ] Try using access token on refresh endpoint (should fail)
- [ ] Try using expired refresh token (should fail)

#### Logout Tests
- [ ] Logout and verify refresh token is revoked
- [ ] Try using revoked refresh token (should fail)

### Bonus Challenges

1. **Email Verification**: Make `is_active=False` on registration, send verification email

2. **Password Reset**:
   - POST /auth/forgot-password (send reset token via email)
   - POST /auth/reset-password (reset with token)

3. **User Roles**: Add role-based access control (admin, user)

4. **Token Blacklisting**: Implement access token blacklisting

5. **Rate Limiting**: Add rate limiting to login endpoint

### Solution Testing with cURL

```bash
# 1. Register user
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123",
    "full_name": "John Doe"
  }'

# 2. Login
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=SecurePass123"

# Save the access_token from response

# 3. Access protected route
curl -X GET "http://localhost:8000/users/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# 4. Create task
curl -X POST "http://localhost:8000/tasks" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Complete JWT tutorial",
    "description": "Finish the practice assignment"
  }'

# 5. List tasks
curl -X GET "http://localhost:8000/tasks" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# 6. Refresh token
curl -X POST "http://localhost:8000/auth/refresh" \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "YOUR_REFRESH_TOKEN"}'
```

### Testing with Python requests

```python
import requests

BASE_URL = "http://localhost:8000"

# Register
response = requests.post(
    f"{BASE_URL}/auth/register",
    json={
        "email": "user@example.com",
        "password": "SecurePass123",
        "full_name": "John Doe"
    }
)
print("Register:", response.json())

# Login
response = requests.post(
    f"{BASE_URL}/auth/login",
    data={
        "username": "user@example.com",
        "password": "SecurePass123"
    }
)
tokens = response.json()
access_token = tokens["access_token"]
print("Login:", tokens)

# Access protected route
headers = {"Authorization": f"Bearer {access_token}"}
response = requests.get(f"{BASE_URL}/users/me", headers=headers)
print("Current User:", response.json())

# Create task
response = requests.post(
    f"{BASE_URL}/tasks",
    headers=headers,
    json={
        "title": "Complete JWT tutorial",
        "description": "Finish the practice assignment"
    }
)
print("Task Created:", response.json())
```

---

## Key Takeaways

### Security Best Practices

1. **Never store plain passwords** - Always hash with bcrypt
2. **Keep SECRET_KEY secure** - Use environment variables
3. **Short access token expiry** - 15-30 minutes
4. **Long refresh token expiry** - 7-30 days
5. **Validate token type** - Prevent refresh token misuse
6. **Check user active status** - On every protected request
7. **Use HTTPS in production** - Tokens sent in headers must be encrypted

### Common Pitfalls to Avoid

❌ **DON'T**: Store tokens in localStorage (vulnerable to XSS)
✅ **DO**: Store in httpOnly cookies or secure storage

❌ **DON'T**: Send passwords in GET requests
✅ **DO**: Use POST with request body

❌ **DON'T**: Return passwords in API responses
✅ **DO**: Exclude password fields in response schemas

❌ **DON'T**: Use predictable SECRET_KEYs
✅ **DO**: Generate with `openssl rand -hex 32`

❌ **DON'T**: Accept refresh tokens in place of access tokens
✅ **DO**: Validate token type in dependencies

### Performance Tips

1. **Cache user data** - After token validation (use Redis)
2. **Index database columns** - Email and user_id columns
3. **Connection pooling** - Configure SQLAlchemy pool size
4. **Async endpoints** - Use async/await for I/O operations

### Next Steps

1. Implement the practice assignment
2. Add email verification
3. Implement password reset flow
4. Add role-based access control (RBAC)
5. Integrate with frontend (React, Vue, etc.)
6. Deploy to production with proper secret management
7. Set up monitoring and logging
8. Implement API rate limiting

---

## Additional Resources

### Documentation
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [JWT.io](https://jwt.io/)
- [OAuth 2.0 RFC](https://tools.ietf.org/html/rfc6749)
- [Passlib Documentation](https://passlib.readthedocs.io/)

### Tools
- [JWT Debugger](https://jwt.io/#debugger)
- [Postman](https://www.postman.com/) - API testing
- [Insomnia](https://insomnia.rest/) - API testing

### Security
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [OWASP API Security](https://owasp.org/www-project-api-security/)

---

## Glossary

- **JWT**: JSON Web Token - A compact token format for securely transmitting information
- **Bearer Token**: A token that grants access to whoever possesses it
- **OAuth2**: An authorization framework for token-based authentication
- **Hashing**: One-way encryption for passwords
- **Salt**: Random data added to passwords before hashing
- **Claims**: Data stored in JWT payload (sub, exp, iat, etc.)
- **Access Token**: Short-lived token for API access
- **Refresh Token**: Long-lived token for obtaining new access tokens
- **Dependency Injection**: FastAPI pattern for reusable logic
- **Middleware**: Code that runs before/after requests

---

**End of Guide**

Happy coding! 🚀
