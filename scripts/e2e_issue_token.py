#!/usr/bin/env python
"""Mint JWTs for local/E2E tests without going through email/OTP.

Useful when a fork mounts a thin public auth surface, or when CI should
bootstrap an active account without Resend.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import secrets
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from tortoise import Tortoise

from app.access.services import (
    assign_access_roles_to_account,
    build_token_auth_payload,
    seed_default_access_roles,
)
from app.accounts.auth import create_access_token, create_refresh_token, hash_password
from app.accounts.enums import UserStatus, UserType
from app.accounts.models import Account
from app.config.settings import settings


async def _run(email: str, *, admin: bool, first_name: str, last_name: str) -> dict:
    await Tortoise.init(config=settings.TORTOISE_CONFIG)
    try:
        await seed_default_access_roles()
        email = email.strip().lower()
        account = await Account.filter(email=email).first()
        if account is None:
            account = await Account.create(
                email=email,
                first_name=first_name,
                last_name=last_name,
                password=hash_password(secrets.token_urlsafe(24)),
                status=UserStatus.ACTIVE,
                user_type=UserType.ADMIN if admin else UserType.CUSTOMER,
            )
        else:
            account.status = UserStatus.ACTIVE
            if admin:
                account.user_type = UserType.ADMIN
            await account.save()
        if admin:
            await assign_access_roles_to_account(
                account, ["super_admin", "content_admin"]
            )
        else:
            await assign_access_roles_to_account(account, ["customer_basic"])
        payload = await build_token_auth_payload(account)
        access = create_access_token(payload)
        refresh = create_refresh_token({"sub": payload["sub"], "v": payload["v"]})
        return {
            "account_id": account.id,
            "email": account.email,
            "access": access,
            "refresh": refresh,
        }
    finally:
        await Tortoise.close_connections()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create/activate an account and print access + refresh JWTs."
    )
    parser.add_argument("--email", required=True)
    parser.add_argument("--admin", action="store_true")
    parser.add_argument("--first-name", default="E2E")
    parser.add_argument("--last-name", default="User")
    args = parser.parse_args()
    print(
        json.dumps(
            asyncio.run(
                _run(
                    args.email,
                    admin=args.admin,
                    first_name=args.first_name,
                    last_name=args.last_name,
                )
            )
        )
    )


if __name__ == "__main__":
    main()
