"""
Pydantic Schemas for OAuth2 Authentication
This module defines the request/response models for authentication endpoints.
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Union
import uuid
from models import UserRole


# Token Schemas
class Token(BaseModel):
    """
    OAuth2 token response model.
    This is the standard OAuth2 response format.
    """
    access_token: str
    token_type: str
    refresh_token: Optional[str] = None


class TokenData(BaseModel):
    """
    Data extracted from JWT token payload.
    """
    user_id: Optional[str] = None
    email: Optional[str] = None


# User Schemas
class UserBase(BaseModel):
    """Base user schema with common fields."""
    email: EmailStr
    full_name: Optional[str] = None
    phone_number: Optional[str] = None


class UserCreate(UserBase):
    """Schema for user registration."""
    password: str
    role: UserRole = UserRole.USER
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "strongpassword123",
                "full_name": "John Doe",
                "phone_number": "+1234567890",
                "role": "user"
            }
        }


class UserLogin(BaseModel):
    """
    Schema for traditional login endpoint (not OAuth2 standard).
    Note: OAuth2 uses OAuth2PasswordRequestForm instead.
    """
    email: EmailStr
    password: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "strongpassword123"
            }
        }


class UserResponse(UserBase):
    """Schema for user response (excludes sensitive data)."""
    id: uuid.UUID
    role: UserRole
    is_active: bool
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "email": "user@example.com",
                "full_name": "John Doe",
                "phone_number": "+1234567890",
                "role": "user",
                "is_active": True
            }
        }


class UserUpdate(BaseModel):
    """Schema for updating user information."""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "full_name": "Jane Doe",
                "phone_number": "+1987654321"
            }
        }


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request."""
    refresh_token: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }


class MessageResponse(BaseModel):
    """Generic message response schema."""
    message: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Operation successful"
            }
        }
