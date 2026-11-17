"""Rate limiting helpers built on slowapi."""

from slowapi import Limiter

from app.base.client_ip import client_ip
from app.config.settings import settings


limiter = Limiter(
    key_func=lambda request: client_ip(request),
    default_limits=[settings.RATE_LIMIT_DEFAULT],
    storage_uri=settings.RATE_LIMIT_STORAGE_URL,
    enabled=settings.RATE_LIMIT_ENABLED,
)


def rate_limit(limit: str):
    """Decorator for route-specific rate-limit overrides."""
    return limiter.limit(limit)
