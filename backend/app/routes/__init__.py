"""
Application route handlers interface.
"""

from app.domain.auth.router import router as auth_router
from app.domain.temple.router import router as temple_router
from app.domain.gallery.router import router as gallery_router
from app.domain.festivals.router import router as festivals_router
from app.domain.donations.router import router as donations_router
from app.domain.users.router import router as users_router
from app.domain.admin.router import router as admin_router

__all__ = [
    "auth_router",
    "temple_router",
    "gallery_router",
    "festivals_router",
    "donations_router",
    "users_router",
    "admin_router",
]
