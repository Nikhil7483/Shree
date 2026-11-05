"""
Shared FastAPI dependencies for authentication and authorization.
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import decode_access_token
from app.domain.users.models import User

# HTTP Bearer token scheme
security_scheme = HTTPBearer()
optional_security_scheme = HTTPBearer(auto_error=False)


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_security_scheme),
) -> Optional[User]:
    """
    Extract authenticated User if Authorization header is present, else None.
    """
    if credentials is None:
        return None
    token = credentials.credentials
    payload = decode_access_token(token)
    if payload is None:
        return None
    email: str = payload.get("sub")
    if email is None:
        return None
    user = await User.find_one({"email": email})
    if not user and payload.get("role") == "admin":
        return User(
            name="Temple Admin",
            email=email,
            mobile="0000000000",
            hashed_password="",
            preferred_language="kn",
            role="admin",
            is_active=True,
        )
    return user


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
) -> User:
    """
    Dependency that extracts and validates the JWT from the Authorization header.
    Returns the authenticated User document.
    """
    token = credentials.credentials
    payload = decode_access_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    email: str = payload.get("sub")
    if email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await User.find_one({"email": email})
    if user is None:
        if payload.get("role") == "admin":
            return User(
                name="Temple Admin",
                email=email,
                mobile="0000000000",
                hashed_password="",
                preferred_language="kn",
                role="admin",
                is_active=True,
            )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user


async def get_current_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Dependency that ensures the authenticated user has admin role.
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user
