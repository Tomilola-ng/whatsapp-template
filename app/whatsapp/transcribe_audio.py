"""Compatibility shim — prefer ``app.whatsapp.services.media``."""

from app.whatsapp.services.media import VOICE_TRANSCRIBE_FAILED_REPLY, transcribe_audio

__all__ = ["VOICE_TRANSCRIBE_FAILED_REPLY", "transcribe_audio"]
