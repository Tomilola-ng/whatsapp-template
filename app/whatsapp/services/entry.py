"""Inbound message orchestration after PyWa normalization."""

from __future__ import annotations

import logging
from typing import Any

from app.whatsapp.brain import process_message
from app.whatsapp.schemas import WhatsAppLogicResponse
from app.whatsapp.services.service_window import record_inbound_service_window
from app.whatsapp.shared import normalize_inbound_msisdn

logger = logging.getLogger(__name__)


async def entry_point(
    text: str,
    msisdn: str,
    *,
    context: dict[str, Any] | None = None,
) -> WhatsAppLogicResponse:
    """Normalize MSISDN and delegate to the stub brain."""

    context = context or {}
    try:
        normalized = normalize_inbound_msisdn(msisdn)
    except ValueError:
        logger.exception("whatsapp_msisdn_normalize_failed")
        return WhatsAppLogicResponse(
            reply="I could not read that phone number. Please try again from WhatsApp."
        )

    occurred_at = context.get("occurred_at")
    if occurred_at is not None:
        try:
            record_inbound_service_window(msisdn=normalized, inbound_at=occurred_at)
        except Exception:
            logger.exception("whatsapp_service_window_record_failed")

    try:
        return await process_message(text, normalized, context=context)
    except Exception:
        logger.exception("whatsapp_entry_brain_failed", extra={"msisdn": normalized})
        return WhatsAppLogicResponse(
            reply="Something went wrong on my side. Please try again in a moment."
        )
