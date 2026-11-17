"""Safe inbound media download via PyWa URL + host allowlist."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

from app.config.settings import settings
from app.whatsapp.exceptions import WhatsAppMediaError, WhatsAppTransientError
from app.whatsapp.llm_client import get_llm_client

logger = logging.getLogger(__name__)

VOICE_TRANSCRIBE_FAILED_REPLY = (
    "I received a voice note, but I couldn't transcribe it. Could you type that instead?"
)


@dataclass(frozen=True, slots=True)
class FetchedMedia:
    content: bytes
    mime_type: str


def _host_allowed(url: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    allow = {
        h.strip().lower()
        for h in (settings.WHATSAPP_MEDIA_FETCH_ALLOWLIST_HOSTS or [])
        if h and h.strip()
    }
    return bool(host and host in allow)


def _mime_allowed(mime: str) -> bool:
    allowed = {
        m.strip().lower()
        for m in (settings.WHATSAPP_MEDIA_ALLOWED_MIME_TYPES or [])
        if m and m.strip()
    }
    if not allowed:
        return True
    return (mime or "").strip().lower() in allowed


async def download_media_bytes(wa_client: Any, media_id: str) -> FetchedMedia:
    """Resolve media URL via PyWa, enforce host/size/MIME, then download bytes."""

    media_id = (media_id or "").strip()
    if not media_id:
        raise WhatsAppMediaError("media_id is required")

    try:
        media_url = await wa_client.get_media_url(media_id=media_id)
    except Exception as exc:
        raise WhatsAppTransientError("media metadata unavailable") from exc

    url = getattr(media_url, "url", None) or str(media_url)
    mime = str(getattr(media_url, "mime_type", None) or "application/octet-stream")
    if not url or not _host_allowed(url):
        raise WhatsAppMediaError("media download host not allowlisted")
    if not _mime_allowed(mime):
        raise WhatsAppMediaError("media mime type not allowed")

    try:
        content = await wa_client.get_media_bytes(url=url)
    except Exception as exc:
        raise WhatsAppTransientError("media download failed") from exc

    payload = bytes(content or b"")
    max_bytes = max(1, int(settings.WHATSAPP_MEDIA_MAX_BYTES))
    if len(payload) > max_bytes:
        raise WhatsAppMediaError("media exceeds size limit")
    return FetchedMedia(content=payload, mime_type=mime)


async def describe_image(
    wa_client: Any,
    image_id: str,
    caption: str | None = None,
) -> str:
    try:
        media = await download_media_bytes(wa_client, image_id)
        return await get_llm_client().describe_image(
            image_bytes=media.content,
            mime_type=media.mime_type,
            caption=caption,
        )
    except Exception:
        logger.exception("whatsapp_describe_image_failed", extra={"image_id": image_id})
        if caption and caption.strip():
            return f"[image] {caption.strip()}"
        return "[image received]"


async def transcribe_audio(wa_client: Any, audio_id: str) -> str | None:
    """Return transcript text, or None when the caller should ask the user to type."""

    try:
        media = await download_media_bytes(wa_client, audio_id)
        if not media.content:
            return None
        text = await get_llm_client().transcribe_audio(
            audio_bytes=media.content, mime_type=media.mime_type
        )
        cleaned = (text or "").strip()
        return cleaned or None
    except Exception:
        logger.exception("whatsapp_transcribe_audio_failed", extra={"audio_id": audio_id})
        return None
