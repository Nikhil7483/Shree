"""
Admin dashboard API routes.
"""

from fastapi import APIRouter, Depends
from app.core.dependencies import get_current_admin
from app.domain.admin.service import get_dashboard_stats
from app.domain.users.models import User

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/dashboard")
async def dashboard(admin: User = Depends(get_current_admin)):
    """Get admin dashboard statistics."""
    stats = await get_dashboard_stats()
    return stats
