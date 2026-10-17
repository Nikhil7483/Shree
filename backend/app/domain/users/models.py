"""
User document model for MongoDB via Beanie ODM.
"""

from datetime import datetime, timezone
from typing import Optional

from beanie import Document
from pydantic import EmailStr, Field


class User(Document):
    """Represents a registered user or admin."""

    name: str
    email: str = Field(unique=True)
    mobile: str
    hashed_password: str
    preferred_language: str = "en"  # "en" or "kn"
    role: str = "user"  # "user" or "admin"
    is_active: bool = True
    address: Optional[str] = None
    photo_url: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "users"
