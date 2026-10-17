"""
Donation API routes.
"""

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from beanie import PydanticObjectId
import io

from datetime import datetime
from app.core.dependencies import get_current_user, get_current_admin
from app.domain.donations.models import Donation
from app.domain.donations.schemas import DonationCreateRequest, DonationVerifyRequest
from app.domain.donations.service import create_donation_order, verify_donation_payment
from app.domain.users.models import User
from app.utils.pdf_receipt import generate_receipt_pdf, generate_donations_report_pdf

router = APIRouter(prefix="/donate", tags=["Donations"])


@router.post("/create-order")
async def create_order(
    data: DonationCreateRequest,
    current_user: User = Depends(get_current_user),
):
    """Create a Razorpay order for donation (authenticated)."""
    result = await create_donation_order(data, str(current_user.id))
    return result


@router.post("/verify")
async def verify_payment(
    data: DonationVerifyRequest,
    current_user: User = Depends(get_current_user),
):
    """Verify Razorpay payment after checkout (authenticated)."""
    result = await verify_donation_payment(data)
    return result


@router.get("/history")
async def donation_history(
    current_user: User = Depends(get_current_user),
):
    """Get donation history for the logged-in user."""
    donations = await Donation.find(
        Donation.user_id == str(current_user.id)
    ).sort("-created_at").to_list()

    return [
        {
            "id": str(d.id),
            "amount": d.amount // 100,  # Convert paise back to rupees
            "donation_type": d.donation_type,
            "status": d.status,
            "receipt_number": d.receipt_number,
            "created_at": d.created_at.isoformat(),
            "donor_name": d.donor_name,
        }
        for d in donations
    ]


@router.get("/receipt/{donation_id}")
async def download_receipt(
    donation_id: str,
    current_user: User = Depends(get_current_user),
):
    """Download PDF receipt for a specific donation."""
    donation = await Donation.get(PydanticObjectId(donation_id))
    if not donation:
        return {"message": "Donation not found"}

    # Security check: user can only download their own receipts
    if donation.user_id != str(current_user.id) and current_user.role != "admin":
        return {"message": "Unauthorized"}

    # Generate PDF
    pdf_buffer = generate_receipt_pdf(donation)

    return StreamingResponse(
        io.BytesIO(pdf_buffer),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=receipt_{donation.receipt_number}.pdf"
        },
    )


@router.get("/all")
async def all_donations(
    admin: User = Depends(get_current_admin),
):
    """Get all donations (admin only)."""
    donations = await Donation.find_all().sort("-created_at").to_list()
    return [
        {
            "id": str(d.id),
            "amount": d.amount // 100,
            "donation_type": d.donation_type,
            "status": d.status,
            "receipt_number": d.receipt_number,
            "created_at": d.created_at.isoformat(),
            "donor_name": d.donor_name,
            "donor_email": d.donor_email,
            "donor_mobile": d.donor_mobile,
            "user_id": d.user_id,
        }
        for d in donations
    ]


@router.get("/export-pdf")
async def export_donations_pdf(
    query: str = "",
    admin: User = Depends(get_current_admin),
):
    """Export all or filtered donations as an official PDF report (admin only)."""
    donations = await Donation.find_all().sort("-created_at").to_list()
    if query:
        q_lower = query.strip().lower()
        donations = [
            d for d in donations
            if q_lower in (d.donor_name or "").lower()
            or q_lower in (d.donor_email or "").lower()
            or q_lower in (d.donor_mobile or "").lower()
            or q_lower in (d.receipt_number or "").lower()
            or q_lower in (d.donation_type or "").lower()
            or q_lower in (d.status or "").lower()
        ]

    pdf_buffer = generate_donations_report_pdf(donations, query=query.strip())
    date_str = datetime.now().strftime("%Y%m%d")

    return StreamingResponse(
        io.BytesIO(pdf_buffer),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=donations_report_{date_str}.pdf"
        },
    )


@router.get("/recent")
async def recent_donations():
    """Get recent completed donations for the live ticker (public)."""
    donations = await Donation.find(
        Donation.status == "completed"
    ).sort("-created_at").limit(30).to_list()

    return [
        {
            "id": str(d.id),
            "amount": d.amount // 100,
            "donation_type": d.donation_type,
            "created_at": d.created_at.isoformat(),
            "donor_name": "Anonymous Devotee" if d.is_anonymous else d.donor_name,
        }
        for d in donations
    ]
