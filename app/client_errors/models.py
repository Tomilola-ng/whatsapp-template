"""Client error log models."""

from tortoise import fields, models

from app.base.utils import IDPrefix, PREFIXED_ID_MAX_LENGTH, make_id_default


class ClientErrorLog(models.Model):
    """Append-only client-reported errors. Table: client_error_logs"""

    id = fields.CharField(
        pk=True,
        max_length=PREFIXED_ID_MAX_LENGTH,
        default=make_id_default(IDPrefix.CLIENT_ERROR_LOG),
    )
    message = fields.CharField(max_length=4000)
    flow = fields.CharField(max_length=120, null=True)
    screen = fields.CharField(max_length=255, null=True)
    email = fields.CharField(max_length=255, null=True)
    account = fields.ForeignKeyField(
        "models.Account",
        related_name="client_error_logs",
        null=True,
        on_delete=fields.SET_NULL,
    )
    platform = fields.CharField(max_length=40, null=True)
    app_version = fields.CharField(max_length=80, null=True)
    client_timestamp = fields.DatetimeField(null=True)
    stack = fields.TextField(null=True)
    metadata = fields.JSONField(null=True)
    ip_address = fields.CharField(max_length=80, null=True)
    user_agent = fields.TextField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "client_error_logs"
        indexes = [
            ("flow", "created_at"),
            ("email",),
            ("account", "created_at"),
            ("created_at",),
        ]

    def __str__(self) -> str:
        return f"{self.flow or 'unknown'}:{self.message[:60]}"
