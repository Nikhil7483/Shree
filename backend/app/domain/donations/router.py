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
    Marks transaction as 'completed' and generates instant official receipt.
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
        status="completed",
        receipt_number=receipt_number,
        razorpay_order_id=None,
        razorpay_payment_id=f"UTR:{data.utr_number.strip()}",
        youpi_utr=data.utr_number.strip(),
        payment_gateway="direct_upi",
    )
    await donation.insert()
    return {
        "status": "completed",
        "receipt_number": receipt_number,
        "donation_id": str(donation.id),
        "donor_name": donation.donor_name,
        "amount": data.amount,
        "donation_type": donation.donation_type,
        "utr_number": data.utr_number.strip(),
        "download_receipt_url": f"/api/donate/receipt-pdf/{donation.id}",
        "message": "Payment recorded successfully. Official receipt ready."
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
@router.get("/receipt-pdf/{donation_id}")
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
            "payment_gateway": d.payment_gateway or ("youpi" if d.youpi_order_id else "direct_upi"),
            "utr_number": d.youpi_utr or ((d.razorpay_payment_id or "").replace("UTR:", "").replace("YOUPI:", "").strip() if (d.razorpay_payment_id or "").startswith(("UTR:", "YOUPI:")) else (d.razorpay_payment_id or "")),
        }
        for d in donations
    ]


@router.delete("/clear-all")
async def clear_all_donations(
    admin: User = Depends(get_current_admin),
):
    """Delete all donation records (admin only)."""
    await Donation.find_all().delete()
    return {"status": "ok", "message": "All donation records cleared."}


@router.delete("/{donation_id}")
async def delete_donation(
    donation_id: str,
    admin: User = Depends(get_current_admin),
):
    """Delete a specific donation record (admin only)."""
    donation = None
    try:
        donation = await Donation.get(PydanticObjectId(donation_id))
    except Exception:
        pass
    if not donation:
        donation = await Donation.find_one({"receipt_number": donation_id})
    if not donation:
        raise HTTPException(status_code=404, detail="Donation not found")
    await donation.delete()
    return {"status": "ok", "message": f"Donation {donation_id} deleted."}


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

@router.get("/youpi-config-status")
async def youpi_config_status():
    """
    Check if YouPI gateway is configured in backend environment.
    """
    api_url = settings.youpi_api_base_url
    configured = bool(api_url and settings.YOUPI_MERCHANT_ID)
    return {
        "configured": configured,
        "gateway_url": api_url,
        "checkout_url": settings.YOUPI_CHECKOUT_URL or None,
        "public_key": settings.YOUPI_PUBLIC_KEY or None,
    }


