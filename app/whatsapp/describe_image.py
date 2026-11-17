"""Compatibility shim — prefer ``app.whatsapp.services.media``."""

from app.whatsapp.services.media import describe_image

__all__ = ["describe_image"]
