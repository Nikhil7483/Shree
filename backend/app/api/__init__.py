"""
FastAPI API route registry.
Aggregates and registers all domain-specific routers under the /api prefix.
"""

from fastapi import APIRouter

from app.domain.auth.router import router as auth_router
from app.domain.temple.router import router as temple_router
from app.domain.gallery.router import router as gallery_router
from app.domain.festivals.router import router as festivals_router
from app.domain.donations.router import router as donations_router
from app.domain.users.router import router as users_router
from app.domain.admin.router import router as admin_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(temple_router)
api_router.include_router(gallery_router)
api_router.include_router(festivals_router)
api_router.include_router(donations_router)
api_router.include_router(users_router)
api_router.include_router(admin_router)

__all__ = [
    "api_router",
    "auth_router",
    "temple_router",
    "gallery_router",
    "festivals_router",
    "donations_router",
    "users_router",
    "admin_router",
]
