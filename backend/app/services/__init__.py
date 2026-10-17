"""
Business logic services interface.
"""

from app.domain.donations.service import (
    create_donation_order,
    verify_donation_payment,
    generate_receipt_number,
)
from app.domain.auth.service import (
    register_user,
    login_user,
)
from app.domain.admin.service import (
    get_dashboard_stats,
)

__all__ = [
    "create_donation_order",
    "verify_donation_payment",
    "generate_receipt_number",
    "register_user",
    "login_user",
    "get_dashboard_stats",
]
