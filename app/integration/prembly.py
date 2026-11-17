"""Prembly identity verification integration."""

from typing import Any

import httpx

from app.config.settings import settings


class PremblyError(Exception):
    """Raised when a Prembly API request fails."""

    def __init__(self, message: str, status_code: int | None = None, data: dict | None = None):
        self.message = message
        self.status_code = status_code
        self.data = data or {}
        super().__init__(self.message)


class PremblyService:
    """Thin HTTP wrapper for Prembly verification endpoints."""

    def __init__(
        self,
        *,
        secret_key: str | None = None,
        public_key: str | None = None,
        base_url: str | None = None,
        nin_path: str | None = None,
        timeout_seconds: int | None = None,
    ):
        self.secret_key = secret_key or settings.PREMBLY_SECRET_KEY
        self.public_key = public_key or settings.PREMBLY_PUBLIC_KEY
        self.base_url = (base_url or settings.PREMBLY_BASE_URL).rstrip("/")
        self.nin_path = nin_path or settings.PREMBLY_NIN_PATH
        self.timeout_seconds = timeout_seconds or settings.PREMBLY_TIMEOUT_SECONDS

    def _headers(self) -> dict[str, str]:
        return {
            "accept": "application/json",
            "content-type": "application/json",
            "x-api-key": self.secret_key or "",
            "app-id": self.public_key or "",
        }

    async def verify_nin(self, nin: str) -> dict[str, Any]:
        """
        Verify a provider's identity with Prembly.

        The upstream sample payload only documents ``number``.
        """
        if not self.secret_key:
            raise PremblyError("PREMBLY_SECRET_KEY is not configured")

        payload = {
            "number": nin
        }

        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.post(
                f"{self.base_url}{self.nin_path}",
                headers=self._headers(),
                json=payload,
            )

        body = response.json() if response.content else {}

        if not response.is_success:
            raise PremblyError(
                body.get("message", response.reason_phrase or "Request failed"),
                status_code=response.status_code,
                data=body,
            )
        if not body.get("status"):
            raise PremblyError(
                body.get("message", "Identity verification failed"),
                data=body,
            )

        return body


prembly_service = PremblyService()
