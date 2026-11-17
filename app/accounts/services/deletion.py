"""Starter-scoped, retention-friendly account deletion."""

import secrets
from typing import Any

from fastapi import HTTPException, status
from tortoise.transactions import in_transaction

from app.access.models import AccountAccessRole, AccountPermission
from app.accounts.auth import hash_password
from app.accounts.enums import UserStatus
from app.accounts.models import Account, AccountPreferences
from app.accounts.schemas import AccountDeleteRequest
from app.base.responses import success_response
from app.client_errors.models import ClientErrorLog
from app.records.models import Notification, OTP, PasswordSetupCode

ACCOUNT_DELETE_CONFIRMATION_PHRASE = "DELETE MY ACCOUNT"


async def delete_account(account: Account, data: AccountDeleteRequest) -> dict[str, Any]:
    if data.confirm is not True or (data.confirmation_phrase or "").strip() != ACCOUNT_DELETE_CONFIRMATION_PHRASE:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "account_deletion_confirmation_required",
                "required_confirmation_phrase": ACCOUNT_DELETE_CONFIRMATION_PHRASE,
            },
        )

    async with in_transaction() as conn:
        locked = await Account.filter(id=account.id).using_db(conn).select_for_update().first()
        if not locked:
            raise HTTPException(status_code=404, detail="Account not found.")
        if locked.status == UserStatus.DEACTIVATED:
            return success_response(
                data={"account_id": locked.id, "already_deleted": True},
                message="Account already deleted",
            )

        locked.status = UserStatus.DEACTIVATED
        locked.auth_token_version = int(locked.auth_token_version or 0) + 1
        locked.permissions_version = int(locked.permissions_version or 0) + 1
        locked.first_name = None
        locked.last_name = None
        locked.display_name_override = None
        locked.username = None
        locked.email = f"deleted-{locked.id.lower()}@deleted.invalid"
        locked.phone_number = None
        locked.state = None
        locked.image_id = None
        locked.password = hash_password(secrets.token_urlsafe(48))
        await locked.save(using_db=conn)

    purge = {
        "preferences": await AccountPreferences.filter(account_id=account.id).delete(),
        "notifications": await Notification.filter(account_id=account.id).delete(),
        "otps": await OTP.filter(account_id=account.id).delete(),
        "password_setup_codes": await PasswordSetupCode.filter(account_id=account.id).delete(),
        "access_roles": await AccountAccessRole.filter(account_id=account.id).delete(),
        "permissions": await AccountPermission.filter(account_id=account.id).delete(),
        "client_errors": await ClientErrorLog.filter(account_id=account.id).update(account_id=None),
    }
    return success_response(
        data={"account_id": locked.id, "already_deleted": False, "purge": purge},
        message="Account deleted",
    )
