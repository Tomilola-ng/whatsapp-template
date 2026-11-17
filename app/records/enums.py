"""Records enums"""

from enum import Enum


class NotificationType(str, Enum):
    """Notification type enum"""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


class NotificationChannel(str, Enum):
    """Notification channel enum"""
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"


class OTPPurpose(str, Enum):
    """OTP purpose enum"""
    ACCOUNT_VERIFICATION = "account_verification"
    LOGIN_VERIFICATION = "login_verification"
    PASSWORD_RESET = "password_reset"
    DELIVERY_CONFIRMATION = "delivery_confirmation"


class OTPStatus(str, Enum):
    """OTP status enum"""
    PENDING = "pending"
    USED = "used"
    EXPIRED = "expired"
