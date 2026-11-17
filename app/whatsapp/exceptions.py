"""Starter WhatsApp domain errors (single-WABA; no tenant/usage types)."""

from __future__ import annotations


class WhatsAppError(Exception):
    """Base WhatsApp boundary error."""


class WhatsAppConfigurationError(WhatsAppError):
    """Missing or invalid WhatsApp configuration."""


class WhatsAppProviderError(WhatsAppError):
    """Provider/Graph API failure."""

    def __init__(self, message: str, *, provider_code: str | None = None) -> None:
        super().__init__(message)
        self.provider_code = provider_code


class WhatsAppTransientError(WhatsAppProviderError):
    """Retryable provider failure."""


class WhatsAppPermanentError(WhatsAppProviderError):
    """Non-retryable provider failure."""


class WhatsAppAuthError(WhatsAppPermanentError):
    """Access token / permission failure — reconnect credentials."""


class WhatsAppMediaError(WhatsAppPermanentError):
    """Media download/validation rejected."""
