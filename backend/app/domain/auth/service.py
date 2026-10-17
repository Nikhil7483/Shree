"""
Authentication business logic: registration and login.
"""

from fastapi import HTTPException, status

from app.core.security import hash_password, verify_password, create_access_token
from app.domain.users.models import User
from app.domain.auth.schemas import RegisterRequest, LoginRequest, TokenResponse


async def register_user(data: RegisterRequest) -> TokenResponse:
    """
    Register a new user.
    Validates passwords match, checks for existing email, creates user, returns JWT.
    """
    # Validate passwords match
    if data.password != data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match",
        )

    # Check if email already exists
    existing = await User.find_one(User.email == data.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    # Create user
    user = User(
        name=data.name,
        email=data.email,
        mobile=data.mobile,
        hashed_password=hash_password(data.password),
        preferred_language=data.preferred_language,
        role="user",
    )
    await user.insert()

    # Generate JWT
    token = create_access_token(data={"sub": user.email, "role": user.role})
    return TokenResponse(
        access_token=token,
        user_name=user.name,
        user_email=user.email,
        user_role=user.role,
        preferred_language=user.preferred_language,
        photo_url=user.photo_url,
    )


async def login_user(data: LoginRequest) -> TokenResponse:
    """
    Authenticate a user by email and password, return JWT.
    """
    user = await User.find_one(User.email == data.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is blocked. Please contact temple administration.",
        )

    if not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Generate JWT
    token = create_access_token(data={"sub": user.email, "role": user.role})
    return TokenResponse(
        access_token=token,
        user_name=user.name,
        user_email=user.email,
        user_role=user.role,
        preferred_language=user.preferred_language,
        photo_url=user.photo_url,
    )
