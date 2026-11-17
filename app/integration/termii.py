"""Thin SMS integration wrapper placeholder."""


class SMSConfigurationError(RuntimeError):
    """Raised when SMS delivery is requested without a configured provider."""


def send_sms_via_provider(*, recipient: str, body: str):
    """Deliver SMS through the configured provider.

    This starter intentionally ships as a provider-neutral template. Wire your
    Termii or preferred provider client here in product forks.
    """
    raise SMSConfigurationError(
        "SMS provider is not configured. Implement app.integration.termii for production SMS."
    )
