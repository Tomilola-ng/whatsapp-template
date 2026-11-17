"""PyWa inbound message pipeline."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from pywa.types import MessageType

from app.whatsapp.schemas import WhatsAppLogicResponse
from app.whatsapp.services.entry import entry_point
from app.whatsapp.services.media import (
    VOICE_TRANSCRIBE_FAILED_REPLY,
    describe_image,
    transcribe_audio,
)
from app.whatsapp.services.presence import typing_while_working
from app.whatsapp.services.replies import send_reply
from app.whatsapp.shared import normalize_inbound_msisdn

logger = logging.getLogger(__name__)

_RECENT_INBOUND: dict[str, tuple[str, float]] = {}
_DEDUPE_SECONDS = 60.0


def _is_duplicate_inbound(*, msisdn: str, text: str) -> bool:
    import time

    key = f"{msisdn}:{text.strip().casefold()}"
    now = time.monotonic()
    prior = _RECENT_INBOUND.get(key)
    _RECENT_INBOUND[key] = (text, now)
    if prior is None:
        return False
    _last_text, last_at = prior
    return (now - last_at) < _DEDUPE_SECONDS and _last_text.strip() == text.strip()


def _sender_wa_id(message: Any) -> str:
    user = getattr(message, "from_user", None)
    if user is not None:
        for attr in ("wa_id", "id", "phone_number"):
            value = getattr(user, attr, None)
            if value:
                return str(value)
    for attr in ("sender", "from_", "from_user_id"):
        value = getattr(message, attr, None)
        if value:
            return str(value)
    return ""


def register_message_handlers(wa: Any) -> None:
    @wa.on_message()
    async def on_message(client: Any, message: Any) -> None:
        try:
            wa_id = _sender_wa_id(message)
            msg_type = getattr(message, "type", None)
            if not wa_id:
                logger.warning("whatsapp_message_missing_sender")
                return
            msisdn = normalize_inbound_msisdn(wa_id)
            text = ""
            audio_id: str | None = None
            if msg_type == MessageType.TEXT:
                text = str(getattr(message, "text", "") or "")
            elif msg_type == MessageType.AUDIO:
                audio = getattr(message, "audio", None)
                raw_audio_id = getattr(audio, "id", None) if audio is not None else None
                audio_id = str(raw_audio_id).strip() if raw_audio_id else None
                if not audio_id:
                    await send_reply(
                        msisdn=msisdn,
                        response=WhatsAppLogicResponse(reply=VOICE_TRANSCRIBE_FAILED_REPLY),
                        wa_client=client,
                    )
                    return
            elif msg_type == MessageType.IMAGE:
                image = getattr(message, "image", None)
                image_id = getattr(image, "id", None) if image is not None else None
                caption = getattr(image, "caption", None) if image is not None else None
                if image_id:
                    text = await describe_image(client, str(image_id), caption=caption)
                else:
                    text = "[image received]"
            else:
                logger.info("whatsapp_message_ignored", extra={"type": str(msg_type)})
                return

            occurred = getattr(message, "timestamp", None)
            if isinstance(occurred, (int, float)):
                occurred_at = datetime.fromtimestamp(int(occurred), tz=timezone.utc)
            elif isinstance(occurred, datetime):
                occurred_at = occurred if occurred.tzinfo else occurred.replace(tzinfo=timezone.utc)
            else:
                occurred_at = datetime.now(timezone.utc)

            external_message_id = str(getattr(message, "id", "") or "")
            context = {
                "wa_id": wa_id,
                "external_message_id": external_message_id,
                "external_thread_id": msisdn,
                "event_id": external_message_id,
                "occurred_at": occurred_at,
                "is_group": False,
                "is_voice": bool(audio_id),
            }

            async with typing_while_working(client=client, message=message):
                if audio_id:
                    text = await transcribe_audio(client, audio_id) or ""
                    if not text:
                        await send_reply(
                            msisdn=msisdn,
                            response=WhatsAppLogicResponse(reply=VOICE_TRANSCRIBE_FAILED_REPLY),
                            wa_client=client,
                        )
                        return
                if _is_duplicate_inbound(msisdn=msisdn, text=text):
                    return
                response = await entry_point(text, msisdn, context=context)
                if response.silent:
                    return
                await send_reply(msisdn=msisdn, response=response, wa_client=client)
        except Exception:
            logger.exception("whatsapp_on_message_failed")
            try:
                wa_id = _sender_wa_id(message)
                if wa_id:
                    msisdn = normalize_inbound_msisdn(wa_id)
                    await send_reply(
                        msisdn=msisdn,
                        response=WhatsAppLogicResponse(
                            reply="Something went wrong on my side. Please try again in a moment."
                        ),
                        wa_client=client,
                    )
            except Exception:
                logger.exception("whatsapp_error_reply_failed")
