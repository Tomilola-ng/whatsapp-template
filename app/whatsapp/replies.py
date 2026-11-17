"""Compatibility shim — prefer ``app.whatsapp.services.replies``."""

from app.whatsapp.services.replies import send_reply, send_user_message

__all__ = ["send_reply", "send_user_message"]
