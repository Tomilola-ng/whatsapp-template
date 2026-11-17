"""Compatibility shim — prefer ``app.whatsapp.services.callbacks``."""

from app.whatsapp.services.callbacks import PREFIX_HELP, register_callback_handlers

__all__ = ["PREFIX_HELP", "register_callback_handlers"]
