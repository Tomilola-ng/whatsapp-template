"""Accounts enums"""

from enum import Enum


class UserType(str, Enum):
    """Product persona for an account (not the same as access roles)."""
    CUSTOMER = "customer"
    PROVIDER = "provider"
    ADMIN = "admin"


class UserStatus(str, Enum):
    """User account status within the platform."""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"
    DEACTIVATED = "deactivated"
    BANNED = "banned"


# Backward-compatible aliases during template migration.
UserRole = UserType
AccountRole = UserType
