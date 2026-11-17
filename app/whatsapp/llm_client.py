"""Optional LLM helpers for inbound media (describe / transcribe)."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.config.settings import settings


class LLMClient(ABC):
    @abstractmethod
    async def describe_image(self, *, image_bytes: bytes, mime_type: str, caption: str | None) -> str:
        raise NotImplementedError

    @abstractmethod
    async def transcribe_audio(self, *, audio_bytes: bytes, mime_type: str) -> str:
        raise NotImplementedError


class StubLLMClient(LLMClient):
    async def describe_image(self, *, image_bytes: bytes, mime_type: str, caption: str | None) -> str:
        _ = image_bytes, mime_type
        if caption and caption.strip():
            return f"[image] {caption.strip()}"
        return "[image received]"

    async def transcribe_audio(self, *, audio_bytes: bytes, mime_type: str) -> str:
        _ = audio_bytes, mime_type
        return "[voice note received — transcription not configured]"


class GeminiLLMClient(LLMClient):
    """Placeholder — wire google-genai in your fork when GEMINI_ENABLED=true."""

    async def describe_image(self, *, image_bytes: bytes, mime_type: str, caption: str | None) -> str:
        _ = image_bytes
        return await StubLLMClient().describe_image(
            image_bytes=b"",
            mime_type=mime_type,
            caption=caption,
        )

    async def transcribe_audio(self, *, audio_bytes: bytes, mime_type: str) -> str:
        _ = audio_bytes, mime_type
        return await StubLLMClient().transcribe_audio(audio_bytes=b"", mime_type=mime_type)


def get_llm_client() -> LLMClient:
    if getattr(settings, "GEMINI_ENABLED", False) and getattr(settings, "GEMINI_API_KEY", None):
        return GeminiLLMClient()
    return StubLLMClient()
