"""Accounts checkers"""

from app.accounts.enums import UserType, UserStatus
from app.accounts.models import Account


def is_admin(user: Account) -> bool:
    """Return True when the account has the admin user type."""
    return user.user_type == UserType.ADMIN


def is_customer(user: Account) -> bool:
    """Return True when the account has the customer user type."""
    return user.user_type == UserType.CUSTOMER


def is_provider(user: Account) -> bool:
    """Return True when the account has the provider user type."""
    return user.user_type == UserType.PROVIDER


def is_active(user: Account) -> bool:
    """Return True when the account status is active."""
    return user.status == UserStatus.ACTIVE