@router.post("/youpi-create-order")
async def youpi_create_order(
    request: Request,
    data: DonationCreateRequest,
    current_user: Optional[User] = Depends(get_optional_user),
):
    """
    Initiate a donation order with YouPI-PG.
    Creates a pending donation and calls YouPI Payment API: POST /api/v1/payments.
    """
    api_url = settings.youpi_api_base_url
    merchant_id = settings.YOUPI_MERCHANT_ID

    receipt_number = generate_receipt_number()
    user_id = str(current_user.id) if current_user else "online_donor"
    donor_email = (current_user.email if current_user and not data.donor_email else (data.donor_email or "")).strip()

    # Create pending donation record in MongoDB
    donation = Donation(
        user_id=user_id,
        donor_name=data.donor_name.strip(),
        donor_email=donor_email,
        donor_mobile=data.donor_mobile.strip(),
        donor_address=(data.donor_address or "").strip(),
        amount=int(data.amount * 100),  # rupees to paise
        donation_type=data.donation_type or "general",
        is_anonymous=bool(data.is_anonymous),
        payment_gateway="youpi",
        status="pending",
        receipt_number=receipt_number,
    )
    await donation.insert()

    # Determine return URL for redirect after payment
    base_url = str(request.base_url).rstrip("/")
    if "shreeshanishwara" in base_url or "railway.app" in base_url:
        base_url = "https://shreeshanishwara.up.railway.app"
    return_url = f"{base_url}/donate?order_id={str(donation.id)}"

    # If YouPI gateway is not configured, inform the user to use direct QR
    if not api_url or not merchant_id:
        return {
            "success": False,
            "configured": False,
            "donation_id": str(donation.id),
            "receipt_number": donation.receipt_number,
            "message": "YouPI Gateway server is not configured yet. Devotees can scan the Canara Bank QR code directly.",
            "fallback": {
                "upi_id": "47808680004653@cnrb",
                "account_no": "1516101004653",
                "ifsc": "CNRB0001516",
                "bank_name": "Canara Bank",
            }
        }

    order_id = str(donation.id)
    donation.youpi_order_id = order_id
    await donation.save()

    payload = {
        "orderId": order_id,
        "amount": f"{data.amount:.2f}",
        "currency": "INR",
        "returnUrl": return_url,
    }
    headers = {
        "Content-Type": "application/json",
        "X-Merchant-Id": merchant_id,
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{api_url.rstrip('/')}/api/v1/payments",
                json=payload,
                headers=headers,
            )
            if resp.status_code not in (200, 201):
                print(f"[YouPI Error] API returned status {resp.status_code}: {resp.text}")
                return {
                    "success": False,
                    "configured": True,
                    "donation_id": str(donation.id),
                    "receipt_number": donation.receipt_number,
                    "message": f"YouPI Payment API error ({resp.status_code}). Devotees can scan the official Canara Bank QR code.",
                }

            youpi_data = resp.json()
            donation.youpi_payment_id = youpi_data.get("paymentId")
            await donation.save()

            return {
                "success": True,
                "configured": True,
                "donation_id": str(donation.id),
                "order_id": order_id,
                "payment_id": youpi_data.get("paymentId"),
                "checkout_url": youpi_data.get("checkoutUrl"),
                "status": youpi_data.get("status", "ACTIVE"),
                "receipt_number": donation.receipt_number,
                "amount": data.amount,
            }
    except Exception as exc:
        print(f"[YouPI Exception] Failed to reach YouPI gateway: {exc}")
        return {
            "success": False,
            "configured": True,
            "donation_id": str(donation.id),
            "receipt_number": donation.receipt_number,
            "message": f"Could not reach YouPI Gateway server: {str(exc)}. Please scan the Canara Bank QR code directly.",
        }


