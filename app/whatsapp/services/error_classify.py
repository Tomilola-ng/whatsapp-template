"""Versioned WhatsApp provider error classification (starter subset)."""

from __future__ import annotations

from dataclasses import dataclass

from app.base.redaction import redact_exception_message
from app.whatsapp.exceptions import (
    WhatsAppAuthError,
    WhatsAppPermanentError,
    WhatsAppProviderError,
    WhatsAppTransientError,
)

CLASSIFIER_VERSION = "wa-err-v1"

_PERMANENT_PROVIDER_CODES: frozenset[str] = frozenset(
    {
        "100",
        "131026",
        "131047",
        "131051",
        "132000",
        "132001",
        "132005",
        "132007",
        "132012",
        "132015",
        "132016",
        "368",
        "10",
        "190",
    }
)

_TRANSIENT_PROVIDER_CODES: frozenset[str] = frozenset(
    {
        "1",
        "2",
        "4",
        "17",
        "80007",
        "130429",
        "131048",
        "131056",
        "133016",
    }
)

_AUTH_CODES: frozenset[str] = frozenset({"10", "190", "102", "200", "OAuthException"})


@dataclass(frozen=True, slots=True)
class ClassificationResult:
    retryable: bool
    error_code: str
    remediation_code: str
    safe_message: str
    provider_code: str | None
    retry_after_seconds: float | None
    ambiguous: bool
    classifier_version: str = CLASSIFIER_VERSION


def _provider_code_of(exc: BaseException) -> str | None:
    for attr in ("provider_code", "error_code", "code"):
        if hasattr(exc, attr):
            value = getattr(exc, attr)
            if value is not None and str(value).strip():
                return str(value).strip()
    return None


def _retry_after_of(exc: BaseException) -> float | None:
    for attr in ("retry_after", "retry_after_seconds"):
        if hasattr(exc, attr):
            try:
                value = float(getattr(exc, attr))
                if value >= 0:
                    return value
            except (TypeError, ValueError):
                continue
    headers = getattr(exc, "headers", None)
    if isinstance(headers, dict):
        raw = headers.get("Retry-After") or headers.get("retry-after")
        if raw is not None:
            try:
                return max(0.0, float(raw))
            except (TypeError, ValueError):
                return None
    return None


def classify_send_failure(exc: BaseException) -> ClassificationResult:
    """Classify a send/provider failure for soft retry policy."""

    raw_message = str(exc)
    safe_message = redact_exception_message(raw_message) or "WhatsApp provider call failed"
    name = type(exc).__name__
    lowered = f"{name} {raw_message}".lower()
    provider_code = _provider_code_of(exc)
    code_key = (provider_code or "").strip()
    retry_after = _retry_after_of(exc)

    if isinstance(exc, WhatsAppAuthError):
        return ClassificationResult(
            retryable=False,
            error_code="whatsapp_auth_error",
            remediation_code="reconnect_whatsapp",
            safe_message=safe_message,
            provider_code=provider_code,
            retry_after_seconds=None,
            ambiguous=False,
        )
    if isinstance(exc, WhatsAppTransientError):
        ambiguous = any(m in lowered for m in ("timeout", "timed out", "ambiguous"))
        return ClassificationResult(
            retryable=True,
            error_code="provider_temporarily_unavailable",
            remediation_code="retry_later",
            safe_message=safe_message,
            provider_code=provider_code,
            retry_after_seconds=retry_after,
            ambiguous=ambiguous,
        )
    if isinstance(exc, WhatsAppPermanentError):
        return ClassificationResult(
            retryable=False,
            error_code="provider_rejected",
            remediation_code="fix_recipient_or_content",
            safe_message=safe_message,
            provider_code=provider_code,
            retry_after_seconds=None,
            ambiguous=False,
        )

    if code_key in _AUTH_CODES or any(
        m in lowered
        for m in (
            "authorization",
            "auth",
            "token",
            "permission",
            "expiredaccesstoken",
            "oauth",
            "accessdenied",
            "invalid oauth",
            "session has expired",
        )
    ):
        return ClassificationResult(
            retryable=False,
            error_code="whatsapp_auth_error",
            remediation_code="reconnect_whatsapp",
            safe_message=safe_message,
            provider_code=provider_code or code_key,
            retry_after_seconds=None,
            ambiguous=False,
        )

    if code_key in _PERMANENT_PROVIDER_CODES or any(
        m in lowered
        for m in (
            "invalid recipient",
            "not a valid whatsapp",
            "blocked",
            "user is part of an experiment",
            "template",
            "policy",
            "unsupported media",
            "media upload",
            "parameter value is not valid",
        )
    ):
        remediation = "fix_recipient_or_content"
        error_code = "provider_rejected"
        if "template" in lowered or code_key.startswith("132"):
            remediation = "fix_template"
            error_code = "template_rejected"
        elif "block" in lowered or code_key in {"131047", "368"}:
            remediation = "recipient_unreachable"
            error_code = "recipient_blocked"
        elif "media" in lowered:
            remediation = "fix_media"
            error_code = "media_rejected"
        return ClassificationResult(
            retryable=False,
            error_code=error_code,
            remediation_code=remediation,
            safe_message=safe_message,
            provider_code=provider_code or code_key,
            retry_after_seconds=None,
            ambiguous=False,
        )

    if code_key in _TRANSIENT_PROVIDER_CODES or any(
        m in lowered
        for m in (
            "timeout",
            "timed out",
            "temporarily",
            "rate",
            "throttle",
            "unavailable",
            "connection",
            "429",
            "500",
            "502",
            "503",
            "504",
        )
    ):
        ambiguous = any(m in lowered for m in ("timeout", "timed out"))
        return ClassificationResult(
            retryable=True,
            error_code="provider_temporarily_unavailable",
            remediation_code="retry_later",
            safe_message=safe_message,
            provider_code=provider_code or code_key,
            retry_after_seconds=retry_after,
            ambiguous=ambiguous,
        )

    return ClassificationResult(
        retryable=False,
        error_code="provider_rejected",
        remediation_code="fix_recipient_or_content",
        safe_message=safe_message,
        provider_code=provider_code,
        retry_after_seconds=None,
        ambiguous=False,
    )


def classify_provider_exception(exc: BaseException) -> WhatsAppProviderError:
    result = classify_send_failure(exc)
    if result.error_code == "whatsapp_auth_error":
        err: WhatsAppProviderError = WhatsAppAuthError(
            result.safe_message, provider_code=result.provider_code
        )
    elif result.retryable:
        err = WhatsAppTransientError(
            result.safe_message, provider_code=result.provider_code
        )
    else:
        err = WhatsAppPermanentError(
            result.safe_message, provider_code=result.provider_code
        )
    setattr(err, "classification", result)
    if result.retry_after_seconds is not None:
        setattr(err, "retry_after_seconds", result.retry_after_seconds)
    return err


def classification_from_exception(exc: BaseException) -> ClassificationResult:
    existing = getattr(exc, "classification", None)
    if isinstance(existing, ClassificationResult):
        return existing
    return classify_send_failure(exc)
