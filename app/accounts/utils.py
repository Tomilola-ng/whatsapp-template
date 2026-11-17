"""
Shared utilities for the accounts module.
"""

from datetime import datetime, timezone
import hashlib
import hmac
import re

from fastapi import HTTPException
from fastapi.security import OAuth2PasswordBearer
from starlette.requests import Request

from app.accounts.models import Account
from app.base.client_ip import client_ip
from app.records.models import OTP
from app.records.enums import OTPPurpose, OTPStatus
from app.config.settings import settings

USERNAME_RE = re.compile(r"^[a-z0-9_]{3,32}$")


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False)


async def get_user_by_email_or_none(email: str) -> Account | None:
    """Fetch Account by normalized email or return None."""
    return await Account.filter(email=str(email).strip().lower()).first()


async def get_user_or_404_by_email(email: str) -> Account:
    """Fetch Account by email field or 404."""
    user = await get_user_by_email_or_none(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return user


async def get_valid_otp_or_error(
    account: Account,
    otp_code: str,
    *,
    purpose: OTPPurpose = OTPPurpose.ACCOUNT_VERIFICATION,
    require_reset_password: bool = False,
) -> OTP:
    """Validate OTP; raise error if invalid/expired."""
    if require_reset_password:
        purpose = OTPPurpose.PASSWORD_RESET
    otp = await OTP.filter(
        account=account, purpose=purpose, status=OTPStatus.PENDING
    ).order_by("-created_at").first()
    if not otp:
        raise HTTPException(status_code=400, detail="Invalid or expired code.")

    if otp.attempts >= otp.max_attempts:
        otp.status = OTPStatus.EXPIRED
        await otp.save()
        raise HTTPException(status_code=400, detail="Invalid or expired code.")

    expected_hash = hmac.new(
        settings.OTP_HMAC_SECRET.encode(),
        otp_code.encode(),
        hashlib.sha256,
    ).hexdigest()
    legacy_match = otp.code == otp_code
    is_valid = legacy_match or bool(otp.code_hash and hmac.compare_digest(otp.code_hash, expected_hash))
    if not is_valid:
        otp.attempts += 1
        if otp.attempts >= otp.max_attempts:
            otp.status = OTPStatus.EXPIRED
        await otp.save()
        raise HTTPException(status_code=400, detail="Invalid or expired code.")

    now_utc = datetime.now(timezone.utc)
    expires_utc = (
        otp.expires_at.replace(tzinfo=timezone.utc)
        if otp.expires_at.tzinfo is None
        else otp.expires_at.astimezone(timezone.utc)
    )
    if expires_utc <= now_utc:
        otp.status = OTPStatus.EXPIRED
        await otp.save()
        raise HTTPException(status_code=400, detail="Invalid or expired code.")

    return otp


def hash_otp_code(otp_code: str) -> str:
    """Hash an OTP with the application secret for at-rest storage."""
    return hmac.new(
        settings.OTP_HMAC_SECRET.encode(),
        otp_code.encode(),
        hashlib.sha256,
    ).hexdigest()


def hash_setup_code(code: str) -> str:
    """Hash an opaque admin password-setup code for at-rest storage."""
    return hmac.new(
        settings.OTP_HMAC_SECRET.encode(),
        code.encode(),
        hashlib.sha256,
    ).hexdigest()


def apply_partial_update(model, fields: dict) -> None:
    """Apply dict fields to model instance."""
    for key, value in fields.items():
        setattr(model, key, value)


def normalize_username(raw: str) -> str:
    return raw.strip().lower()


def validate_username(raw: str) -> str:
    value = normalize_username(raw)
    if not USERNAME_RE.fullmatch(value):
        raise ValueError("invalid_username")
    return value


def validate_display_name(raw: str) -> str:
    value = " ".join(raw.strip().split())
    if not value or len(value) > 80:
        raise ValueError("invalid_display_name")
    return value


def client_login_location(request: Request) -> dict[str, str | None]:
    """Best-effort IP and User-Agent for the current request."""
    return {
        "ip": client_ip(request),
        "user_agent": request.headers.get("user-agent"),
    }
