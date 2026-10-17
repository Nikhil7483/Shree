"""
Pydantic schemas for authentication requests and responses.
"""

from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    """Schema for user registration."""
    name: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., min_length=5)
    mobile: str = Field(..., min_length=10, max_length=15)
    password: str = Field(..., min_length=6)
    confirm_password: str = Field(..., min_length=6)
    preferred_language: str = Field(default="en", pattern="^(en|kn)$")


class LoginRequest(BaseModel):
    """Schema for user login."""
    email: str
    password: str


class TokenResponse(BaseModel):
    """Schema for JWT token response."""
    access_token: str
    token_type: str = "bearer"
    user_name: str
    user_email: str
    user_role: str
    preferred_language: str
    photo_url: Optional[str] = None


class UserProfileResponse(BaseModel):
    """Schema for user profile data."""
    id: str
    name: str
    email: str
    mobile: str
    preferred_language: str
    role: str
    created_at: str
