"""Public WhatsApp service API for the single-WABA starter."""

from app.whatsapp.services.entry import entry_point
from app.whatsapp.services.error_classify import (
    ClassificationResult,
    classify_send_failure,
)
from app.whatsapp.services.flows import handle_flow_completion
from app.whatsapp.services.handlers import register_message_handlers
from app.whatsapp.services.replies import send_reply, send_user_message
from app.whatsapp.services.service_window import (
    get_service_window_last_inbound,
    record_inbound_service_window,
    service_window_open,
)
from app.whatsapp.services.templates import send_template_message

__all__ = [
    "ClassificationResult",
    "classify_send_failure",
    "entry_point",
    "get_service_window_last_inbound",
    "handle_flow_completion",
    "record_inbound_service_window",
    "register_message_handlers",
    "send_reply",
    "send_template_message",
    "send_user_message",
    "service_window_open",
]
