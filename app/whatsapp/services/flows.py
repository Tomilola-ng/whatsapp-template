"""WhatsApp Flow completion registry (placeholder)."""

from __future__ import annotations

import logging
from typing import Any, Awaitable, Callable

from app.whatsapp.schemas import FlowId, WhatsAppLogicResponse

logger = logging.getLogger(__name__)

FlowHandler = Callable[[Any, Any], Awaitable[WhatsAppLogicResponse]]

_REGISTRY: dict[str, FlowHandler] = {}


async def _generic_contact_handler(_wa_client: Any, completion: Any) -> WhatsAppLogicResponse:
    _ = completion
    return WhatsAppLogicResponse(
        reply="Thanks — I received the form. An operator will follow up if needed."
    )


def register_flow_handler(flow_id: str, handler: FlowHandler) -> None:
    _REGISTRY[flow_id] = handler


register_flow_handler(FlowId.GENERIC_CONTACT.value, _generic_contact_handler)


async def handle_flow_completion(wa_client: Any, completion: Any) -> WhatsAppLogicResponse:
    """Dispatch a completed flow to a registered handler."""

    token = str(
        getattr(completion, "flow_token", None) or getattr(completion, "token", None) or ""
    )
    handler = _REGISTRY.get(token) or _REGISTRY.get(FlowId.GENERIC_CONTACT.value)
    if handler is None:
        logger.warning("whatsapp_flow_unhandled", extra={"token": token[:80]})
        return WhatsAppLogicResponse(reply="Thanks — I received that.")
    try:
        return await handler(wa_client, completion)
    except Exception:
        logger.exception("whatsapp_flow_handler_failed")
        return WhatsAppLogicResponse(
            reply="Something went wrong while processing that form. Please try again later."
        )


def register_flow_handlers(wa: Any) -> None:
    @wa.on_flow_completion()
    async def on_flow_completion(client: Any, completion: Any) -> None:
        from app.whatsapp.services.replies import send_reply
        from app.whatsapp.shared import normalize_inbound_msisdn

        response = await handle_flow_completion(client, completion)
        raw_from = (
            getattr(getattr(completion, "from_user", None), "wa_id", None)
            or getattr(completion, "sender", None)
            or ""
        )
        if not raw_from:
            return
        msisdn = normalize_inbound_msisdn(str(raw_from))
        await send_reply(msisdn=msisdn, response=response, wa_client=client)
