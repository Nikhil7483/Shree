"""
Donation API routes.
"""

from typing import Optional
import hmac
import hashlib
import json
import io
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from beanie import PydanticObjectId
import httpx

from app.core.config import get_settings
from app.core.dependencies import get_current_user, get_current_admin, get_optional_user
from app.domain.donations.models import Donation
from app.domain.donations.schemas import DonationCreateRequest, DonationVerifyRequest, UtrIntimationRequest, CashfreeVerifyRequest
from app.domain.donations.service import (
    create_donation_order,
    verify_donation_payment,
    generate_receipt_number,
    create_cashfree_order,
    verify_cashfree_order,
    verify_cashfree_signature,
)
from app.domain.users.models import User
from app.utils.pdf_receipt import generate_receipt_pdf, generate_donations_report_pdf

settings = get_settings()
router = APIRouter(prefix="/donate", tags=["Donations"])


@router.post("/submit-utr")
async def submit_utr(
    data: UtrIntimationRequest,
    current_user: Optional[User] = Depends(get_optional_user),
):
    """
    Record an offline direct UPI or bank transfer reference.
    Marks transaction as 'pending_verification' for administrator review.
    """
    receipt_number = generate_receipt_number()
    user_id = str(current_user.id) if current_user else "direct_upi_donor"
    donor_email = (current_user.email if current_user and not data.donor_email else (data.donor_email or "")).strip()

    donation = Donation(
        user_id=user_id,
        donor_name=data.donor_name.strip(),
        donor_email=donor_email,
        donor_mobile=data.donor_mobile.strip(),
        donor_address="",
        amount=int(data.amount * 100),  # rupees to paise
        donation_type=data.donation_type or "general",
        is_anonymous=False,
        status="pending_verification",
        receipt_number=receipt_number,
        razorpay_order_id=None,
        razorpay_payment_id=f"UTR:{data.utr_number.strip()}",
    )
    await donation.insert()
    return {
        "status": "pending_verification",
        "receipt_number": receipt_number,
        "donation_id": str(donation.id),
        "message": "Transaction reference recorded. Status: Pending Verification."
    }


@router.post("/create-order")
async def create_order(
    data: DonationCreateRequest,
    current_user: Optional[User] = Depends(get_optional_user),
):
    """Create a payment order for donation."""
    user_id = str(current_user.id) if current_user else "online_donor"
    result = await create_donation_order(data, user_id)
    return result


@router.post("/verify")
async def verify_payment(
    data: DonationVerifyRequest,
    current_user: Optional[User] = Depends(get_optional_user),
):
    """Verify payment and mark donation complete."""
    result = await verify_donation_payment(data)
    return result


@router.post("/cashfree-create-order")
async def cashfree_create_order(
    request: Request,
    data: DonationCreateRequest,
    current_user: Optional[User] = Depends(get_optional_user),
):
    """
    Create a Cashfree payment order using official APIs.
    Returns payment_session_id and hosted_url to redirect user to Cashfree Hosted Checkout.
    """
    user_id = str(current_user.id) if current_user else "online_donor"
    # Resolve base URL from request or fallback to production
    base_url = str(request.base_url).rstrip("/")
    if "shreeshanishwara" in base_url or "railway.app" in base_url:
        base_url = "https://shreeshanishwara.up.railway.app"
    result = await create_cashfree_order(data, user_id, base_url=base_url)
    return result


@router.post("/cashfree-verify")
async def cashfree_verify_payment(
    data: CashfreeVerifyRequest,
    current_user: Optional[User] = Depends(get_optional_user),
):
    """
    Verify payment status with Cashfree APIs securely from backend.
    """
    result = await verify_cashfree_order(data.order_id, data.donation_id)
    return result


@router.post("/cashfree-webhook")
async def cashfree_webhook(request: Request):
    """
    Cashfree webhook endpoint with HMAC-SHA256 signature verification.
    """
    timestamp = request.headers.get("x-webhook-timestamp", "")
    signature = request.headers.get("x-webhook-signature", "")
    raw_body_bytes = await request.body()
    raw_body_str = raw_body_bytes.decode("utf-8")

    # Verify signature
    is_valid = verify_cashfree_signature(timestamp, raw_body_str, signature)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Cashfree webhook signature",
        )

    try:
        payload = json.loads(raw_body_str)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    data = payload.get("data", {})
    order_data = data.get("order", {})
    payment_data = data.get("payment", {})
    order_id = order_data.get("order_id")

    if not order_id:
        return {"status": "ignored", "reason": "No order_id in webhook"}

    order_status = order_data.get("order_status", "").upper()
    payment_status = payment_data.get("payment_status", "").upper()

    if order_status == "PAID" or payment_status == "SUCCESS":
        donation = await Donation.find_one({"cashfree_order_id": order_id})
        if donation and donation.status != "completed":
            donation.status = "completed"
            cf_pay_id = payment_data.get("cf_payment_id")
            if cf_pay_id:
                donation.cashfree_payment_id = str(cf_pay_id)
            if not donation.receipt_number:
                donation.receipt_number = generate_receipt_number()
            await donation.save()
            print(f"[Cashfree Webhook] Order {order_id} marked as completed.")

    return {"status": "received", "order_id": order_id}


