"""
Pydantic schemas for donation requests and responses.
"""

from typing import Optional
from pydantic import BaseModel, Field


class DonationCreateRequest(BaseModel):
    """Schema for initiating a donation / creating Razorpay order."""
    amount: int = Field(..., gt=0, description="Amount in INR (rupees)")
    donation_type: str = Field(default="general")
    donor_name: str
    donor_mobile: str
    donor_email: Optional[str] = ""
    donor_address: Optional[str] = ""
    is_anonymous: Optional[bool] = False


class DonationVerifyRequest(BaseModel):
    """Schema for verifying Razorpay payment."""
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
    donation_id: str


class DonationResponse(BaseModel):
    """Schema for donation in history listing."""
    id: str
    amount: int
    donation_type: str
    status: str
    receipt_number: str
    created_at: str
    donor_name: str


class UtrIntimationRequest(BaseModel):
    """Schema for submitting offline UPI UTR reference for verification."""
    donor_name: str
    donor_mobile: str
    amount: int = Field(..., gt=0)
    utr_number: str
    donor_email: Optional[str] = ""
    donation_type: Optional[str] = "general"


class CashfreeVerifyRequest(BaseModel):
    """Schema for verifying Cashfree payment status after return redirect."""
    order_id: str
    donation_id: Optional[str] = None


