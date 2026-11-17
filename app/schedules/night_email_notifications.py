"""
Scheduled task for sending nightly email notifications.
"""

import datetime
import asyncio

from app.base.utils import send_email
from app.config.settings import settings


async def night_email_notifications():
    """
    Send nightly email notifications to admins.
    """
    print("Running nightly email notifications...")

    today = datetime.datetime.now().strftime("%Y-%m-%d")

    await asyncio.to_thread(
        send_email,
        subject=f"Daily Admin Stats Report - {today}",
        address=settings.CONTACT_RECIPIENT_EMAIL,
        body="No, notifications to send.",
    )
