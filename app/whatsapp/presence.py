"""Compatibility shim — prefer ``app.whatsapp.services.presence``."""

from app.whatsapp.services.presence import (
    inbound_message_id,
    indicate_typing,
    typing_while_working,
)

__all__ = ["inbound_message_id", "indicate_typing", "typing_while_working"]
