"""Failure-isolated starter maintenance orchestration."""

import logging
from collections.abc import Awaitable, Callable
from datetime import timezone

from app.base.converters import utc_now
from app.records.enums import OTPStatus
from app.records.models import OTP

logger = logging.getLogger(__name__)


async def _expire_otps() -> dict:
    expired = await OTP.filter(
        status=OTPStatus.PENDING,
        expires_at__lt=utc_now().astimezone(timezone.utc),
    ).update(status=OTPStatus.EXPIRED)
    return {"expired": expired}


async def _notification_retry() -> dict:
    return {"status": "noop", "detail": "Forks may add durable delivery retry here."}


async def _run_job(name: str, job: Callable[[], Awaitable[dict]]) -> dict:
    try:
        return {"status": "ok", "result": await job()}
    except Exception as exc:
        logger.exception("maintenance_job_failed job=%s", name)
        return {"status": "failed", "error": type(exc).__name__}


async def run_maintenance() -> dict:
    return {
        "otp_expiration": await _run_job("otp_expiration", _expire_otps),
        "notification_retry": await _run_job(
            "notification_retry", _notification_retry
        ),
    }
