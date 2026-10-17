"""
Unit tests for authentication security, password hashing, and JWT tokens.
"""

import pytest
from app.core.security import hash_password, verify_password, create_access_token
from jose import jwt
from app.core.config import get_settings

settings = get_settings()


def test_password_hashing():
    raw_password = "SecurePassword@123"
    hashed = hash_password(raw_password)
    assert hashed != raw_password
    assert verify_password(raw_password, hashed) is True
    assert verify_password("WrongPassword", hashed) is False


def test_jwt_token_generation_and_decoding():
    payload = {"sub": "donor@example.com", "role": "user"}
    token = create_access_token(payload)
    assert isinstance(token, str)
    assert len(token) > 20

    decoded = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    assert decoded["sub"] == "donor@example.com"
    assert decoded["role"] == "user"
    assert "exp" in decoded
