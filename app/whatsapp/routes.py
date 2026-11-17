"""WhatsApp HTTP routes: status + local test send/agent."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.base.responses import success_response
from app.config.settings import settings
from app.whatsapp.schemas import TestAgentRequest, TestMessageRequest
from app.whatsapp.services.entry import entry_point
from app.whatsapp.services.replies import send_reply, send_user_message
from app.whatsapp.shared import normalize_inbound_msisdn

router = APIRouter(tags=["whatsapp"])


def _require_local_or_staging_only() -> None:
    if settings.ENVIRONMENT == "production":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")


@router.get("/whatsapp/status", status_code=status.HTTP_200_OK)
async def get_whatsapp_status():
    """Non-secret WhatsApp wiring check (no auth)."""

    phone = (settings.WHATSAPP_PHONE_NUMBER_ID or "").strip()
    waba = (settings.WHATSAPP_BUSINESS_ACCOUNT_ID or "").strip()
    origin = (settings.WHATSAPP_CALLBACK_URL or settings.APP_BASE_URL or "").rstrip("/")
    return success_response(
        {
            "enabled": bool(settings.WHATSAPP_ENABLED),
            "phone_number_id": phone or None,
            "business_account_id": waba or None,
            "display_number": (settings.WHATSAPP_DISPLAY_NUMBER or "").strip() or None,
            "webhook_endpoint": settings.WHATSAPP_WEBHOOK_ENDPOINT,
            "callback_url_setting": settings.WHATSAPP_CALLBACK_URL or None,
            "expected_meta_callback": (
                f"{origin}{settings.WHATSAPP_WEBHOOK_ENDPOINT}" if origin else None
            ),
            "hint": (
                "Configure the Meta webhook to expected_meta_callback, subscribe to "
                "`messages`, add a tester number, then text the Cloud API number. "
                "Look for '[whatsapp] HTTP POST' and inbound handler logs."
            ),
        },
        message="WhatsApp status.",
    )


@router.post("/whatsapp/test-message", status_code=status.HTTP_200_OK)
async def post_test_message(body: TestMessageRequest):
    """Send a free-form outbound text (local/staging only)."""

    _require_local_or_staging_only()
    if not settings.WHATSAPP_ENABLED:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="WhatsApp disabled")
    msisdn = normalize_inbound_msisdn(body.msisdn)
    message_id = await send_user_message(msisdn=msisdn, text=body.text)
    return success_response(
        {"msisdn": msisdn, "provider_message_id": message_id},
        message="Test message sent.",
    )


@router.post("/whatsapp/test-agent", status_code=status.HTTP_200_OK)
async def post_test_agent(body: TestAgentRequest):
    """Run inbound text through entry_point without a Meta webhook (local/staging)."""

    _require_local_or_staging_only()
    msisdn = normalize_inbound_msisdn(body.msisdn)
    response = await entry_point(body.text, msisdn, context={"source": "test-agent"})
    provider_message_id = None
    if body.send_whatsapp and settings.WHATSAPP_ENABLED and not response.silent:
        provider_message_id = await send_reply(msisdn=msisdn, response=response)
    return success_response(
        {
            "msisdn": msisdn,
            "reply": response.reply,
            "silent": response.silent,
            "provider_message_id": provider_message_id,
        },
        message="Test agent completed.",
    )
