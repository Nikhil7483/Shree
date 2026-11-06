"""
Donation document model for MongoDB via Beanie ODM.
"""

from datetime import datetime, timezone
from typing import Optional

from beanie import Document
from pydantic import Field


class Donation(Document):
    """Represents a donation transaction."""

    user_id: str  # References User document ID
    donor_name: str
    donor_email: str
    donor_mobile: str
    donor_address: Optional[str] = ""
    amount: int  # Amount in paise (e.g., 10000 = ₹100)
    donation_type: str = "general"  # general, annadanam, temple_development, festival, goshala
    is_anonymous: bool = False
    razorpay_order_id: Optional[str] = None
    razorpay_payment_id: Optional[str] = None
    razorpay_signature: Optional[str] = None
    cashfree_order_id: Optional[str] = None
    cashfree_payment_id: Optional[str] = None
    payment_gateway: Optional[str] = None
    status: str = "pending"  # pending, completed, failed
    receipt_number: str = ""
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    class Settings:
        name = "donations"
