"""Customer-service window helpers for free-form outbound sends (in-memory)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.base.converters import utc_now
from app.config.settings import settings

# Single-WABA starter: process-local last inbound times (no DB table this pass).
_LAST_INBOUND: dict[str, datetime] = {}


def _aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def service_window_open(*, last_inbound_at: datetime | None, now: datetime | None = None) -> bool:
    """Meta-style customer service window from trusted last inbound time."""

    if last_inbound_at is None:
        return False
    clock = _aware(now or utc_now())
    inbound = _aware(last_inbound_at)
    hours = max(0.0, float(settings.WHATSAPP_SERVICE_WINDOW_HOURS))
    return inbound + timedelta(hours=hours) >= clock


def record_inbound_service_window(*, msisdn: str, inbound_at: datetime) -> datetime:
    """Advance per-recipient window from a trusted provider inbound timestamp."""

    key = (msisdn or "").strip()
    if not key:
        return inbound_at
    inbound = _aware(inbound_at)
    prior = _LAST_INBOUND.get(key)
    if prior is None or inbound > prior:
        _LAST_INBOUND[key] = inbound
        return inbound
    return prior


def get_service_window_last_inbound(*, msisdn: str) -> datetime | None:
    return _LAST_INBOUND.get((msisdn or "").strip())


def clear_service_window_cache() -> None:
    """Test helper."""

    _LAST_INBOUND.clear()
