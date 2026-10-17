"""
Festivals API routes.
"""

from fastapi import APIRouter, Depends
from typing import Optional
from beanie import PydanticObjectId

from app.core.dependencies import get_current_admin
from app.domain.festivals.models import Festival
from app.domain.users.models import User

router = APIRouter(prefix="/festivals", tags=["Festivals"])


@router.get("")
async def get_festivals():
    """Get all festivals (public)."""
    festivals = await Festival.find_all().to_list()
    return festivals


@router.get("/{festival_id}")
async def get_festival(festival_id: str):
    """Get a single festival by ID (public)."""
    festival = await Festival.get(PydanticObjectId(festival_id))
    if not festival:
        return {"message": "Festival not found"}
    return festival


@router.post("")
async def create_festival(
    festival_data: dict,
    admin: User = Depends(get_current_admin),
):
    """Create a new festival (admin only)."""
    festival = Festival(**festival_data)
    await festival.insert()
    return {"message": "Festival created", "data": festival}


@router.put("/{festival_id}")
async def update_festival(
    festival_id: str,
    update_data: dict,
    admin: User = Depends(get_current_admin),
):
    """Update a festival (admin only)."""
    festival = await Festival.get(PydanticObjectId(festival_id))
    if not festival:
        return {"message": "Festival not found"}

    for key, value in update_data.items():
        if hasattr(festival, key):
            setattr(festival, key, value)

    await festival.save()
    return {"message": "Festival updated", "data": festival}


@router.delete("/{festival_id}")
async def delete_festival(
    festival_id: str,
    admin: User = Depends(get_current_admin),
):
    """Delete a festival (admin only)."""
    festival = await Festival.get(PydanticObjectId(festival_id))
    if not festival:
        return {"message": "Festival not found"}
    await festival.delete()
    return {"message": "Festival deleted"}
