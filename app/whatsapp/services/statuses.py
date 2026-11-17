"""Delivery status extension point (log-only in the starter)."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def register_status_handlers(wa: Any) -> None:
    """Attach a no-op-friendly status logger when PyWa supports it."""

    handler = getattr(wa, "on_message_status", None)
    if handler is None:
        logger.debug("whatsapp_status_handler_unavailable")
        return

    @handler()
    async def on_message_status(_client: Any, status: Any) -> None:
        try:
            status_value = getattr(status, "status", None) or getattr(status, "type", None)
            message_id = getattr(status, "id", None) or getattr(status, "message_id", None)
            recipient = getattr(status, "recipient_id", None) or getattr(
                getattr(status, "from_user", None), "wa_id", None
            )
            logger.info(
                "whatsapp_message_status status=%s message_id=%s recipient=%s",
                status_value,
                message_id,
                recipient,
            )
        except Exception:
            logger.exception("whatsapp_status_handler_failed")
