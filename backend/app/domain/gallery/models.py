"""
Gallery item document model for MongoDB via Beanie ODM.
"""

from datetime import datetime, timezone
from typing import Optional

from beanie import Document
from pydantic import Field


class GalleryItem(Document):
    """Represents an image or video in the gallery."""

    title_en: str = ""
    title_kn: str = ""
    image_url: str  # Relative path or external URL
    category: str = "temple"  # "temple", "festival", "pooja", "video"
    video_url: Optional[str] = None  # For video gallery items
    uploaded_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    class Settings:
        name = "gallery"
