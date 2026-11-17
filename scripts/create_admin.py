#!/usr/bin/env python
"""
CLI script — create a new ADMIN account, or promote an existing user to admin.

If the email already exists, the account is updated to ADMIN, optional
name/phone number are applied, and a different email is sent: upgrade notice
plus a setup link with an opaque code to complete admin dashboard access.

Usage:
    uv run python scripts/create_admin.py --email admin@example.com
    uv run python scripts/create_admin.py --email admin@example.com --name "Alice Ade"
    uv run python scripts/create_admin.py --email admin@example.com --phone-number "+1-555-0100"
"""

import argparse
import asyncio
import secrets
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from tortoise import Tortoise

from app.accounts.auth import hash_password
from app.accounts.enums import UserType, UserStatus
from app.accounts.models import Account
from app.accounts.services import _send_admin_upgrade_email, _send_invite_email
from app.access.services import assign_access_roles_to_account, seed_default_access_roles
from app.base.utils import make_id
from app.config.settings import settings

ACCOUNT_ROW_LABEL = "accounts row"


def _user_type_value(user_type: UserType | str | None) -> str:
    if isinstance(user_type, UserType):
        return user_type.value
    if user_type is None:
        return ""
    s = str(user_type).strip().lower()
    if s.lower().startswith("usertype."):
        return s.split(".", 1)[1]
    return s


def _format_account(label: str, account: Account | None) -> None:
    if account is None:
        print(f"  {label}: (no row)")
        return
    ut = _user_type_value(account.user_type)
    print(
        f"  {label}: phone_number={account.phone_number!r}  id={account.id!r}  "
        f"email={account.email!r}  display_name={account.display_name!r}  user_type={ut!r}"
    )


def _split_display_name(display_name: str | None, fallback_email: str) -> tuple[str, str]:
    if display_name and display_name.strip():
        parts = display_name.strip().split()
        if len(parts) == 1:
            return parts[0], "Admin"
        return parts[0], " ".join(parts[1:])
    local_part = fallback_email.split("@", 1)[0].strip() or "Admin"
    return local_part[:1].upper() + local_part[1:], "Admin"


