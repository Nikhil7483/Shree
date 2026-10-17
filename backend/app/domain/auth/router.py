"""
Authentication API routes.
"""

from fastapi import APIRouter

from app.domain.auth.schemas import RegisterRequest, LoginRequest, TokenResponse
from app.domain.auth.service import register_user, login_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse)
async def register(data: RegisterRequest):
    """Register a new user account."""
    return await register_user(data)


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest):
    """Login with email and password."""
    return await login_user(data)
