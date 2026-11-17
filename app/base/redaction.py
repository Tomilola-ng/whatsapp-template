"""Sensitive-value redaction helpers for logs, errors, and audit metadata."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

_SENSITIVE_KEY_FRAGMENTS = (
    "password",
    "secret",
    "token",
    "otp",
    "authorization",
    "api_key",
    "apikey",
    "webhook",
    "setup_code",
    "dashboard_token",
    "bearer",
    "prompt",
    "raw_payload",
    "private_key",
    "gemini",
    "internal_note",
    "note_content",
)

_REDACTED = "[REDACTED]"


def is_sensitive_key(key: str) -> bool:
    """Return True when a mapping key looks sensitive."""
    normalized = key.lower().replace("-", "_")
    return any(fragment in normalized for fragment in _SENSITIVE_KEY_FRAGMENTS)


def redact_mapping(value: Any) -> Any:
    """Deep-copy and redact sensitive keys in nested dict/list structures."""
    if isinstance(value, dict):
        cleaned: dict[str, Any] = {}
        for key, item in value.items():
            if is_sensitive_key(str(key)):
                cleaned[key] = _REDACTED
            else:
                cleaned[key] = redact_mapping(item)
        return cleaned
    if isinstance(value, list):
        return [redact_mapping(item) for item in value]
    return value


def redact_for_log(payload: dict[str, Any] | None) -> dict[str, Any] | None:
    """Safe log-oriented redaction (returns ``None`` for ``None`` input)."""
    if payload is None:
        return None
    if not isinstance(payload, dict):
        raise TypeError("Log payload must be a JSON object (dict).")
    return redact_mapping(deepcopy(payload))


def redact_audit_metadata(metadata: dict[str, Any] | None) -> dict[str, Any] | None:
    """Audit-compatible alias for :func:`redact_for_log`."""
    return redact_for_log(metadata)


def redact_exception_message(message: str | None, *, max_length: int = 400) -> str | None:
    """Truncate and scrub common secret-looking substrings from exception text."""
    if not message:
        return None
    text = str(message)
    lowered = text.lower()
    for needle in (
        "bearer ",
        "authorization:",
        "api_key",
        "password=",
        "secret=",
        "webhook",
    ):
        if needle in lowered:
            return _REDACTED
    return text[:max_length]
