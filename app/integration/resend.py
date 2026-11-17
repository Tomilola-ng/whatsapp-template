"""Thin Resend email integration wrapper."""

import resend

from app.config.settings import settings


class ResendConfigurationError(RuntimeError):
    """Raised when Resend is used without required settings."""


class ResendDeliveryError(RuntimeError):
    """Raised when Resend rejects a delivery attempt."""


def send_email_via_resend(*, subject: str, address: str, body: str):
    """Deliver an HTML email through Resend."""
    if not settings.RESEND_API_KEY:
        raise ResendConfigurationError("RESEND_API_KEY is required to send email.")

    resend.api_key = settings.RESEND_API_KEY
    try:
        return resend.Emails.send(
            {
                "from": settings.EMAIL_SENDER,
                "to": [address],
                "subject": subject,
                "html": body,
            }
        )
    except Exception as exc:
        raise ResendDeliveryError(str(exc)) from exc
