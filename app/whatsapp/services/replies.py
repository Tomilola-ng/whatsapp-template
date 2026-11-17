"""Outbound WhatsApp sends — the only module that calls PyWa send APIs."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from app.config.settings import settings
from app.whatsapp.schemas import WhatsAppLogicResponse
from app.whatsapp.services.error_classify import classify_send_failure
from app.whatsapp.shared import format_whatsapp_message, get_whatsapp_client

logger = logging.getLogger(__name__)


def _resolve_client(wa_client: Any | None) -> Any:
    if wa_client is not None:
        return wa_client
    try:
        return get_whatsapp_client()
    except RuntimeError:
        from app.whatsapp.client import ensure_outbound_whatsapp_client

        return ensure_outbound_whatsapp_client()


async def _send_with_soft_retry(send_coro_factory) -> Any:
    """Bounded in-process retry on transient provider failures only."""

    max_attempts = max(1, int(settings.WHATSAPP_OUTBOUND_MAX_ATTEMPTS))
    last_exc: BaseException | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            return await send_coro_factory()
        except Exception as exc:
            last_exc = exc
            result = classify_send_failure(exc)
            if not result.retryable or result.ambiguous or attempt >= max_attempts:
                logger.warning(
                    "whatsapp_outbound_failed attempt=%s retryable=%s code=%s",
                    attempt,
                    result.retryable,
                    result.error_code,
                )
                raise
            delay = result.retry_after_seconds
            if delay is None:
                delay = min(8.0, 0.5 * (2 ** (attempt - 1)))
            logger.info(
                "whatsapp_outbound_retry attempt=%s sleep=%.2fs code=%s",
                attempt,
                delay,
                result.error_code,
            )
            await asyncio.sleep(max(0.0, float(delay)))
    assert last_exc is not None
    raise last_exc


async def send_reply(
    *,
    msisdn: str,
    response: WhatsAppLogicResponse,
    wa_client: Any | None = None,
) -> str | None:
    """Send a text reply. Group replies use ``response.reply_chat_id`` when set."""

    if response.silent:
        return None

    client = _resolve_client(wa_client)
    text = format_whatsapp_message(response.reply)
    to = response.reply_chat_id or msisdn.lstrip("+")

    kwargs: dict[str, Any] = {"to": to, "text": text}
    if response.quote_message_id:
        kwargs["reply_to_message_id"] = response.quote_message_id

    sent = await _send_with_soft_retry(lambda: client.send_message(**kwargs))
    message_id = getattr(sent, "id", None) or getattr(sent, "message_id", None)
    return str(message_id) if message_id is not None else None


async def send_user_message(*, msisdn: str, text: str, wa_client: Any | None = None) -> str | None:
    """Send a plain text message (dev/test helpers)."""

    return await send_reply(
        msisdn=msisdn,
        response=WhatsAppLogicResponse(reply=text),
        wa_client=wa_client,
    )
