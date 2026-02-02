"""
OAuth2 Authentication Module
This module provides OAuth2-compliant authentication utilities including:
- Password hashing and verification
- JWT token creation and validation
- OAuth2PasswordBearer for automatic token extraction
- User authentication and authorization
- Role-based access control (RBAC)
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Union, List
from jose import JWTError, jwt
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from database import get_db
from models import User, UserRole
from enum import Enum

# Security configuration
SECRET_KEY = "your-secret-key-keep-it-secret-in-production"  # TODO: Move to environment variable
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Password hashing context using bcrypt


# OAuth2PasswordBearer automatically extracts token from Authorization header
# tokenUrl points to the endpoint that returns tokens
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# Password Hashing Utilities
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.
    
    Args:
        plain_password: The plain text password to verify
        hashed_password: The hashed password to compare against
        
    Returns:
        bool: True if passwords match, False otherwise
    """
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: The plain text password to hash
        
    Returns:
        str: The hashed password
    """
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


# User Authentication
def authenticate_user(db: Session, email: str, password: str) -> Union[User, bool]:
    """
    Authenticate a user by email and password.
    
    Args:
        db: Database session
        email: User's email address
        password: Plain text password
        
    Returns:
        User object if authentication successful, False otherwise
    """
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


# JWT Token Creation
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Dictionary containing the claims to encode (e.g., {"sub": user_id})
        expires_delta: Optional custom expiration time
        
    Returns:
        str: Encoded JWT token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "type": "access"
    })
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT refresh token.
    
    Args:
        data: Dictionary containing the claims to encode (e.g., {"sub": user_id})
        expires_delta: Optional custom expiration time
        
    Returns:
        str: Encoded JWT refresh token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({
        "exp": expire,
        "type": "refresh"
    })
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# Token Verification and User Extraction
async def get_current_user(
    token: str = Depends(oauth2_scheme), 
    db: Session = Depends(get_db)
) -> User:
    """
    Extract and verify the current user from JWT token.
    This dependency can be used in any endpoint that requires authentication.
    
    Args:
        token: JWT token automatically extracted by OAuth2PasswordBearer
        db: Database session
        
    Returns:
        User: The authenticated user object
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode the JWT token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if user_id is None:
            raise credentials_exception
        
        # Verify it's an access token, not a refresh token
        if token_type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
    except JWTError:
        raise credentials_exception
    
    # Fetch user from database
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Verify that the current user is active.
    
    Args:
        current_user: User object from get_current_user dependency
        
    Returns:
        User: The active user object
        
    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


