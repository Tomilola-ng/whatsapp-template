"""Structured logging hooks for request and ops context."""

from __future__ import annotations

import json
import logging
from typing import Any

from app.config.settings import settings


class StructuredLogger:
    """JSON log lines with request/resource context when enabled."""

    def __init__(self, name: str) -> None:
        self._logger = logging.getLogger(name)

    def log(
        self,
        level: int,
        message: str,
        *,
        request_id: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        **extra: Any,
    ) -> None:
        if not settings.STRUCTURED_LOGGING_ENABLED:
            self._logger.log(level, message)
            return
        payload = {
            "message": message,
            "request_id": request_id,
            "resource_type": resource_type,
            "resource_id": resource_id,
        }
        payload.update({k: v for k, v in extra.items() if v is not None})
        self._logger.log(level, json.dumps(payload, default=str))


structured_log = StructuredLogger("app")
