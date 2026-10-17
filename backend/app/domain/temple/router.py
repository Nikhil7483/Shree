"""
Temple API routes.
"""

from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_admin
from app.domain.temple.models import Temple
from app.domain.users.models import User

router = APIRouter(prefix="/temple", tags=["Temple"])


@router.get("")
async def get_temple():
    """Get temple information (public)."""
    temple = await Temple.find_one()
    if not temple:
        return {"message": "Temple data not found"}
    return temple


@router.put("")
async def update_temple(
    update_data: dict,
    admin: User = Depends(get_current_admin),
):
    """Update temple information (admin only)."""
    temple = await Temple.find_one()
    if not temple:
        return {"message": "Temple data not found"}

    # Update only provided fields
    for key, value in update_data.items():
        if hasattr(temple, key):
            setattr(temple, key, value)

    await temple.save()
    return {"message": "Temple updated successfully", "data": temple}


# ============================================================
# Official Temple Information & Committee Management Endpoints
# ============================================================

from app.domain.temple.models import (
    OfficialTempleInfo,
    CommitteeMember,
    DeityInfo,
    SpecialNotice,
    AuditLogEntry,
)
import os
import shutil
from datetime import datetime
from fastapi import File, UploadFile, HTTPException


@router.get("/official-info")
async def get_official_info():
    """Get official temple information, committee members, donation notices, and document details (public)."""
    info = await OfficialTempleInfo.find_one()
    if not info:
        return {"message": "Official temple information not found"}
    return info


@router.put("/official-info")
async def update_official_info(
    update_data: dict,
    admin: User = Depends(get_current_admin),
):
    """
    Update official temple info, committee members, and notices (admin only).
    Logs the update in audit_logs.
    """
    info = await OfficialTempleInfo.find_one()
    if not info:
        info = OfficialTempleInfo()
        await info.insert()

    changes = []

    # Update basic fields
    for field in [
        "heading_kn", "heading_en", "registration_no",
        "address_kn", "address_en", "dharmadarshi_kn", "dharmadarshi_en",
        "dharmadarshi_phone", "manager_kn", "manager_en",
        "bank_account_info_kn", "bank_account_info_en",
        "document_image_url", "document_page1_url", "document_pdf_url",
        "is_document_public"
    ]:
        if field in update_data and getattr(info, field) != update_data[field]:
            changes.append(f"Updated {field}")
            setattr(info, field, update_data[field])

    # Update deities
    if "deities" in update_data and isinstance(update_data["deities"], list):
        info.deities = [DeityInfo(**d) for d in update_data["deities"]]
        changes.append("Updated Parivara Deities")

    # Update special notice
    if "special_notice" in update_data and isinstance(update_data["special_notice"], dict):
        info.special_notice = SpecialNotice(**update_data["special_notice"])
        changes.append("Updated Donation Notice / Special Notice")

    # Update committee members
    if "committee_members" in update_data and isinstance(update_data["committee_members"], list):
        info.committee_members = [CommitteeMember(**m) for m in update_data["committee_members"]]
        changes.append(f"Updated Committee Members ({len(info.committee_members)} entries)")

    # Record audit log entry
    if changes:
        log_entry = AuditLogEntry(
            admin_email=admin.email,
            action="UPDATE_OFFICIAL_INFO",
            details="; ".join(changes),
            timestamp=datetime.utcnow().isoformat(),
        )
        info.audit_logs.insert(0, log_entry)

    await info.save()
    return {"message": "Official temple information updated successfully", "data": info}


@router.post("/official-info/upload")
async def upload_official_document(
    file: UploadFile = File(...),
    doc_type: str = "image",  # 'image' or 'pdf'
    admin: User = Depends(get_current_admin),
):
    """
    Upload a new official document or replace the existing one (admin only).
    """
    info = await OfficialTempleInfo.find_one()
    if not info:
        info = OfficialTempleInfo()
        await info.insert()

    # Determine destination directory in frontend/assets/documents
    base_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "frontend", "assets", "documents")
    os.makedirs(base_dir, exist_ok=True)

    filename = file.filename
    clean_filename = f"upload_{int(datetime.utcnow().timestamp())}_{filename}"
    file_path = os.path.join(base_dir, clean_filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    relative_url = f"/static/assets/documents/{clean_filename}"

    if doc_type == "pdf" or filename.lower().endswith(".pdf"):
        info.document_pdf_url = relative_url
        action_detail = f"Uploaded official PDF document: {filename}"
    else:
        info.document_image_url = relative_url
        action_detail = f"Uploaded official document image: {filename}"

    # Record audit log
    log_entry = AuditLogEntry(
        admin_email=admin.email,
        action="UPLOAD_DOCUMENT",
        details=action_detail,
        timestamp=datetime.utcnow().isoformat(),
    )
    info.audit_logs.insert(0, log_entry)
    await info.save()

    return {
        "message": "Official document uploaded successfully",
        "file_url": relative_url,
        "doc_type": doc_type,
        "data": info
    }


@router.get("/official-info/audit-logs")
async def get_official_info_audit_logs(
    admin: User = Depends(get_current_admin),
):
    """Get audit logs for official temple information updates (admin only)."""
    info = await OfficialTempleInfo.find_one()
    if not info:
        return []
    return info.audit_logs

