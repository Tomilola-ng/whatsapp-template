"""Shared WhatsApp helpers (MSISDN, formatting, client accessor)."""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

import phonenumbers
from phonenumbers import NumberParseException, PhoneNumberFormat

if TYPE_CHECKING:
    from pywa_async import WhatsApp

logger = logging.getLogger(__name__)

_wa_client: WhatsApp | None = None

_MARKDOWN_BOLD = re.compile(r"\*\*(.+?)\*\*")
_MARKDOWN_ITALIC = re.compile(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)")
_BOLD_PLACEHOLDER = "\x00"


def set_whatsapp_client(client: WhatsApp | None) -> None:
    global _wa_client
    _wa_client = client


def get_whatsapp_client_optional() -> WhatsApp | None:
    return _wa_client


def get_whatsapp_client() -> WhatsApp:
    if _wa_client is None:
        raise RuntimeError("WhatsApp client is not configured.")
    return _wa_client


def normalize_msisdn(raw: str, *, default_region: str | None = None) -> str:
    """Normalize a phone number to E.164."""
    value = (raw or "").strip()
    if not value:
        raise ValueError("Phone number is required.")
    try:
        parsed = phonenumbers.parse(value, default_region)
    except NumberParseException as exc:
        raise ValueError("Invalid phone number format.") from exc
    if not phonenumbers.is_possible_number(parsed):
        raise ValueError("Phone number is not possible.")
    if not phonenumbers.is_valid_number(parsed):
        raise ValueError("Phone number is not valid.")
    return phonenumbers.format_number(parsed, PhoneNumberFormat.E164)


def normalize_inbound_msisdn(raw: str) -> str:
    """Normalize inbound WhatsApp wa_id / phone to E.164."""
    value = (raw or "").strip()
    if value and not value.startswith("+"):
        value = f"+{value}"
    return normalize_msisdn(value)


def format_whatsapp_message(text: str) -> str:
    """Light markdown → WhatsApp-friendly text (**bold** → *bold*, *italic* → _italic_)."""
    cleaned = _MARKDOWN_BOLD.sub(
        lambda m: f"{_BOLD_PLACEHOLDER}{m.group(1)}{_BOLD_PLACEHOLDER}",
        text or "",
    )
    cleaned = _MARKDOWN_ITALIC.sub(r"_\1_", cleaned)
    cleaned = cleaned.replace(_BOLD_PLACEHOLDER, "*")
    return cleaned.strip()[:4096]
