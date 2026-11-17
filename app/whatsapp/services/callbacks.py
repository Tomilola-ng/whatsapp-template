"""Callback button handlers registered on the PyWa client."""

from __future__ import annotations

import logging
from typing import Any

from app.whatsapp.services.replies import send_user_message
from app.whatsapp.shared import normalize_inbound_msisdn

logger = logging.getLogger(__name__)

PREFIX_HELP = "help:"


def register_callback_handlers(wa: Any) -> None:
    """Attach callback-button handlers to the WhatsApp client."""

    @wa.on_callback_button()
    async def on_callback_button(_client: Any, button: Any) -> None:
        try:
            data = str(getattr(button, "data", "") or "")
            raw_from = (
                getattr(getattr(button, "from_user", None), "wa_id", None)
                or getattr(button, "sender", None)
                or getattr(button, "from_", None)
                or ""
            )
            msisdn = normalize_inbound_msisdn(str(raw_from))
            if data.startswith(PREFIX_HELP):
                await send_user_message(
                    msisdn=msisdn,
                    text="Send me a normal text message and I'll reply.",
                    wa_client=_client,
                )
                return
            await send_user_message(
                msisdn=msisdn,
                text="That button is not recognized. Please send a text message instead.",
                wa_client=_client,
            )
        except Exception:
            logger.exception("whatsapp_callback_failed")
