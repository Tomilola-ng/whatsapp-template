"""Thin approved-template send helper (single-WABA; no mapping admin)."""

from __future__ import annotations

import logging
from typing import Any

from app.whatsapp.services.replies import _resolve_client, _send_with_soft_retry

logger = logging.getLogger(__name__)


async def send_template_message(
    *,
    msisdn: str,
    template_name: str,
    language_code: str = "en",
    body_params: list[str] | None = None,
    wa_client: Any | None = None,
) -> str | None:
    """Send an already-approved Cloud API template by name.

    Product forks should keep Meta template approval outside this starter.
    """

    name = (template_name or "").strip()
    if not name:
        raise ValueError("template_name is required")

    client = _resolve_client(wa_client)
    to = msisdn.lstrip("+")
    params = list(body_params or [])

    async def _send() -> Any:
        # Prefer PyWa helper when present; fall back to raw kwargs shape.
        if hasattr(client, "send_template"):
            return await client.send_template(
                to=to,
                name=name,
                language=language_code,
                params=params or None,
            )
        raise RuntimeError("WhatsApp client does not support send_template")

    try:
        sent = await _send_with_soft_retry(_send)
    except Exception:
        logger.exception(
            "whatsapp_template_send_failed",
            extra={"template": name, "msisdn": to},
        )
        raise

    message_id = getattr(sent, "id", None) or getattr(sent, "message_id", None)
    return str(message_id) if message_id is not None else None
