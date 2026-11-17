"""Local development outbox for captured email and SMS messages."""

from __future__ import annotations

import re
from collections import deque
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from threading import Lock
from typing import Literal
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query

from app.config.settings import settings

CaptureChannel = Literal["email", "sms"]


@dataclass
class DevOutboxCapture:
    """Captured outbound message visible only in local development."""

    id: str
    channel: CaptureChannel
    recipient: str
    subject: str | None
    body: str
    purpose: str | None
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


_CAPTURES: deque[DevOutboxCapture] = deque(maxlen=500)
_LOCK = Lock()
_OTP_RE = re.compile(r"(?<!\d)(\d{4,8})(?!\d)")
_STRONG_OTP_RE = re.compile(r"<strong>\s*(\d{4,8})\s*</strong>", re.IGNORECASE)


def extract_otp_from_body(body: str) -> str | None:
    """Extract an OTP while ignoring CSS hex colors such as ``#222222``."""
    strong = _STRONG_OTP_RE.search(body or "")
    if strong:
        return strong.group(1)
    for match in _OTP_RE.finditer(body or ""):
        if match.start() > 0 and body[match.start() - 1] == "#":
            continue
        return match.group(1)
    return None


def dev_outbox_available() -> bool:
    """Return whether local capture should be used."""
    return settings.ENVIRONMENT == "local" and settings.DEV_OUTBOX_ENABLED


def capture_email(
    *,
    recipient: str,
    subject: str,
    body: str,
    purpose: str | None = None,
) -> DevOutboxCapture:
    """Capture an email instead of delivering it."""
    return _capture(
        channel="email",
        recipient=recipient,
        subject=subject,
        body=body,
        purpose=purpose,
    )


def capture_sms(
    *,
    recipient: str,
    body: str,
    purpose: str | None = None,
) -> DevOutboxCapture:
    """Capture an SMS instead of delivering it."""
    return _capture(
        channel="sms",
        recipient=recipient,
        subject=None,
        body=body,
        purpose=purpose,
    )


def _capture(
    *,
    channel: CaptureChannel,
    recipient: str,
    subject: str | None,
    body: str,
    purpose: str | None,
) -> DevOutboxCapture:
    item = DevOutboxCapture(
        id=f"DEV_{uuid4().hex}",
        channel=channel,
        recipient=recipient.strip().lower(),
        subject=subject,
        body=body,
        purpose=purpose,
    )
    with _LOCK:
        _CAPTURES.append(item)
    return item


def _latest_capture(recipient: str, purpose: str | None = None) -> DevOutboxCapture | None:
    normalized = recipient.strip().lower()
    with _LOCK:
        captures = list(_CAPTURES)
    for item in reversed(captures):
        if item.recipient != normalized:
            continue
        if purpose is not None and item.purpose != purpose:
            continue
        return item
    return None


router = APIRouter(prefix="/dev/outbox", tags=["Dev Outbox"])


@router.get("/")
async def list_recent_captures(limit: int = Query(default=25, ge=1, le=100)):
    """List recent local captures for debugging."""
    with _LOCK:
        captures = list(_CAPTURES)[-limit:]
    return {"message": "Dev outbox captures", "data": [asdict(item) for item in captures]}


@router.get("/latest-otp")
async def latest_otp(recipient: str, purpose: str | None = None):
    """Return the latest captured OTP for a recipient and optional purpose."""
    item = _latest_capture(recipient, purpose)
    if item is None:
        raise HTTPException(status_code=404, detail="No matching dev outbox capture.")
    otp = extract_otp_from_body(item.body)
    if otp is None:
        raise HTTPException(status_code=404, detail="No OTP found in latest capture.")
    return {
        "message": "Latest OTP retrieved",
        "data": {
            "otp": otp,
            "recipient": item.recipient,
            "purpose": item.purpose,
            "channel": item.channel,
            "created_at": item.created_at,
        },
    }
