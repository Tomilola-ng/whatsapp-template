"""
Paystack integration: initialize and verify transactions.
"""

import json
from typing import Any

import httpx

from app.config.settings import settings


class PaystackError(Exception):
    """Raised when a Paystack API request fails."""

    def __init__(self, message: str, status_code: int | None = None, data: dict | None = None):
        self.message = message
        self.status_code = status_code
        self.data = data or {}
        super().__init__(self.message)


class PaystackService:
    """Service for Paystack transaction initialize and verify."""

    def __init__(
        self,
        *,
        secret_key: str | None = None,
        base_url: str | None = None,
        callback_url: str | None = None,
    ):
        self.secret_key = secret_key or settings.PAYSTACK_SECRET_KEY
        self.base_url = (base_url or settings.PAYSTACK_BASE_URL).rstrip("/")
        self.callback_url = callback_url or settings.PAYSTACK_CALLBACK_URL

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.secret_key}",
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
        }

    async def create_transaction(
        self,
        *,
        email: str,
        amount: int,
        reference: str,
        currency: str = "NGN",
        callback_url: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Initialize a Paystack transaction. Returns authorization_url and reference.

        Args:
            email: Payer email.
            amount: Amount in kobo (e.g. 10247 = 102.47 NGN).
            reference: Unique transaction reference.
            currency: Currency code (default NGN).
            callback_url: Override default callback URL.
            metadata: Optional metadata (e.g. job_id) sent to Paystack and returned on verify.

        Returns:
            Paystack response data (authorization_url, access_code, reference).

        Raises:
            PaystackError: When the API returns status false or non-2xx.
        """
        if not self.secret_key:
            raise PaystackError("PAYSTACK_SECRET_KEY is not configured")

        url = f"{self.base_url}/transaction/initialize"
        cb = callback_url or self.callback_url

        payload: dict[str, str] = {
            "email": email,
            "amount": str(amount),
            "currency": currency,
            "reference": reference,
        }
        if cb:
            payload["callback_url"] = cb
        if metadata is not None:
            payload["metadata"] = json.dumps(metadata)

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers=self._headers(),
                data=payload,
            )

        body = response.json() if response.content else {}
        if not response.is_success:
            raise PaystackError(
                body.get("message", response.reason_phrase or "Request failed"),
                status_code=response.status_code,
                data=body,
            )
        if not body.get("status"):
            raise PaystackError(
                body.get("message", "Initialize failed"),
                data=body.get("data"),
            )

        return body.get("data", {})

    async def verify_transaction(self, reference: str) -> dict[str, Any]:
        """
        Verify a Paystack transaction by reference.

        Args:
            reference: The transaction reference from initialize or checkout.

        Returns:
            Full transaction data (status, amount, metadata, etc.).

        Raises:
            PaystackError: When the API returns status false or non-2xx.
        """
        if not self.secret_key:
            raise PaystackError("PAYSTACK_SECRET_KEY is not configured")

        url = f"{self.base_url}/transaction/verify/{reference}"
        headers = {
            "Authorization": f"Bearer {self.secret_key}",
            "Accept": "application/json",
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)

        body = response.json() if response.content else {}
        if not response.is_success:
            raise PaystackError(
                body.get("message", response.reason_phrase or "Request failed"),
                status_code=response.status_code,
                data=body,
            )
        if not body.get("status"):
            raise PaystackError(
                body.get("message", "Verification failed"),
                data=body.get("data"),
            )

        return body.get("data", {})

    async def create_subaccount(
        self,
        *,
        business_name: str,
        bank_code: str,
        account_number: str,
        percentage_charge: float,
        primary_contact_email: str | None = None,
        primary_contact_name: str | None = None,
        primary_contact_phone: str | None = None,
        category: str = "Logistics",
        settlement_schedule: str = "manual",
    ) -> dict[str, Any]:
        """
        Create a Paystack subaccount for a provider settlement account.

        Args:
            business_name: Business display name on Paystack.
            bank_code: Paystack settlement bank code.
            account_number: Settlement account number.
            percentage_charge: Platform commission percentage.
            primary_contact_email: Optional provider email.
            primary_contact_name: Optional provider name.
            primary_contact_phone: Optional provider phone.
            category: Paystack business category.
            settlement_schedule: Paystack settlement schedule.

        Returns:
            Subaccount payload from Paystack.

        Raises:
            PaystackError: When the API returns status false or non-2xx.
        """
        if not self.secret_key:
            raise PaystackError("PAYSTACK_SECRET_KEY is not configured")

        payload: dict[str, str] = {
            "business_name": business_name,
            "settlement_bank": bank_code,
            "account_number": account_number,
            "percentage_charge": str(percentage_charge),
            "category": category,
            "settlement_schedule": settlement_schedule,
        }
        if primary_contact_email:
            payload["primary_contact_email"] = primary_contact_email
        if primary_contact_name:
            payload["primary_contact_name"] = primary_contact_name
        if primary_contact_phone:
            payload["primary_contact_phone"] = primary_contact_phone

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/subaccount",
                headers=self._headers(),
                data=payload,
            )

        body = response.json() if response.content else {}
        if not response.is_success:
            raise PaystackError(
                body.get("message", response.reason_phrase or "Request failed"),
                status_code=response.status_code,
                data=body,
            )
        if not body.get("status"):
            raise PaystackError(
                body.get("message", "Subaccount creation failed"),
                data=body.get("data"),
            )

        return body.get("data", {})

    async def resolve_bank_account_raw(
        self,
        *,
        account_number: str,
        bank_code: str,
    ) -> dict[str, Any]:
        """
        Call Paystack ``GET /bank/resolve``.

        Returns the full JSON body (including ``status: false`` for validation errors).
        Raises PaystackError only for HTTP/network failures or missing configuration.
        """
        if not self.secret_key:
            raise PaystackError("PAYSTACK_SECRET_KEY is not configured")

        url = f"{self.base_url}/bank/resolve"
        headers = {
            "Authorization": f"Bearer {self.secret_key}",
            "Accept": "application/json",
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers=headers,
                params={
                    "account_number": account_number,
                    "bank_code": bank_code,
                },
            )

        body = response.json() if response.content else {}
        if not response.is_success:
            raise PaystackError(
                body.get("message", response.reason_phrase or "Request failed"),
                status_code=response.status_code,
                data=body,
            )
        return body


# Singleton for app use
paystack_service = PaystackService()
