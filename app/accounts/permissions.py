"""Account-scoped route guards (active status and user type)."""

from collections.abc import Iterable

from fastapi import Depends, HTTPException, status

from app.accounts.auth import get_current_user, get_current_user_optional
from app.accounts.enums import UserType, UserStatus
from app.accounts.models import Account


def require_user_type_on_account(user: Account, allowed: Iterable[UserType]) -> None:
    """Require the account user_type to be included in the allowed set."""
    allowed_types = set(allowed)
    if user.user_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to perform this action.",
        )


def require_admin(user: Account) -> None:
    """Require an admin user type."""
    require_user_type_on_account(user, [UserType.ADMIN])


def require_provider(user: Account) -> None:
    """Require a provider user type."""
    require_user_type_on_account(user, [UserType.PROVIDER])


def require_customer(user: Account) -> None:
    """Require a customer user type."""
    require_user_type_on_account(user, [UserType.CUSTOMER])


def require_active_account(user: Account) -> None:
    """Reject accounts that are not currently active."""
    if user.status == UserStatus.ACTIVE:
        return

    status_reasons = {
        UserStatus.SUSPENDED: "User is suspended.",
        UserStatus.DEACTIVATED: "User is deactivated.",
        UserStatus.BANNED: "User is banned.",
        UserStatus.PENDING_VERIFICATION: "User is pending verification.",
    }
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=status_reasons.get(user.status, "User is not active."),
    )


def get_current_admin(
    current_user: Account = Depends(get_current_user),
) -> Account:
    """FastAPI dependency returning the current admin account."""
    require_active_account(current_user)
    require_admin(current_user)
    return current_user


def get_current_provider(
    current_user: Account = Depends(get_current_user),
) -> Account:
    """FastAPI dependency returning the current provider account."""
    require_active_account(current_user)
    require_provider(current_user)
    return current_user


def get_current_active_user(
    current_user: Account = Depends(get_current_user),
) -> Account:
    """Current user that must be in an active account status."""
    require_active_account(current_user)
    return current_user


def get_current_active_user_optional(
    current_user: Account | None = Depends(get_current_user_optional),
) -> Account | None:
    """Active user when authenticated; None for anonymous requests."""
    if current_user is None:
        return None
    require_active_account(current_user)
    return current_user


def get_current_customer(
    current_user: Account = Depends(get_current_user),
) -> Account:
    """FastAPI dependency returning the current customer account."""
    require_active_account(current_user)
    require_customer(current_user)
    return current_user
