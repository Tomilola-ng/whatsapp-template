"""Audit log models."""

from tortoise import fields, models

from app.audit.enums import AuditActorType
from app.base.utils import IDPrefix, PREFIXED_ID_MAX_LENGTH, make_id_default


class AuditLog(models.Model):
    """Append-only security/business audit trail. Table: audit_logs"""

    id = fields.CharField(
        pk=True,
        max_length=PREFIXED_ID_MAX_LENGTH,
        default=make_id_default(IDPrefix.AUDIT_LOG),
    )
    actor_account = fields.ForeignKeyField(
        "models.Account",
        related_name="audit_logs",
        null=True,
        on_delete=fields.SET_NULL,
    )
    actor_type = fields.CharEnumField(AuditActorType, max_length=30)
    action = fields.CharField(max_length=120)
    entity_type = fields.CharField(max_length=120)
    entity_id = fields.CharField(max_length=120, null=True)
    metadata = fields.JSONField(null=True)
    idempotency_key = fields.CharField(max_length=255, null=True, unique=True)
    ip_address = fields.CharField(max_length=80, null=True)
    user_agent = fields.TextField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "audit_logs"
        indexes = [
            ("entity_type", "entity_id"),
            ("actor_account", "created_at"),
            ("action",),
        ]

    def __str__(self) -> str:
        return f"{self.action}:{self.entity_type}:{self.entity_id or '-'}"
