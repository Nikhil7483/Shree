"""
Festival document model for MongoDB via Beanie ODM.
"""

from datetime import datetime, timezone
from typing import Optional

from beanie import Document
from pydantic import Field


class Festival(Document):
    """Represents a temple festival or special event."""

    name_en: str
    name_kn: str
    description_en: str = ""
    description_kn: str = ""
    date: Optional[str] = None  # e.g., "2025-01-14" or "Every Amavasya"
    image_url: Optional[str] = None
    is_recurring: bool = False
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    class Settings:
        name = "festivals"
