"""WhatsApp channel response contracts."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field, model_validator


class FlowId(StrEnum):
    GENERIC_CONTACT = "generic_contact"


class WhatsAppLogicResponse(BaseModel):
    """Structured result from entry/flows for replies.py to send."""

    reply: str = Field(default="", max_length=4096)
    silent: bool = False
    reply_chat_id: str | None = None
    quote_message_id: str | None = None
    flow: FlowId | None = None
    flow_buttons: list[str] = Field(default_factory=list, max_length=3)

    @model_validator(mode="after")
    def _require_reply_unless_silent(self) -> WhatsAppLogicResponse:
        if not self.silent and not (self.reply or "").strip():
            raise ValueError("reply is required unless silent=True")
        return self


class TestMessageRequest(BaseModel):
    """Outbound smoke body: send free-form text via the configured Cloud number."""

    msisdn: str = Field(min_length=5, max_length=20)
    text: str = Field(
        default="Hello from the WhatsApp FastAPI template.",
        min_length=1,
        max_length=4096,
    )


class TestAgentRequest(BaseModel):
    """Simulate an inbound WhatsApp DM through entry_point (no Meta webhook)."""

    msisdn: str = Field(min_length=5, max_length=20)
    text: str = Field(min_length=1, max_length=4096)
    send_whatsapp: bool = Field(
        default=False,
        description="If true, also send the reply via Cloud API.",
    )
