"""Application settings and configuration helpers."""

import logging
from typing import Annotated, Any, Literal, Self

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

logger = logging.getLogger(__name__)

_PLACEHOLDER_SECRETS = frozenset({"", "change-me", "change-me-in-real-projects"})
_MIN_SECRET_LENGTH = 32


def _split_csv(value: str | list[str] | None) -> list[str]:
    """Normalize comma-separated env values into a clean list."""
    if value is None:
        return []
    if isinstance(value, list):
        return [item.strip() for item in value if item and item.strip()]
    return [item.strip() for item in value.split(",") if item.strip()]


def _is_weak_secret(value: str) -> bool:
    return not value or len(value) < _MIN_SECRET_LENGTH or value in _PLACEHOLDER_SECRETS


class AppSettings(BaseSettings):
    """Single source of truth for environment variables used by the app."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    PROJECT_NAME: str = "WhatsApp FastAPI 2026 Template"
    API_V1_PREFIX: str = "/api/v1"
    APP_VERSION: str = "0.1.0"
    APP_BASE_URL: str = "http://localhost:8000"
    CLIENT_APP_URL: str = "http://localhost:3000"
    PASSWORD_SETUP_URL: str = "http://localhost:3000/set-password"
    ADMIN_PASSWORD_SETUP_CODE_EXPIRE_HOURS: int = 2
    ENVIRONMENT: Literal["local", "staging", "production"] = "local"
    OPENAPI_ENABLED: bool = False
    STRUCTURED_LOGGING_ENABLED: bool = True
    DATABASE_URL: str = Field(
        default="sqlite://db.sqlite3",
        description="Default local database URL for first boot.",
    )

    # WhatsApp Cloud API (PyWa). Optional until WHATSAPP_ENABLED=true.
    WHATSAPP_ENABLED: bool = False
    WHATSAPP_PHONE_NUMBER_ID: str | None = None
    WHATSAPP_BUSINESS_ACCOUNT_ID: str | None = None
    WHATSAPP_ACCESS_TOKEN: str | None = None
    WHATSAPP_APP_ID: str | None = None
    WHATSAPP_VERIFY_TOKEN: str | None = None
    WHATSAPP_APP_SECRET: str | None = None
    WHATSAPP_GRAPH_VERSION: str | None = None
    WHATSAPP_CALLBACK_URL: str | None = None
    WHATSAPP_AUTO_REGISTER_CALLBACK: bool = False
    WHATSAPP_WEBHOOK_ENDPOINT: str = "/api/v1/webhooks/whatsapp"
    WHATSAPP_DISPLAY_NUMBER: str | None = None
    WHATSAPP_MEDIA_MAX_BYTES: int = Field(default=25_000_000, ge=1, le=100_000_000)
    WHATSAPP_SERVICE_WINDOW_HOURS: float = 24.0
    WHATSAPP_OUTBOUND_MAX_ATTEMPTS: int = Field(default=3, ge=1, le=5)
    WHATSAPP_MEDIA_ALLOWED_MIME_TYPES: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: [
            "image/jpeg",
            "image/png",
            "image/webp",
            "audio/ogg",
            "audio/mpeg",
            "audio/aac",
            "application/pdf",
        ]
    )
    WHATSAPP_MEDIA_FETCH_ALLOWLIST_HOSTS: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: [
            "graph.facebook.com",
            "graph.whatsapp.com",
            "lookaside.fbsbx.com",
        ]
    )
    RATE_LIMIT_WHATSAPP_WEBHOOK: str = "240/minute"
    GEMINI_ENABLED: bool = False
    GEMINI_API_KEY: str | None = None
    CORS_ORIGINS: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://localhost:5173",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
        ]
    )
    JWT_SECRET_KEY: str = ""
    OTP_HMAC_SECRET: str = ""
    API_AUTHORIZATION_TOKEN: str = "change-me"
    TRUSTED_PROXY_IPS: Annotated[list[str], NoDecode] = Field(default_factory=list)
    OTP_RESEND_COOLDOWN_SECONDS: int = 60
    RATE_LIMIT_LOGIN: str = "10/minute"
    RATE_LIMIT_REGISTER: str = "5/minute"
    RATE_LIMIT_OTP_SEND: str = "3/minute"
    RATE_LIMIT_OTP_VERIFY: str = "10/minute"
    RATE_LIMIT_REFRESH: str = "30/minute"
    RATE_LIMIT_CONTACT: str = "3/minute"
    RATE_LIMIT_ACCESS: str = "60/minute"
    RATE_LIMIT_CLIENT_ERRORS: str = "30/minute"
    RATE_LIMIT_UPDATE_POLICY: str = "60/minute"
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_STORAGE_URL: str | None = None
    RATE_LIMIT_DEFAULT: str = "100/minute"
    DEV_OUTBOX_ENABLED: bool = False
    BRAND_NAME: str | None = None
    BRAND_LOGO_URL: str | None = None
    BRAND_PRIMARY_COLOR: str | None = None
    BRAND_DARK_COLOR: str | None = None
    BRAND_ON_PRIMARY_COLOR: str | None = None
    SUPPORT_EMAIL: str | None = None
    TERMS_URL: str = "https://example.com/terms"
    PRIVACY_URL: str = "https://example.com/privacy"
    INTERNAL_JOB_TOKEN: str | None = None
    EMAIL_SENDER: str = "noreply@example.com"
    CONTACT_RECIPIENT_EMAIL: str = "info@example.com"
    RESEND_API_KEY: str | None = None

    R2_ENDPOINT_URL: str | None = None
    R2_ACCESS_KEY_ID: str | None = None
    R2_SECRET_ACCESS_KEY: str | None = None
    R2_BUCKET_NAME: str | None = None
    R2_PUBLIC_URL: str | None = None

    PAYSTACK_SECRET_KEY: str | None = None
    PAYSTACK_PUBLIC_KEY: str | None = None
    PAYSTACK_BASE_URL: str = "https://api.paystack.co"
    PAYSTACK_CALLBACK_URL: str | None = None
    PAYSTACK_SUBACCOUNT_PERCENTAGE_CHARGE: float = 0.5
    PAYSTACK_BANKS_JSON_PATH: str | None = None

    PREMBLY_SECRET_KEY: str | None = None
    PREMBLY_PUBLIC_KEY: str | None = None
    PREMBLY_BASE_URL: str = "https://api.prembly.com"
    PREMBLY_NIN_PATH: str = "/verification/vnin-basic"
    PREMBLY_TIMEOUT_SECONDS: int = 30

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        """Tortoise/Aerich expect the `postgres://` scheme, not `postgresql://`."""
        if isinstance(value, str) and value.startswith("postgresql://"):
            return "postgres://" + value[len("postgresql://") :]
        return value

    @field_validator(
        "CORS_ORIGINS",
        "TRUSTED_PROXY_IPS",
        "WHATSAPP_MEDIA_ALLOWED_MIME_TYPES",
        "WHATSAPP_MEDIA_FETCH_ALLOWLIST_HOSTS",
        mode="before",
    )
    @classmethod
    def validate_csv_lists(cls, value: str | list[str] | None) -> list[str]:
        """Allow comma-separated strings in env files."""
        return _split_csv(value)

    @model_validator(mode="after")
    def resolve_and_validate_secrets(self) -> Self:
        legacy = self.API_AUTHORIZATION_TOKEN or "change-me"
        if not self.JWT_SECRET_KEY:
            object.__setattr__(self, "JWT_SECRET_KEY", legacy)
        if not self.OTP_HMAC_SECRET:
            object.__setattr__(self, "OTP_HMAC_SECRET", legacy)

        if self.ENVIRONMENT in {"staging", "production"}:
            if self.DEV_OUTBOX_ENABLED:
                raise ValueError(
                    "DEV_OUTBOX_ENABLED must be false in staging and production."
                )
            for name, value in (
                ("JWT_SECRET_KEY", self.JWT_SECRET_KEY),
                ("OTP_HMAC_SECRET", self.OTP_HMAC_SECRET),
            ):
                if _is_weak_secret(value):
                    raise ValueError(
                        f"{name} must be at least {_MIN_SECRET_LENGTH} characters "
                        f"and not a known placeholder when ENVIRONMENT={self.ENVIRONMENT}."
                    )

        if self.WHATSAPP_ENABLED:
            missing = [
                name
                for name, value in (
                    ("WHATSAPP_PHONE_NUMBER_ID", self.WHATSAPP_PHONE_NUMBER_ID),
                    ("WHATSAPP_BUSINESS_ACCOUNT_ID", self.WHATSAPP_BUSINESS_ACCOUNT_ID),
                    ("WHATSAPP_ACCESS_TOKEN", self.WHATSAPP_ACCESS_TOKEN),
                    ("WHATSAPP_APP_ID", self.WHATSAPP_APP_ID),
                    ("WHATSAPP_VERIFY_TOKEN", self.WHATSAPP_VERIFY_TOKEN),
                    ("WHATSAPP_APP_SECRET", self.WHATSAPP_APP_SECRET),
                )
                if not (value or "").strip()
            ]
            if missing:
                raise ValueError(
                    "When WHATSAPP_ENABLED=true the following are required: "
                    + ", ".join(missing)
                )
        return self

    @property
    def display_brand_name(self) -> str:
        return self.BRAND_NAME or self.PROJECT_NAME

    @property
    def support_email(self) -> str:
        return self.SUPPORT_EMAIL or self.CONTACT_RECIPIENT_EMAIL

    def warn_if_weak_local_secrets(self) -> None:
        """Log a startup warning when local dev uses placeholder signing secrets."""
        if self.ENVIRONMENT != "local":
            return
        for name, value in (
            ("JWT_SECRET_KEY", self.JWT_SECRET_KEY),
            ("OTP_HMAC_SECRET", self.OTP_HMAC_SECRET),
        ):
            if _is_weak_secret(value):
                logger.warning(
                    "%s uses a placeholder value; set strong secrets before deploying.",
                    name,
                )

    @property
    def openapi_enabled(self) -> bool:
        return self.ENVIRONMENT == "local" or self.OPENAPI_ENABLED

    @property
    def tortoise_models(self) -> list[str]:
        """Supported Tortoise model modules for the base template."""
        return [
            "aerich.models",
            "app.base.models",
            "app.accounts.models",
            "app.access.models",
            "app.records.models",
            "app.audit.models",
            "app.client_errors.models",
            "app.app_releases.models",
        ]

    @property
    def TORTOISE_CONFIG(self) -> dict[str, Any]:
        """Tortoise configuration consumed by FastAPI and Aerich."""
        return {
            "connections": {"default": self.DATABASE_URL},
            "apps": {
                "models": {
                    "models": self.tortoise_models,
                    "default_connection": "default",
                },
            },
        }


settings = AppSettings()
