"""Utility Code"""

# pylint: disable=broad-exception-caught

import re
import secrets
import uuid
from importlib.metadata import PackageNotFoundError, version

from app.config.settings import settings
from app.integration.dev_outbox import capture_email, capture_sms, dev_outbox_available
from app.integration.resend import send_email_via_resend
from app.integration.termii import send_sms_via_provider


# ─────────────────────────────────────────────────────────────
# Prefixed primary-key helpers
# ─────────────────────────────────────────────────────────────
#
# Every UUID-style primary key in the database is stored as a
# `varchar` shaped like `<PREFIX>_<uuid4 hex>` (e.g. `ACC_5e8f6c…`).
# The 3-letter ALL-CAPS prefix lets you tell at a glance what kind
# of record an ID belongs to without inspecting the table.

# Max length for any prefixed ID column. 4 (prefix) + 1 (`_`) + 32 (hex) = 37.
# We round up to 50 for headroom on future longer prefixes.
PREFIXED_ID_MAX_LENGTH = 50


class IDPrefix:
    """3-letter ALL-CAPS prefixes for every prefixed-ID table.

    Keep these in sync with the prefixes used in each app's models.py.
    """

    # Accounts / Auth
    ACCOUNT = "ACC"
    OTP = "OTP"
    PERMISSION = "PRM"
    ACCESS_ROLE = "ACR"
    ACCESS_ROLE_PERMISSION = "ARP"
    ACCOUNT_ACCESS_ROLE = "AAR"
    ACCOUNT_PERMISSION = "APC"
    ACCOUNT_PREFERENCE = "APR"

    # Providers
    PROVIDER_PROFILE = "PRV"
    PROVIDER_KYC = "KYC"
    PROVIDER_BAN = "BAN"
    PROVIDER_CANCELLATION_LOG = "PCL"
    PREMBLY_NIN_CACHE = "PNC"
    PAYSTACK_BANK_RESOLVE_CACHE = "PBR"

    # Orders
    ORDER = "ORD"
    ORDER_STATUS_EVENT = "OSE"
    ORDER_ASSIGNMENT = "OAS"
    FARE_ESTIMATE = "FAR"

    # Ratings & Reviews
    RATING = "RAT"

    # Payments / Payouts / Invoices
    PAYMENT = "PMT"
    PAYOUT = "POU"
    INVOICE = "INV"

    # Communication
    CHAT_THREAD = "CHT"
    CHAT_MESSAGE = "MSG"

    # Notifications
    NOTIFICATION = "NTF"
    AUDIT_LOG = "AUD"
    CLIENT_ERROR_LOG = "CEL"
    APP_RELEASE = "REL"

    # Disputes
    DISPUTE = "DSP"


def generate_prefixed_id(prefix: str) -> str:
    """Generate a prefixed primary-key string like ``ACC_5e8f6c…``.

    Args:
        prefix: 3-4 letter ALL-CAPS code identifying the record type.
            Use a constant from :class:`IDPrefix` so prefixes stay
            consistent across the codebase.

    Returns:
        ``"{PREFIX}_{uuid4 hex}"`` — e.g. ``"ACC_5e8f6c1b9d4a4e7c8b2a1f0d9c8b7a6f"``.
    """
    return f"{prefix}_{uuid.uuid4().hex}"


def make_id(prefix: str) -> str:
    """Backward-compatible helper for generating prefixed IDs."""
    return generate_prefixed_id(prefix)


def make_id_default(prefix: str):
    """Build a zero-arg callable suitable for a Tortoise ``default=``.

    Tortoise's ``Model.describe()`` (used by Aerich during
    ``init-db`` / ``migrate``) reads ``default.__module__`` and
    ``default.__name__`` to serialize the field. ``functools.partial``
    objects don't expose ``__name__``, which crashes Aerich. This helper
    wraps :func:`generate_prefixed_id` in a real function with a stable,
    prefix-derived name so migrations serialize cleanly.

    Args:
        prefix: 3-4 letter ALL-CAPS code from :class:`IDPrefix`.

    Returns:
        A no-argument function returning a freshly generated
        ``"{PREFIX}_{uuid4 hex}"`` string each time it's called.
    """
    def _default() -> str:
        return generate_prefixed_id(prefix)

    _default.__name__ = f"id_default_{prefix.lower()}"
    _default.__qualname__ = _default.__name__
    _default.__module__ = __name__
    return _default


def send_email(subject: str, address: str, body: str):
    """Send an email and handle errors."""
    if dev_outbox_available():
        return capture_email(
            recipient=address,
            subject=subject,
            body=body,
            purpose=_email_subject_to_purpose(subject),
        )
    try:
        response = send_email_via_resend(subject=subject, address=address, body=body)
        print("Email response:", response)
        return response
    except Exception as e:
        print(f"Error sending email: {e}")
        return None


def send_sms(recipient: str, body: str, purpose: str | None = None):
    """Send SMS or capture it in the local dev outbox."""
    if dev_outbox_available():
        return capture_sms(recipient=recipient, body=body, purpose=purpose)
    try:
        return send_sms_via_provider(recipient=recipient, body=body)
    except Exception as e:
        print(f"Error sending SMS: {e}")
        return None


def _email_subject_to_purpose(subject: str) -> str | None:
    normalized = subject.lower()
    if "login" in normalized or "sign-in" in normalized or "sign in" in normalized:
        return "login_verification"
    if "verification" in normalized or "activate" in normalized:
        return "account_verification"
    if "reset" in normalized:
        return "password_reset"
    return None


def generate_otp(length: int = 6) -> str:
    """
    Generate a random OTP of the specified length.

    Args:
        length (int): The length of the OTP. Defaults to 6.

    Returns:
        str: The generated OTP.
    """
    return "".join(secrets.choice("0123456789") for _ in range(length))


def generate_slug(text: str) -> str:
    """
    Generate a URL-friendly slug from the provided text.

    Args:
        text (str): The text to generate the slug from.

    Returns:
        str: The generated slug.
    """
    slug = text.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    # Ensure uniqueness or further processing if needed
    return slug


def normalise_msisdn(msisdn: str) -> str:
    """Normalize Nigerian phone numbers into E.164 format."""
    digits = re.sub(r"\D+", "", msisdn or "")
    if not digits:
        raise ValueError("Phone number is required.")
    if digits.startswith("234") and len(digits) == 13:
        return f"+{digits}"
    if digits.startswith("0") and len(digits) == 11:
        return f"+234{digits[1:]}"
    if len(digits) == 10:
        return f"+234{digits}"
    raise ValueError(
        "Unsupported phone number format. Use a valid Nigerian number such as 08012345678 or +2348012345678."
    )


def health_check() -> dict:
    """Return basic API liveness and version metadata."""
    try:
        app_version = version("fastapi-base-template")
    except PackageNotFoundError:
        app_version = settings.APP_VERSION

    return {
        "message": "Healthy",
        "data": {
            "project": settings.PROJECT_NAME,
            "environment": settings.ENVIRONMENT,
            "version": app_version,
        },
    }
