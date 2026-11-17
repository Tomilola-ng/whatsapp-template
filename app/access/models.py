"""Access control models: permissions, access roles, and assignments."""

from tortoise import fields, models

from app.base.utils import IDPrefix, PREFIXED_ID_MAX_LENGTH, make_id_default


class Permission(models.Model):
    """Atomic capability (e.g. accounts.edit)."""

    id = fields.CharField(
        pk=True,
        max_length=PREFIXED_ID_MAX_LENGTH,
        default=make_id_default(IDPrefix.PERMISSION),
    )
    codename = fields.CharField(max_length=100, unique=True)
    module = fields.CharField(max_length=50)
    action = fields.CharField(max_length=50)
    description = fields.CharField(max_length=255, null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "permissions"
        indexes = [("module",), ("module", "action")]

    def __str__(self) -> str:
        return self.codename


class AccessRole(models.Model):
    """Named bundle of permissions assignable to any account."""

    id = fields.CharField(
        pk=True,
        max_length=PREFIXED_ID_MAX_LENGTH,
        default=make_id_default(IDPrefix.ACCESS_ROLE),
    )
    slug = fields.CharField(max_length=100, unique=True)
    name = fields.CharField(max_length=255)
    description = fields.TextField(null=True)
    is_system = fields.BooleanField(default=False)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    permissions: fields.ManyToManyRelation["Permission"]

    class Meta:
        table = "access_roles"
        indexes = [("slug",)]

    def __str__(self) -> str:
        return self.slug


class AccessRolePermission(models.Model):
    """Join table: access role ↔ permission."""

    id = fields.CharField(
        pk=True,
        max_length=PREFIXED_ID_MAX_LENGTH,
        default=make_id_default(IDPrefix.ACCESS_ROLE_PERMISSION),
    )
    access_role = fields.ForeignKeyField(
        "models.AccessRole",
        related_name="role_permissions",
        on_delete=fields.CASCADE,
    )
    permission = fields.ForeignKeyField(
        "models.Permission",
        related_name="permission_roles",
        on_delete=fields.CASCADE,
    )

    class Meta:
        table = "access_role_permissions"
        unique_together = (("access_role_id", "permission_id"),)


class AccountAccessRole(models.Model):
    """Assign an access role to an account."""

    id = fields.CharField(
        pk=True,
        max_length=PREFIXED_ID_MAX_LENGTH,
        default=make_id_default(IDPrefix.ACCOUNT_ACCESS_ROLE),
    )
    account = fields.ForeignKeyField(
        "models.Account",
        related_name="account_access_roles",
        on_delete=fields.CASCADE,
    )
    access_role = fields.ForeignKeyField(
        "models.AccessRole",
        related_name="role_accounts",
        on_delete=fields.CASCADE,
    )
    assigned_by = fields.ForeignKeyField(
        "models.Account",
        related_name="assigned_access_roles",
        null=True,
        on_delete=fields.SET_NULL,
    )
    assigned_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "account_access_roles"
        unique_together = (("account_id", "access_role_id"),)


class AccountPermission(models.Model):
    """Direct permission grant or deny for one account."""

    id = fields.CharField(
        pk=True,
        max_length=PREFIXED_ID_MAX_LENGTH,
        default=make_id_default(IDPrefix.ACCOUNT_PERMISSION),
    )
    account = fields.ForeignKeyField(
        "models.Account",
        related_name="account_permissions",
        on_delete=fields.CASCADE,
    )
    permission = fields.ForeignKeyField(
        "models.Permission",
        related_name="permission_accounts",
        on_delete=fields.CASCADE,
    )
    granted = fields.BooleanField(default=True)
    assigned_by = fields.ForeignKeyField(
        "models.Account",
        related_name="assigned_direct_permissions",
        null=True,
        on_delete=fields.SET_NULL,
    )
    assigned_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "account_permissions"
        unique_together = (("account_id", "permission_id"),)
