"""Compatibility shim — prefer ``app.whatsapp.services.handlers``."""

from app.whatsapp.services.handlers import register_message_handlers

__all__ = ["register_message_handlers"]
