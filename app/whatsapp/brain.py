"""Domain-agnostic message brain — replace this for your product."""

from __future__ import annotations

from typing import Any

from app.whatsapp.schemas import WhatsAppLogicResponse


async def process_message(
    text: str,
    msisdn: str,
    *,
    context: dict[str, Any] | None = None,
) -> WhatsAppLogicResponse:
    """Stub brain: echo inbound text.

    Swap this function (or call your agent / LangGraph host from here) when you
    fork the template into a real WhatsApp product.
    """
    _ = context
    body = (text or "").strip() or "[empty message]"
    return WhatsAppLogicResponse(
        reply=f"Got it ({msisdn}): {body}",
    )
