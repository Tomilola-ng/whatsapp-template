"""Audit service orchestration."""

from __future__ import annotations

import logging
from typing import Any

from tortoise.backends.base.client import BaseDBAsyncClient
from tortoise.expressions import Q

from app.audit.enums import AuditActorType
from app.audit.models import AuditLog
from app.audit.schemas import AuditLogListResponse, AuditLogRead
from app.audit.utils import redact_audit_metadata

logger = logging.getLogger(__name__)


async def record_audit_event(
    *,
    action: str,
    entity_type: str,
    entity_id: str | None = None,
    actor_type: AuditActorType = AuditActorType.SYSTEM,
    actor_account_id: str | None = None,
    metadata: dict[str, Any] | None = None,
    idempotency_key: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    using_db: BaseDBAsyncClient | None = None,
) -> AuditLog:
    """Append an audit row. Safe for use inside Tortoise transactions via ``using_db``.

    When ``idempotency_key`` is set, a matching existing row is returned instead of
    inserting a duplicate (replay-safe for financial/support mutations).
    """
    if not action or not action.strip():
        raise ValueError("action is required")
    if not entity_type or not entity_type.strip():
        raise ValueError("entity_type is required")

    action = action.strip()
    entity_type = entity_type.strip()
    entity_id = entity_id.strip() if entity_id else None
    idempotency_key = idempotency_key.strip() if idempotency_key else None

    if idempotency_key:
        query = AuditLog.filter(idempotency_key=idempotency_key)
        if using_db is not None:
            query = query.using_db(using_db)
        existing = await query.first()
        if existing:
            return existing

    try:
        safe_metadata = redact_audit_metadata(metadata)
        create_kwargs: dict[str, Any] = {
            "actor_type": actor_type,
            "action": action,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "metadata": safe_metadata,
            "idempotency_key": idempotency_key,
            "ip_address": ip_address,
            "user_agent": user_agent,
        }
        if actor_account_id:
            create_kwargs["actor_account_id"] = actor_account_id
        if using_db is not None:
            return await AuditLog.create(**create_kwargs, using_db=using_db)
        return await AuditLog.create(**create_kwargs)
    except Exception:
        logger.exception(
            "audit_write_failed action=%s entity_type=%s entity_id=%s",
            action,
            entity_type,
            entity_id,
        )
        raise


async def list_audit_logs(
    *,
    page: int = 1,
    page_size: int = 50,
    action: str | None = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
    actor_account_id: str | None = None,
) -> AuditLogListResponse:
    """Paginated staff inspection of audit logs."""
    filters = Q()
    if action:
        filters &= Q(action=action)
    if entity_type:
        filters &= Q(entity_type=entity_type)
    if entity_id:
        filters &= Q(entity_id=entity_id)
    if actor_account_id:
        filters &= Q(actor_account_id=actor_account_id)

    query = AuditLog.filter(filters)
    total = await query.count()
    offset = (page - 1) * page_size
    rows = await query.order_by("-created_at").offset(offset).limit(page_size)
    items = [
        AuditLogRead(
            id=row.id,
            actor_account_id=row.actor_account_id,
            actor_type=row.actor_type,
            action=row.action,
            entity_type=row.entity_type,
            entity_id=row.entity_id,
            metadata=row.metadata,
            idempotency_key=row.idempotency_key,
            ip_address=row.ip_address,
            user_agent=row.user_agent,
            created_at=row.created_at,
        )
        for row in rows
    ]
    return AuditLogListResponse(
        items=items, page=page, page_size=page_size, total=total
    )
