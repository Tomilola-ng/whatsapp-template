"""Accounts models"""

from tortoise import fields, models

from app.accounts.enums import UserType, UserStatus
from app.base.utils import IDPrefix, PREFIXED_ID_MAX_LENGTH, make_id_default


class Account(models.Model):
    """
    Table: accounts
    """

    id = fields.CharField(
        pk=True,
        max_length=PREFIXED_ID_MAX_LENGTH,
        default=make_id_default(IDPrefix.ACCOUNT),
    )

    user_type = fields.CharEnumField(
        UserType, max_length=50, default=UserType.CUSTOMER)
    first_name = fields.CharField(max_length=255, null=True)
    last_name = fields.CharField(max_length=255, null=True)
    image = fields.ForeignKeyField(
        "models.FileAsset", related_name="account_images", to_field="id", null=True, on_delete=fields.SET_NULL
    )

    state = fields.CharField(max_length=255, null=True)
    email = fields.CharField(max_length=255, null=True, unique=True)
    phone_number = fields.CharField(max_length=20, null=True)
    password = fields.CharField(max_length=255, null=True)
    # Optional profile fields (additive to first/last name).
    display_name_override = fields.CharField(max_length=80, null=True)
    username = fields.CharField(max_length=32, null=True, unique=True)

    status = fields.CharEnumField(
        UserStatus, max_length=50, default=UserStatus.PENDING_VERIFICATION)
    last_login_at = fields.DatetimeField(null=True)
    auth_token_version = fields.IntField(default=0)
    permissions_version = fields.IntField(default=0)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        """Meta class for Account model"""
        table = "accounts"
        indexes = [
            ("email",),
            ("user_type",),
            ("status",),
            ("user_type", "status"),
            ("phone_number",),
            ("username",),
        ]

    @property
    def msisdn(self) -> str | None:
        """Compatibility alias for phone number."""
        return self.phone_number

    @property
    def display_name(self) -> str:
        """Override when set; otherwise combined first and last names."""
        override = (self.display_name_override or "").strip()
        if override:
            return override
        return " ".join(
            part for part in [self.first_name, self.last_name] if part
        ).strip()

    @property
    def is_active(self) -> bool:
        """Compatibility alias for active status."""
        return self.status == UserStatus.ACTIVE

    def __str__(self):
        return f"{self.display_name or self.email or self.id} - ({self.user_type})"


class AccountPreferences(models.Model):
    """Generic per-account notification preferences."""

    id = fields.CharField(
        pk=True,
        max_length=PREFIXED_ID_MAX_LENGTH,
        default=make_id_default(IDPrefix.ACCOUNT_PREFERENCE),
    )
    account = fields.OneToOneField(
        "models.Account",
        related_name="preferences",
        on_delete=fields.CASCADE,
    )
    push_enabled = fields.BooleanField(default=True)
    email_notifications_enabled = fields.BooleanField(default=False)
    marketing_email_enabled = fields.BooleanField(default=False)
    email_login_mfa_enabled = fields.BooleanField(default=False)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "account_preferences"
