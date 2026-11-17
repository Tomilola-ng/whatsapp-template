"""Records models"""

from tortoise import fields, models

from app.base.utils import IDPrefix, PREFIXED_ID_MAX_LENGTH, make_id_default
from app.records.enums import (
    NotificationType,
    NotificationChannel,
    OTPPurpose,
    OTPStatus,
)


class Notification(models.Model):
    """
    Table: notifications
    """

    id = fields.CharField(
        pk=True,
        max_length=PREFIXED_ID_MAX_LENGTH,
        default=make_id_default(IDPrefix.NOTIFICATION),
    )
    account = fields.ForeignKeyField(
        "models.Account", related_name="notifications", on_delete=fields.CASCADE
    )
    type = fields.CharEnumField(
        NotificationType, max_length=20, default=NotificationType.INFO
    )
    channel = fields.CharEnumField(
        NotificationChannel, max_length=20, default=NotificationChannel.PUSH
    )
    title = fields.CharField(max_length=255)
    message = fields.TextField()
    action_url = fields.CharField(max_length=500, null=True)
    is_read = fields.BooleanField(default=False)
    sent_at = fields.DatetimeField(null=True)
    read_at = fields.DatetimeField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True, null=True)

    class Meta:
        """Notification model meta"""
        table = "notifications"
        indexes = [
            ("account",),
            ("is_read",),
            ("created_at",),
        ]


class OTP(models.Model):
    """
    Table: otps
    """

    id = fields.CharField(
        pk=True,
        max_length=PREFIXED_ID_MAX_LENGTH,
        default=make_id_default(IDPrefix.OTP),
    )
    account = fields.ForeignKeyField(
        "models.Account", related_name="otps", on_delete=fields.CASCADE
    )
    code = fields.CharField(max_length=10, null=True)
    code_hash = fields.CharField(max_length=64, null=True)
    purpose = fields.CharEnumField(
        OTPPurpose, max_length=50, default=OTPPurpose.ACCOUNT_VERIFICATION
    )
    status = fields.CharEnumField(
        OTPStatus, max_length=20, default=OTPStatus.PENDING)
    attempts = fields.IntField(default=0)
    max_attempts = fields.IntField(default=3)
    expires_at = fields.DatetimeField()
    verified_at = fields.DatetimeField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True, null=True)

    class Meta:
        """OTP model meta"""
        table = "otps"
        indexes = [
            ("account", "purpose", "status"),
            ("expires_at",),
        ]


class PasswordSetupCode(models.Model):
    """One-time opaque code for admin password setup links."""

    id = fields.CharField(
        pk=True,
        max_length=PREFIXED_ID_MAX_LENGTH,
        default=make_id_default(IDPrefix.OTP),
    )
    account = fields.ForeignKeyField(
        "models.Account", related_name="password_setup_codes", on_delete=fields.CASCADE
    )
    code_hash = fields.CharField(max_length=64)
    expires_at = fields.DatetimeField()
    used_at = fields.DatetimeField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "password_setup_codes"
        indexes = [
            ("account",),
            ("expires_at",),
        ]
