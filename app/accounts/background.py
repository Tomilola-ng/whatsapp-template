"""Accounts Background Tasks"""

from datetime import datetime, timedelta, timezone

from app.base.utils import generate_otp, send_email
from app.accounts.emails import activate_account_otp, welcome_email
from app.accounts.utils import get_user_or_404_by_email
from app.config.settings import settings
from app.records.models import OTP
from app.records.enums import OTPPurpose, OTPStatus


async def send_activation_email(email: str):
    """Send account activation OTP email to user."""

    user = await get_user_or_404_by_email(email)

    await OTP.filter(
        account=user, purpose=OTPPurpose.ACCOUNT_VERIFICATION, status=OTPStatus.PENDING
    ).delete()

    otp_code = generate_otp()
    await OTP.create(
        account=user,
        code=otp_code,
        purpose=OTPPurpose.ACCOUNT_VERIFICATION,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
    )

    context = {"first_name": user.first_name,
               "otp": otp_code, "valid_minutes": 5}
    send_email("Your Verification OTP", email,  activate_account_otp(context))


async def send_welcome_email(email: str):
    """Send welcome email to newly activated user."""
    user = await get_user_or_404_by_email(email)
    context = {
        "first_name": user.first_name
    }
    send_email(f"Welcome to {settings.PROJECT_NAME}!", email, welcome_email(context))