async def _run(
    email: str,
    display_name: str | None,
    phone_number: str | None,
) -> None:
    await Tortoise.init(config=settings.TORTOISE_CONFIG)
    try:
        await seed_default_access_roles()
        email = email.strip().lower()
        phone_number = phone_number.strip() if phone_number and phone_number.strip() else None

        existing = await Account.get_or_none(email=email)
        if phone_number is not None:
            phone_match = await Account.get_or_none(phone_number=phone_number)
            if existing is None:
                existing = phone_match
            elif phone_match is not None and phone_match.id != existing.id:
                print(
                    "ERROR: Email and phone number match different accounts.",
                    file=sys.stderr,
                )
                sys.exit(1)

        print("\n--- initial ---")
        _format_account(ACCOUNT_ROW_LABEL, existing)
        existing_id = existing.id if existing is not None else None
        phone_conflict = False
        if phone_number is not None:
            phone_conflict_query = Account.filter(phone_number=phone_number)
            if existing_id is not None:
                phone_conflict_query = phone_conflict_query.exclude(id=existing_id)
            phone_conflict = await phone_conflict_query.exists()

        if existing is not None:
            old_user_type = _user_type_value(existing.user_type)
            changed: list[str] = []
            if old_user_type != UserType.ADMIN.value:
                existing.user_type = UserType.ADMIN
                changed.append("user_type")
            if existing.status != UserStatus.ACTIVE:
                existing.status = UserStatus.ACTIVE
                changed.append("status")
            if email != existing.email:
                existing.email = email
                changed.append("email")
            if phone_number is not None and phone_number != existing.phone_number:
                existing.phone_number = phone_number
                changed.append("phone_number")
            if display_name is not None and display_name != existing.display_name:
                first_name, last_name = _split_display_name(display_name, email)
                if first_name != existing.first_name:
                    existing.first_name = first_name
                    changed.append("first_name")
                if last_name != existing.last_name:
                    existing.last_name = last_name
                    changed.append("last_name")

            print("\n--- changes ---")
            print(f"  SET user_type = {UserType.ADMIN.value!r} (was {old_user_type!r})")
            if "status" in changed:
                print(f"  SET status = {UserStatus.ACTIVE.value!r}")
            if "email" in changed:
                print(f"  SET email = {email!r}")
            if "phone_number" in changed:
                print(f"  SET phone_number = {phone_number!r}")
            if "first_name" in changed or "last_name" in changed:
                print(f"  SET display_name = {display_name!r}")
            if not changed:
                print("  no field changes required")

            if changed:
                await existing.save(update_fields=[*changed, "updated_at"])

            verified = await Account.get_or_none(id=existing.id)
            got_user_type = _user_type_value(verified.user_type) if verified else ""
            ok = verified is not None and got_user_type == UserType.ADMIN.value
            print("\n--- verified ---")
            print(f"  fields_updated: {len(changed)}")
            print(
                f"  user_type after save: {got_user_type!r}  "
                f"(expected {UserType.ADMIN.value!r})  ok={ok}"
            )
            if not ok:
                print("ERROR: User type not persisted after save.", file=sys.stderr)
                sys.exit(1)

            await assign_access_roles_to_account(
                verified,
                ["super_admin"],
                replace=True,
            )

            print("\n--- updated (new fetch) ---")
            _format_account(ACCOUNT_ROW_LABEL, verified)

            assert verified is not None
            print(
                f"\nSummary: promoted to admin  id={verified.id}  "
                f"phone_number={verified.phone_number!r}  email={verified.email!r}"
            )
            if verified.email:
                await _send_admin_upgrade_email(verified)
                print(f"Admin upgrade email dispatched to {verified.email}")
            else:
                print("WARNING: No email on file — upgrade email not sent.")
            return

        if phone_conflict:
            print(
                f"ERROR: A different account already uses phone number {phone_number!r}.",
                file=sys.stderr,
            )
            sys.exit(1)

        admin_id = make_id("ACC")
        first_name, last_name = _split_display_name(display_name, email)

        print("\n--- changes ---")
        print("  action: CREATE new admin row")
        print(
            f"  phone_number={phone_number!r}  id={admin_id!r}  email={email!r}  "
            f"display_name={display_name!r}  user_type={UserType.ADMIN.value!r}"
        )

        await Account.create(
            id=admin_id,
            email=email,
            phone_number=phone_number,
            first_name=first_name,
            last_name=last_name,
            user_type=UserType.ADMIN,
            status=UserStatus.ACTIVE,
            password=hash_password(secrets.token_urlsafe(24)),
        )

        verified = await Account.get_or_none(email=email)
        got_new = _user_type_value(verified.user_type) if verified else ""
        ok_new = verified is not None and got_new == UserType.ADMIN.value
        print("\n--- verified ---")
        print(f"  row exists after CREATE: {verified is not None}")
        print(
            f"  user_type: {got_new!r}  "
            f"(expected {UserType.ADMIN.value!r})  ok={ok_new}"
        )
        if not ok_new:
            print("ERROR: New admin user type not persisted.", file=sys.stderr)
            sys.exit(1)

        await assign_access_roles_to_account(
            verified,
            ["super_admin"],
            replace=True,
        )

        print("\n--- updated (new fetch) ---")
        _format_account(ACCOUNT_ROW_LABEL, verified)

        assert verified is not None
        print(
            f"\nSummary: created admin  id={verified.id}  "
            f"phone_number={verified.phone_number!r}  email={verified.email!r}"
        )

        if verified.email:
            await _send_invite_email(verified)
            print(f"Invite email dispatched to {verified.email}")
        else:
            print("WARNING: No email address provided — invite email not sent.")
    finally:
        await Tortoise.close_connections()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create an admin account or promote an existing user, then send the invite or upgrade email."
    )
    parser.add_argument(
        "--email",
        required=True,
        help="Admin email address. The invite link will be sent here.",
    )
    parser.add_argument(
        "--phone-number",
        default=None,
        help="Optional admin phone number.",
    )
    parser.add_argument(
        "--name",
        default=None,
        dest="display_name",
        help="Optional display name for the admin account.",
    )

    args = parser.parse_args()
    asyncio.run(
        _run(
            email=args.email,
            display_name=args.display_name,
            phone_number=args.phone_number,
        )
    )


if __name__ == "__main__":
    main()
