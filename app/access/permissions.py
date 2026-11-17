"""JWT-based permission guards (no database lookup for decode; version check on enforce)."""

from collections.abc import Iterable
from dataclasses import dataclass

from fastapi import Depends, Header, HTTPException, status

from app.access.utils import check_permission
from app.accounts.auth import _bearer_token_from_authorization, decode_token
from app.accounts.enums import UserStatus, UserType
from app.accounts.models import Account


@dataclass(frozen=True, slots=True)
class TokenAuth:
    """Decoded access-token authorization context."""

    sub: str
    user_type: str
    perms: tuple[str, ...]
    token_version: int
    permissions_version: int


def _decode_token_auth(authorization: str | None) -> TokenAuth:
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    token = _bearer_token_from_authorization(authorization)
    if not token:
        raise HTTPException(status_code=401, detail="Invalid authorization scheme")

    payload = decode_token(token)
    if payload.get("scope") != "access_token":
        raise HTTPException(status_code=401, detail="Invalid token scope")

    sub = payload.get("sub")
    if not sub:
        raise HTTPException(status_code=401, detail="Missing user ID in token")

    perms_raw = payload.get("perms") or []
    if not isinstance(perms_raw, list):
        raise HTTPException(status_code=401, detail="Invalid permissions claim")

    if "v" not in payload or "pv" not in payload:
        raise HTTPException(status_code=401, detail="Invalid token version")

    return TokenAuth(
        sub=str(sub),
        user_type=str(payload.get("ut") or UserType.CUSTOMER.value),
        perms=tuple(str(p) for p in perms_raw),
        token_version=int(payload["v"]),
        permissions_version=int(payload["pv"]),
    )


def get_token_auth(authorization: str | None = Header(None)) -> TokenAuth:
    """Decode JWT claims without a database lookup."""
    return _decode_token_auth(authorization)


async def get_validated_token_auth(
    authorization: str | None = Header(None),
) -> TokenAuth:
    """Decode JWT and verify session versions and active status against the database."""
    auth = _decode_token_auth(authorization)
    account = await Account.filter(id=auth.sub).first()
    if not account:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    if account.status != UserStatus.ACTIVE:
        raise HTTPException(status_code=403, detail="User is not active.")
    if auth.token_version != int(account.auth_token_version):
        raise HTTPException(status_code=401, detail="Session expired or revoked")
    if auth.permissions_version != int(account.permissions_version):
        raise HTTPException(status_code=401, detail="Session expired or revoked")
    return auth


def require_permission(codename: str):
    """FastAPI dependency factory: require permission with live session validation."""

    async def _dependency(
        auth: TokenAuth = Depends(get_validated_token_auth),
    ) -> TokenAuth:
        if not check_permission(codename, auth.perms):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action.",
            )
        return auth

    return _dependency


def require_any_permission(*codenames: str):
    """FastAPI dependency factory: require any one of the listed permissions."""

    async def _dependency(
        auth: TokenAuth = Depends(get_validated_token_auth),
    ) -> TokenAuth:
        if any(check_permission(code, auth.perms) for code in codenames):
            return auth
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to perform this action.",
        )

    return _dependency


def require_user_type(allowed: Iterable[UserType]):
    """FastAPI dependency factory: require user_type claim from JWT."""

    allowed_values = {t.value for t in allowed}

    async def _dependency(
        auth: TokenAuth = Depends(get_validated_token_auth),
    ) -> TokenAuth:
        if auth.user_type not in allowed_values:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action.",
            )
        return auth

    return _dependency
