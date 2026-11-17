"""Compatibility shim — prefer ``app.whatsapp.services.flows``."""

from app.whatsapp.services.flows import (
    handle_flow_completion,
    register_flow_handler,
    register_flow_handlers,
)

__all__ = [
    "handle_flow_completion",
    "register_flow_handler",
    "register_flow_handlers",
]
