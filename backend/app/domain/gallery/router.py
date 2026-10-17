"""
Gallery API routes.
"""

from fastapi import APIRouter, Depends, UploadFile, File, Form
from typing import Optional
import os
import uuid

from app.core.dependencies import get_current_admin
from app.domain.gallery.models import GalleryItem
from app.domain.users.models import User

router = APIRouter(prefix="/gallery", tags=["Gallery"])

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "frontend", "assets", "uploads")


@router.get("")
async def get_gallery(category: Optional[str] = None):
    """Get gallery items, optionally filtered by category (public)."""
    all_items = await GalleryItem.find_all().to_list()
    if category and category.lower() != "all":
        items = [
            i for i in all_items 
            if category.lower() in [c.strip().lower() for c in i.category.split(",")]
        ]
    else:
        items = all_items
    return items


@router.post("")
async def add_gallery_item(
    title_en: str = Form(""),
    title_kn: str = Form(""),
    category: str = Form("temple"),
    video_url: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    admin: User = Depends(get_current_admin),
):
    """Add a new gallery item with optional image upload (admin only)."""
    image_url = ""

    if image and image.filename:
        # Ensure upload directory exists
        os.makedirs(UPLOAD_DIR, exist_ok=True)

        # Generate unique filename
        ext = os.path.splitext(image.filename)[1]
        filename = f"{uuid.uuid4().hex}{ext}"
        filepath = os.path.join(UPLOAD_DIR, filename)

        # Save file
        content = await image.read()
        with open(filepath, "wb") as f:
            f.write(content)

        image_url = f"/static/assets/uploads/{filename}"

    item = GalleryItem(
        title_en=title_en,
        title_kn=title_kn,
        image_url=image_url,
        category=category,
        video_url=video_url,
    )
    await item.insert()
    return {"message": "Gallery item added", "data": item}


@router.delete("/{item_id}")
async def delete_gallery_item(
    item_id: str,
    admin: User = Depends(get_current_admin),
):
    """Delete a gallery item (admin only)."""
    from beanie import PydanticObjectId
    item = await GalleryItem.get(PydanticObjectId(item_id))
    if not item:
        return {"message": "Item not found"}
    await item.delete()
    return {"message": "Gallery item deleted"}
