"""Standard API response envelopes."""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class EnvelopeResponse(BaseModel, Generic[T]):
    """Generic API envelope schema."""

    success: bool = True
    message: str
    data: T | None = None


class HealthResponse(BaseModel):
    """Health-check payload schema."""

    success: bool = True
    message: str
    data: dict[str, Any]


def success_response(data: Any = None, message: str = "OK") -> dict[str, Any]:
    """Build a standard success response envelope."""
    return {"success": True, "message": message, "data": data}


def error_response(message: str, code: str | None = None) -> dict[str, Any]:
    """Build a standard error response envelope."""
    payload = {"success": False, "message": message, "data": None}
    if code:
        payload["code"] = code
    return payload