def verify_refresh_token(token: str, db: Session) -> User:
    """
    Verify a refresh token and return the associated user.
    
    Args:
        token: JWT refresh token
        db: Database session
        
    Returns:
        User: The user associated with the token
        
    Raises:
        HTTPException: If token is invalid, expired, or not a refresh token
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if user_id is None:
            raise credentials_exception
        
        # Verify it's a refresh token
        if token_type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type. Expected refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    
    return user


# ============================================================================
# ROLE-BASED ACCESS CONTROL (RBAC)
# ============================================================================

class Permission(str, Enum):
    """System permissions for fine-grained access control"""
    # User permissions
    READ_USERS = "read:users"
    CREATE_USERS = "create:users"
    UPDATE_USERS = "update:users"
    DELETE_USERS = "delete:users"
    
    # Product permissions
    READ_PRODUCTS = "read:products"
    CREATE_PRODUCTS = "create:products"
    UPDATE_PRODUCTS = "update:products"
    DELETE_PRODUCTS = "delete:products"
    
    # Report permissions
    READ_REPORTS = "read:reports"
    EXPORT_DATA = "export:data"
    
    # Admin permissions
    MANAGE_ROLES = "manage:roles"
    VIEW_AUDIT_LOGS = "view:audit_logs"


# Role to permission mapping
ROLE_PERMISSIONS = {
    UserRole.ADMIN: [
        # Admins have all permissions
        Permission.READ_USERS,
        Permission.CREATE_USERS,
        Permission.UPDATE_USERS,
        Permission.DELETE_USERS,
        Permission.READ_PRODUCTS,
        Permission.CREATE_PRODUCTS,
        Permission.UPDATE_PRODUCTS,
        Permission.DELETE_PRODUCTS,
        Permission.READ_REPORTS,
        Permission.EXPORT_DATA,
        Permission.MANAGE_ROLES,
        Permission.VIEW_AUDIT_LOGS,
    ],
    UserRole.MANAGER: [
        Permission.READ_USERS,
        Permission.UPDATE_USERS,
        Permission.READ_PRODUCTS,
        Permission.CREATE_PRODUCTS,
        Permission.UPDATE_PRODUCTS,
        Permission.READ_REPORTS,
        Permission.EXPORT_DATA,
    ],
    UserRole.USER: [
        Permission.READ_PRODUCTS,
        Permission.READ_REPORTS,
    ],
    UserRole.GUEST: [
        Permission.READ_PRODUCTS,
    ],
}


def has_permission(user: User, required_permission: Permission) -> bool:
    """
    Check if user's role has the required permission.
    
    Args:
        user: User object
        required_permission: Permission to check
    
    Returns:
        bool: True if user has permission
    """
    user_permissions = ROLE_PERMISSIONS.get(user.role, [])
    return required_permission in user_permissions


def require_permission(permission: Permission):
    """
    Dependency factory for permission-based access control.
    
    Usage:
        @app.delete("/admin/users/{user_id}")
        def delete_user(
            user_id: uuid.UUID,
            current_user: User = Depends(require_permission(Permission.DELETE_USERS))
        ):
            ...
    
    Args:
        permission: Required permission
    
    Returns:
        Dependency function that checks permission
    """
    async def permission_checker(current_user: User = Depends(get_current_active_user)):
        if not has_permission(current_user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied. Required: {permission.value}"
            )
        return current_user
    
    return permission_checker


def require_role(allowed_roles: List[UserRole]):
    """
    Dependency factory that creates a role checker dependency.
    
    Usage:
        @app.get("/reports")
        def get_reports(
            current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.MANAGER]))
        ):
            ...
    
    Args:
        allowed_roles: List of roles allowed to access the endpoint
    
    Returns:
        Dependency function that checks user role
    """
    async def role_checker(current_user: User = Depends(get_current_active_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {[role.value for role in allowed_roles]}"
            )
        return current_user
    
    return role_checker


async def require_admin(current_user: User = Depends(get_current_active_user)) -> User:
    """
    Dependency that requires admin role.
    
    Usage:
        @app.get("/admin/users")
        def list_users(current_user: User = Depends(require_admin)):
            ...
    
    Args:
        current_user: The current authenticated user
        
    Returns:
        User: The admin user
        
    Raises:
        HTTPException: If user is not an admin
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


async def require_manager_or_admin(current_user: User = Depends(get_current_active_user)) -> User:
    """
    Dependency that requires manager or admin role.
    
    Usage:
        @app.post("/tasks/assign")
        def assign_task(current_user: User = Depends(require_manager_or_admin)):
            ...
    
    Args:
        current_user: The current authenticated user
        
    Returns:
        User: The manager or admin user
        
    Raises:
        HTTPException: If user is not a manager or admin
    """
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Manager or Admin access required"
        )
    return current_user


# Role hierarchy for comparison
ROLE_HIERARCHY = {
    UserRole.ADMIN: 4,
    UserRole.MANAGER: 3,
    UserRole.USER: 2,
    UserRole.GUEST: 1,
}


def has_higher_or_equal_role(user: User, required_role: UserRole) -> bool:
    """
    Check if user's role is higher or equal in hierarchy.
    
    Args:
        user: User object
        required_role: Minimum required role
    
    Returns:
        bool: True if user's role is sufficient
    """
    return ROLE_HIERARCHY.get(user.role, 0) >= ROLE_HIERARCHY.get(required_role, 0)