@router.get("/history")
async def donation_history(
    current_user: User = Depends(get_current_user),
):
    """Get donation history for the logged-in user."""
    donations = await Donation.find(
        {"user_id": str(current_user.id)}
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
    token: Optional[str] = None,
    current_user: Optional[User] = Depends(get_optional_user),
):
    """Download PDF receipt for a specific donation."""
    from app.core.security import decode_access_token

    # Check query param token if header was not provided
    if not current_user and token:
        try:
            payload = decode_access_token(token)
            if payload and payload.get("sub"):
                current_user = await User.find_one({"email": payload.get("sub")})
        except Exception:
            pass

    donation = None
    try:
        donation = await Donation.get(PydanticObjectId(donation_id))
    except Exception:
        pass
    if not donation:
        donation = await Donation.find_one({"receipt_number": donation_id})

    if not donation:
        raise HTTPException(status_code=404, detail="Donation not found")

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
            "utr_number": (d.razorpay_payment_id or "").replace("UTR:", "").strip() if (d.razorpay_payment_id or "").startswith("UTR:") else (d.razorpay_payment_id or ""),
        }
        for d in donations
    ]


@router.post("/approve/{donation_id}")
async def approve_donation(
    donation_id: str,
    admin: User = Depends(get_current_admin),
):
    """
    Approve a pending donation after administrator verification of bank credit.
    Updates status to 'completed' and ensures receipt number exists.
    """
    try:
        obj_id = PydanticObjectId(donation_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid donation ID format",
        )

    donation = await Donation.get(obj_id)
    if not donation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Donation record not found",
        )

    donation.status = "completed"
    if not donation.receipt_number:
        donation.receipt_number = generate_receipt_number()
    await donation.save()

    return {
        "status": "completed",
        "donation_id": str(donation.id),
        "receipt_number": donation.receipt_number,
        "donor_name": donation.donor_name,
        "amount": donation.amount // 100,
        "message": f"Payment of ₹{donation.amount // 100} by {donation.donor_name} approved successfully.",
    }


@router.post("/reject/{donation_id}")
async def reject_donation(
    donation_id: str,
    admin: User = Depends(get_current_admin),
):
    """
    Reject an invalid or unverified donation reference.
    """
    try:
        obj_id = PydanticObjectId(donation_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid donation ID format",
        )

    donation = await Donation.get(obj_id)
    if not donation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Donation record not found",
        )

    donation.status = "rejected"
    await donation.save()

    return {
        "status": "rejected",
        "donation_id": str(donation.id),
        "donor_name": donation.donor_name,
        "message": f"Payment reference for {donation.donor_name} marked as rejected.",
    }


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
        {"status": "completed"}
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


# ==============================================================================
# YouPI-PG 0% Fee Automated Gateway Endpoints
# ==============================================================================

@router.post("/youpi-webhook")
async def youpi_webhook(request: Request):
    """
    Receives automated payment verification webhooks from YouPI-PG.
    Validates HMAC-SHA256 signature and automatically approves donation.
    """
    raw_body = await request.body()
    signature_header = request.headers.get("x-gateway-signature", "")

    # 1. Verify HMAC signature if webhook secret is configured
    if settings.YOUPI_WEBHOOK_SECRET:
        secret = settings.YOUPI_WEBHOOK_SECRET.encode("utf-8")
        computed_sig = hmac.new(secret, raw_body, hashlib.sha256).hexdigest()
        expected = f"sha256={computed_sig}"
        # Also check without prefix if gateway sends raw hex
        if not (hmac.compare_digest(signature_header, expected) or hmac.compare_digest(signature_header, computed_sig)):
            print("[YouPI Webhook] Invalid signature received.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook signature",
            )

    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    event = payload.get("event") or request.headers.get("x-gateway-event", "")
    order_id = payload.get("orderId") or payload.get("merchantRefId")
    payment_id = payload.get("paymentId") or payload.get("utr", "")

    print(f"[YouPI Webhook] Event: {event}, Order ID: {order_id}, Payment ID: {payment_id}")

    # 2. Automatically mark donation as completed upon observed success or reconciliation
    if event in ["OBSERVED_SUCCESS", "RECONCILED", "SUCCESS"]:
        donation = None
        # Try matching by MongoDB ObjectId
        try:
            donation = await Donation.get(PydanticObjectId(order_id))
        except Exception:
            pass

        # Try matching by receipt number
        if not donation and order_id:
            donation = await Donation.find_one({"receipt_number": order_id})

        # Try matching by payment ID or UTR
        if not donation and payment_id:
            donation = await Donation.find_one({"razorpay_payment_id": f"UTR:{payment_id}"})

        if donation:
            donation.status = "completed"
            donation.razorpay_payment_id = f"YOUPI:{payment_id or 'auto'}"
            if not donation.receipt_number:
                donation.receipt_number = generate_receipt_number()
            await donation.save()
            print(f"[YouPI Webhook] Donation {donation.id} automatically marked COMPLETED. Receipt: {donation.receipt_number}")
            return {
                "status": "received",
                "message": "Donation verified and approved",
                "receipt_number": donation.receipt_number,
            }
        else:
            print(f"[YouPI Webhook] No matching donation found for order: {order_id}")

    return {"status": "received", "event": event}


@router.get("/status/{donation_id}")
async def check_donation_status(donation_id: str):
    """
    Public polling endpoint for frontend to check if donation has been confirmed.
    """
    donation = None
    try:
        donation = await Donation.get(PydanticObjectId(donation_id))
    except Exception:
        pass

    if not donation:
        donation = await Donation.find_one({"receipt_number": donation_id})

    if not donation:
        raise HTTPException(status_code=404, detail="Donation not found")

    return {
        "donation_id": str(donation.id),
        "status": donation.status,
        "receipt_number": donation.receipt_number,
        "amount": donation.amount // 100,
        "is_completed": donation.status == "completed",
    }

