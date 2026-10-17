"""
Admin dashboard business logic — aggregation queries.
"""

from datetime import datetime, timezone, timedelta
from app.domain.donations.models import Donation
from app.domain.users.models import User


async def get_dashboard_stats() -> dict:
    """
    Compute admin dashboard statistics:
    - Total donations (count and sum)
    - Today's donations
    - This month's donations
    - Total users
    - Recent donations (last 10)
    """
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # All completed donations
    all_donations = await Donation.find(
        Donation.status == "completed"
    ).to_list()

    total_amount = sum(d.amount for d in all_donations) // 100  # paise → rupees
    total_count = len(all_donations)

    # Today's donations
    today_donations = [
        d for d in all_donations if d.created_at >= today_start
    ]
    today_amount = sum(d.amount for d in today_donations) // 100
    today_count = len(today_donations)

    # Monthly donations
    month_donations = [
        d for d in all_donations if d.created_at >= month_start
    ]
    monthly_amount = sum(d.amount for d in month_donations) // 100
    monthly_count = len(month_donations)

    # Total users
    total_users = await User.find(User.role == "user").count()

    # Recent donations (last 10)
    recent = await Donation.find(
        Donation.status == "completed"
    ).sort("-created_at").limit(10).to_list()

    recent_list = [
        {
            "id": str(d.id),
            "donor_name": d.donor_name,
            "amount": d.amount // 100,
            "donation_type": d.donation_type,
            "receipt_number": d.receipt_number,
            "created_at": d.created_at.isoformat(),
        }
        for d in recent
    ]

    return {
        "total_donations": {"count": total_count, "amount": total_amount},
        "today_donations": {"count": today_count, "amount": today_amount},
        "monthly_donations": {"count": monthly_count, "amount": monthly_amount},
        "total_users": total_users,
        "recent_donations": recent_list,
    }
