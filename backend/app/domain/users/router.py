"""
Users API routes (admin management + user profile).
"""

from fastapi import APIRouter, Depends, UploadFile, File
from beanie import PydanticObjectId
import os

from app.core.dependencies import get_current_user, get_current_admin
from app.domain.users.models import User

router = APIRouter(prefix="/users", tags=["Users"])

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "frontend", "assets", "uploads")


@router.get("/profile")
async def get_profile(current_user: User = Depends(get_current_user)):
    """Get current user's profile."""
    return {
        "id": str(current_user.id),
        "name": current_user.name,
        "email": current_user.email,
        "mobile": current_user.mobile,
        "preferred_language": current_user.preferred_language,
        "address": current_user.address,
        "photo_url": current_user.photo_url,
        "role": current_user.role,
        "created_at": current_user.created_at.isoformat(),
    }


@router.put("/profile")
async def update_profile(
    update_data: dict,
    current_user: User = Depends(get_current_user),
):
    """Update current user's profile (name, mobile, preferred_language, address)."""
    allowed_fields = {"name", "mobile", "preferred_language", "address"}
    for key, value in update_data.items():
        if key in allowed_fields:
            setattr(current_user, key, value)
    await current_user.save()
    return {"message": "Profile updated successfully"}


@router.get("/all")
async def get_all_users(admin: User = Depends(get_current_admin)):
    """Get all users (admin only)."""
    users = await User.find_all().sort("-created_at").to_list()
    return [
        {
            "id": str(u.id),
            "name": u.name,
            "email": u.email,
            "mobile": u.mobile,
            "role": u.role,
            "is_active": u.is_active,
            "preferred_language": u.preferred_language,
            "created_at": u.created_at.isoformat(),
        }
        for u in users
    ]


@router.put("/{user_id}/block")
async def toggle_block_user(
    user_id: str,
    admin: User = Depends(get_current_admin),
):
    """Block or unblock a user (admin only)."""
    user = await User.get(PydanticObjectId(user_id))
    if not user:
        return {"message": "User not found"}
    user.is_active = not user.is_active
    await user.save()
    status = "unblocked" if user.is_active else "blocked"
    return {"message": f"User {status} successfully"}


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    admin: User = Depends(get_current_admin),
):
    """Delete a user (admin only)."""
    user = await User.get(PydanticObjectId(user_id))
    if not user:
        return {"message": "User not found"}
    if user.role == "admin":
        return {"message": "Cannot delete admin user"}
    await user.delete()
    return {"message": "User deleted successfully"}


@router.post("/change-password")
async def change_password(
    data: dict,
    current_user: User = Depends(get_current_user),
):
    """Change current user's password."""
    old_password = data.get("old_password")
    new_password = data.get("new_password")
    
    if not old_password or not new_password:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Missing old or new password")
        
    from app.core.security import verify_password, hash_password
    if not verify_password(old_password, current_user.hashed_password):
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Incorrect old password")
        
    if len(new_password) < 6:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="New password must be at least 6 characters")
        
    current_user.hashed_password = hash_password(new_password)
    await current_user.save()
    return {"message": "Password changed successfully"}


@router.post("/upload-photo")
async def upload_profile_photo(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """Upload a profile picture for the current user."""
    import os
    import uuid
    
    # Ensure upload directory exists
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    # Generate unique filename
    ext = os.path.splitext(file.filename)[1]
    filename = f"avatar_{current_user.id}_{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    # Save file
    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)

    # Update user model
    photo_url = f"/static/assets/uploads/{filename}"
    current_user.photo_url = photo_url
    await current_user.save()

    return {"photo_url": photo_url}
