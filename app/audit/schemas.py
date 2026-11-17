"""Audit API schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.audit.enums import AuditActorType


class AuditLogRead(BaseModel):
    id: str
    actor_account_id: str | None = None
    actor_type: AuditActorType
    action: str
    entity_type: str
    entity_id: str | None = None
    metadata: dict[str, Any] | None = None
    idempotency_key: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AuditLogListResponse(BaseModel):
    items: list[AuditLogRead]
    page: int
    page_size: int
    total: int


class AuditLogListQuery(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=100)
    action: str | None = None
    entity_type: str | None = None
    entity_id: str | None = None
    actor_account_id: str | None = None
