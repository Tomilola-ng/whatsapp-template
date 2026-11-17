"""Trusted client IP resolution for rate limiting and audit metadata."""

from starlette.requests import Request

from app.config.settings import settings


def client_ip(request: Request) -> str:
    """Resolve the client IP, trusting forwarded headers only from known proxies."""
    direct_ip = request.client.host if request.client else "unknown"
    if direct_ip not in settings.TRUSTED_PROXY_IPS:
        return direct_ip

    xff = request.headers.get("x-forwarded-for") or request.headers.get("X-Forwarded-For")
    if xff:
        return xff.split(",")[0].strip() or direct_ip
    return direct_ip
