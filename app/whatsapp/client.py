"""Construct and attach the single-number PyWa client to FastAPI."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from urllib.parse import urlparse

from pywa_async import WhatsApp

from app.config.settings import settings
from app.whatsapp.services.callbacks import register_callback_handlers
from app.whatsapp.services.flows import register_flow_handlers
from app.whatsapp.services.handlers import register_message_handlers
from app.whatsapp.services.statuses import register_status_handlers
from app.whatsapp.shared import get_whatsapp_client_optional, set_whatsapp_client

if TYPE_CHECKING:
    from fastapi import FastAPI

logger = logging.getLogger(__name__)

_whatsapp: WhatsApp | None = None


def get_attached_whatsapp() -> WhatsApp | None:
    return _whatsapp


def _public_callback_origin() -> str | None:
    """PyWa expects ``callback_url`` to be the public *origin only*.

    It appends ``webhook_endpoint`` itself. Passing a full webhook URL doubles the path.
    """

    raw = (settings.WHATSAPP_CALLBACK_URL or settings.APP_BASE_URL or "").strip()
    if not raw:
        return None
    endpoint = (settings.WHATSAPP_WEBHOOK_ENDPOINT or "").rstrip("/")
    trimmed = raw.rstrip("/")
    if endpoint and trimmed.endswith(endpoint):
        trimmed = trimmed[: -len(endpoint)].rstrip("/")
    parsed = urlparse(trimmed if "://" in trimmed else f"https://{trimmed}")
    if parsed.scheme not in {"https"}:
        print(
            f"[whatsapp] skip PyWa auto-register: origin must be https "
            f"(got {trimmed!r}); configure Meta webhook manually",
            flush=True,
        )
        return None
    host = (parsed.hostname or "").lower()
    if host in {"localhost", "127.0.0.1"} or host.endswith(".local"):
        print(
            f"[whatsapp] skip PyWa auto-register: non-public host {host!r}; "
            "configure Meta webhook manually",
            flush=True,
        )
        return None
    return f"{parsed.scheme}://{parsed.netloc}"


def _register_raw_debug_handler(wa: WhatsApp) -> None:
    """Log every webhook payload so PaaS logs show POSTs even when filters drop them."""

    @wa.on_raw_update()
    async def on_raw_update(_client: WhatsApp, update: object) -> None:
        field = getattr(update, "field", None)
        payload_id = getattr(update, "id", None)
        value = getattr(update, "value", None) or {}
        meta = value.get("metadata") if isinstance(value, dict) else None
        phone = (meta or {}).get("phone_number_id") if isinstance(meta, dict) else None
        has_messages = isinstance(value, dict) and bool(value.get("messages"))
        print(
            f"[whatsapp] RAW webhook field={field!r} payload_id={payload_id!r} "
            f"phone_id={phone!r} messages={has_messages}",
            flush=True,
        )


def _register_webhook_access_log(app: FastAPI, webhook_endpoint: str) -> None:
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.requests import Request

    class WhatsAppWebhookAccessLog(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):
            path = request.url.path
            if path.rstrip("/") == webhook_endpoint.rstrip("/"):
                print(
                    f"[whatsapp] HTTP {request.method} {path} "
                    f"query={dict(request.query_params)!r}",
                    flush=True,
                )
            return await call_next(request)

    app.add_middleware(WhatsAppWebhookAccessLog)


def attach_whatsapp(app: FastAPI) -> WhatsApp | None:
    """Attach PyWa to ``app`` when WhatsApp is enabled. Idempotent."""

    global _whatsapp
    if not settings.WHATSAPP_ENABLED:
        set_whatsapp_client(None)
        _whatsapp = None
        return None
    if _whatsapp is not None:
        return _whatsapp

    webhook_endpoint = settings.WHATSAPP_WEBHOOK_ENDPOINT or "/api/v1/webhooks/whatsapp"
    callback_origin = _public_callback_origin()
    api_version = settings.WHATSAPP_GRAPH_VERSION or None
    kwargs: dict = {
        "phone_id": settings.WHATSAPP_PHONE_NUMBER_ID,
        "token": settings.WHATSAPP_ACCESS_TOKEN,
        "server": app,
        "webhook_endpoint": webhook_endpoint,
        "verify_token": settings.WHATSAPP_VERIFY_TOKEN,
        "app_id": settings.WHATSAPP_APP_ID,
        "app_secret": settings.WHATSAPP_APP_SECRET,
        "waba_id": settings.WHATSAPP_BUSINESS_ACCOUNT_ID,
        "validate_updates": True,
        "skip_duplicate_updates": True,
        "webhook_challenge_delay": 8,
        "webhook_fields": (
            "messages",
            "message_template_status_update",
            "account_update",
        ),
    }
    if settings.WHATSAPP_AUTO_REGISTER_CALLBACK and callback_origin:
        kwargs["callback_url"] = callback_origin
        print(
            f"[whatsapp] auto-register enabled → Meta will challenge {callback_origin}"
            f"{webhook_endpoint}",
            flush=True,
        )
    else:
        print(
            "[whatsapp] skipping Meta callback auto-register "
            "(set WHATSAPP_AUTO_REGISTER_CALLBACK=true only if you need PyWa to set it). "
            "Webhook must already be configured in Meta Developer Console.",
            flush=True,
        )
    if api_version:
        kwargs["api_version"] = api_version

    expected_meta_url = f"{callback_origin or '<set WHATSAPP_CALLBACK_URL>'}{webhook_endpoint}"
    print(
        "[whatsapp] attaching PyWa "
        f"phone_id={settings.WHATSAPP_PHONE_NUMBER_ID!r} "
        f"waba_id={settings.WHATSAPP_BUSINESS_ACCOUNT_ID!r} "
        f"webhook_endpoint={webhook_endpoint!r} "
        f"meta_callback_should_be={expected_meta_url!r}",
        flush=True,
    )

    _register_webhook_access_log(app, webhook_endpoint)
    client = WhatsApp(**kwargs)
    _register_raw_debug_handler(client)
    register_message_handlers(client)
    register_callback_handlers(client)
    register_flow_handlers(client)
    register_status_handlers(client)
    set_whatsapp_client(client)
    _whatsapp = client
    logger.info("whatsapp_pywa_attached", extra={"webhook_endpoint": webhook_endpoint})
    print("[whatsapp] PyWa attached OK", flush=True)
    return client


def ensure_outbound_whatsapp_client() -> WhatsApp:
    """Send-capable PyWa client for API processes (no webhook server)."""

    global _whatsapp
    existing = get_attached_whatsapp() or get_whatsapp_client_optional()
    if existing is not None:
        return existing
    if not settings.WHATSAPP_ENABLED:
        raise RuntimeError("WhatsApp is disabled.")
    phone = (settings.WHATSAPP_PHONE_NUMBER_ID or "").strip()
    token = (settings.WHATSAPP_ACCESS_TOKEN or "").strip()
    if not phone or not token:
        raise RuntimeError("WHATSAPP_PHONE_NUMBER_ID and WHATSAPP_ACCESS_TOKEN are required.")
    kwargs: dict = {"phone_id": phone, "token": token}
    api_version = settings.WHATSAPP_GRAPH_VERSION or None
    if api_version:
        kwargs["api_version"] = api_version
    client = WhatsApp(**kwargs)
    set_whatsapp_client(client)
    _whatsapp = client
    return client