@router.post("/youpi-webhook")
async def youpi_webhook(request: Request):
    """
    Receives automated payment verification webhooks from YouPI-PG.
    Follows Part G of the YouPI-PG integration specification:
    1. Reads raw body exactly as received.
    2. Validates HMAC-SHA256 signature (X-Gateway-Signature / X-Gateway-Signature-V2).
    3. Checks deliveryId for idempotency / duplicate prevention.
    4. Finds donation by orderId.
    5. Validates amount (amountPaise == donation.amount).
    6. Prevents duplicate UTR misuse.
    7. Marks donation completed and assigns receipt number.
    """
    raw_body = await request.body()
    signature_header = (
        request.headers.get("x-gateway-signature")
        or request.headers.get("X-Gateway-Signature")
        or request.headers.get("x-gateway-signature-v2")
        or request.headers.get("X-Gateway-Signature-V2")
        or ""
    )

    # 1. Verify HMAC signature if webhook secret is configured
    if settings.YOUPI_WEBHOOK_SECRET:
        secret = settings.YOUPI_WEBHOOK_SECRET.encode("utf-8")
        computed_sig = hmac.new(secret, raw_body, hashlib.sha256).hexdigest()
        expected_prefixed = f"sha256={computed_sig}"

        timestamp = (
            request.headers.get("x-gateway-timestamp")
            or request.headers.get("X-Gateway-Timestamp")
            or ""
        )
        computed_v2 = ""
        if timestamp:
            computed_v2 = hmac.new(secret, f"{timestamp}.".encode("utf-8") + raw_body, hashlib.sha256).hexdigest()

        is_valid = (
            hmac.compare_digest(signature_header, expected_prefixed)
            or hmac.compare_digest(signature_header, computed_sig)
            or (computed_v2 and (hmac.compare_digest(signature_header, f"sha256={computed_v2}") or hmac.compare_digest(signature_header, computed_v2)))
        )

        if not is_valid:
            print("[YouPI Webhook] Invalid signature received.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook signature",
            )

    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    event = (
        payload.get("event")
        or request.headers.get("x-gateway-event")
        or request.headers.get("X-Gateway-Event")
        or ""
    ).upper()

    order_id = payload.get("orderId") or payload.get("merchantRefId") or payload.get("order_id")
    payment_id = payload.get("paymentId") or payload.get("payment_id") or ""
    utr = payload.get("utr") or ""
    amount_paise = payload.get("amountPaise")
    delivery_id = (
        payload.get("deliveryId")
        or request.headers.get("x-gateway-delivery-id")
        or request.headers.get("X-Gateway-Delivery-Id")
        or ""
    )

    print(f"[YouPI Webhook] Event: {event}, Order ID: {order_id}, Payment ID: {payment_id}, UTR: {utr}")

    # Deduplication check: if delivery_id was already processed
    if delivery_id:
        existing_delivery = await Donation.find_one({"youpi_delivery_id": delivery_id})
        if existing_delivery and existing_delivery.status == "completed":
            print(f"[YouPI Webhook] Delivery {delivery_id} already processed.")
            return {"received": True, "already_processed": True}

    # Only process successful credit events
    if event in ["SUCCESS", "OBSERVED_SUCCESS", "RECONCILED", "PAID"]:
        donation = None
        if order_id:
            try:
                donation = await Donation.get(PydanticObjectId(order_id))
            except Exception:
                pass

            if not donation:
                donation = await Donation.find_one({"receipt_number": order_id})
            if not donation:
                donation = await Donation.find_one({"youpi_order_id": order_id})
            if not donation:
                donation = await Donation.find_one({"razorpay_order_id": order_id})

        if not donation and utr:
            donation = await Donation.find_one({"youpi_utr": utr})
        if not donation and payment_id:
            donation = await Donation.find_one({"youpi_payment_id": payment_id})

        if not donation:
            print(f"[YouPI Webhook] No matching donation found for order: {order_id}")
            return {"received": True, "status": "order_not_found"}

        if donation.status == "completed":
            if delivery_id and not donation.youpi_delivery_id:
                donation.youpi_delivery_id = delivery_id
                await donation.save()
            return {"received": True, "already_completed": True, "receipt_number": donation.receipt_number}

        # Amount validation
        if amount_paise is not None:
            try:
                expected_paise = int(amount_paise)
                if donation.amount != expected_paise:
                    print(f"[YouPI Webhook WARNING] Amount mismatch! Donation: {donation.amount} paise vs Webhook: {expected_paise} paise")
                    return {"received": True, "warning": "amount_mismatch"}
            except Exception:
                pass

        # Duplicate UTR check across different completed donations
        if utr:
            utr_used = await Donation.find_one({
                "youpi_utr": utr,
                "status": "completed",
                "_id": {"$ne": donation.id}
            })
            if utr_used:
                print(f"[YouPI Webhook WARNING] UTR {utr} already used for donation {utr_used.id}!")
                return {"received": True, "warning": "duplicate_utr"}

        # Mark donation completed
        donation.status = "completed"
        donation.payment_gateway = "youpi"
        if utr:
            donation.youpi_utr = str(utr).strip()
            donation.razorpay_payment_id = f"UTR:{utr}"
        if payment_id:
            donation.youpi_payment_id = str(payment_id).strip()
        if delivery_id:
            donation.youpi_delivery_id = str(delivery_id).strip()
        if not donation.receipt_number:
            donation.receipt_number = generate_receipt_number()

        await donation.save()
        print(f"[YouPI Webhook] Donation {donation.id} marked COMPLETED. Receipt: {donation.receipt_number}, UTR: {utr}")

        return {
            "received": True,
            "status": "completed",
            "donation_id": str(donation.id),
            "receipt_number": donation.receipt_number,
        }

    elif event in ["FAILED", "EXPIRED", "CANCELLED"]:
        if order_id:
            try:
                donation = await Donation.get(PydanticObjectId(order_id))
                if donation and donation.status == "pending":
                    donation.status = event.lower()
                    await donation.save()
            except Exception:
                pass

    return {"received": True, "event": event}


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
        donation = await Donation.find_one({"youpi_order_id": donation_id})

    if not donation:
        raise HTTPException(status_code=404, detail="Donation not found")

    return {
        "donation_id": str(donation.id),
        "status": donation.status,
        "receipt_number": donation.receipt_number,
        "amount": donation.amount // 100,
        "donor_name": donation.donor_name,
        "donation_type": donation.donation_type,
        "is_completed": donation.status == "completed",
        "utr": donation.youpi_utr or "",
        "download_receipt_url": f"/api/donate/receipt-pdf/{donation.id}",
    }

