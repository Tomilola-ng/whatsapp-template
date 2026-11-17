"""Compatibility shim — prefer ``app.whatsapp.services.entry``."""

from app.whatsapp.services.entry import entry_point

__all__ = ["entry_point"]
