"""
Data models interface (MongoDB Beanie ODM Documents).
"""

from app.domain.users.models import User
from app.domain.donations.models import Donation
from app.domain.temple.models import Temple
from app.domain.festivals.models import Festival
from app.domain.gallery.models import GalleryItem

__all__ = [
    "User",
    "Donation",
    "Temple",
    "Festival",
    "GalleryItem",
]
