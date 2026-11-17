"""WhatsApp Cloud API boundary via PyWa (single business number)."""

from app.whatsapp.client import attach_whatsapp, get_attached_whatsapp
from app.whatsapp.routes import router
from app.whatsapp.services.entry import entry_point
from app.whatsapp.services.flows import handle_flow_completion
from app.whatsapp.services.templates import send_template_message

__all__ = [
    "attach_whatsapp",
    "entry_point",
    "get_attached_whatsapp",
    "handle_flow_completion",
    "router",
    "send_template_message",
]
