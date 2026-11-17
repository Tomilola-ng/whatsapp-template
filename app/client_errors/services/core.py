"""Client error log service workflows."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import Request
from tortoise.expressions import Q

from app.accounts.models import Account
from app.base.client_ip import client_ip
from app.base.redaction import redact_exception_message, redact_for_log
from app.client_errors.models import ClientErrorLog
from app.client_errors.schemas import (
    ClientErrorCreate,
    ClientErrorLogListResponse,
    ClientErrorLogRead,
)

_STACK_MAX = 8000


def _clean_optional(value: str | None, *, max_len: int) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    if not cleaned:
        return None
    return cleaned[:max_len]


def _to_read(row: ClientErrorLog) -> ClientErrorLogRead:
    return ClientErrorLogRead(
        id=row.id,
        message=row.message,
        flow=row.flow,
        screen=row.screen,
        email=row.email,
        account_id=row.account_id,
        platform=row.platform,
        app_version=row.app_version,
        client_timestamp=row.client_timestamp,
        stack=row.stack,
        metadata=row.metadata,
        ip_address=row.ip_address,
        user_agent=row.user_agent,
        created_at=row.created_at,
    )


async def create_client_error_log(
    data: ClientErrorCreate,
    *,
    request: Request,
    current_user: Account | None = None,
) -> dict[str, Any]:
    """Persist a client-reported error. Resilient: bad account_id is ignored."""
    account: Account | None = current_user
    if account is None and data.account_id:
        account = await Account.filter(id=data.account_id.strip()).first()

    email = str(data.email).strip().lower() if data.email else None
    if email is None and account and account.email:
        email = account.email

    stack = _clean_optional(data.stack, max_len=_STACK_MAX)
    row = await ClientErrorLog.create(
        message=redact_exception_message(data.message, max_length=4000) or "Client error",
        flow=_clean_optional(data.flow, max_len=120),
        screen=_clean_optional(data.screen, max_len=255),
        email=email,
        account=account,
        platform=_clean_optional(data.platform, max_len=40),
        app_version=_clean_optional(data.app_version, max_len=80),
        client_timestamp=data.client_timestamp,
        stack=redact_exception_message(stack, max_length=_STACK_MAX),
        metadata=redact_for_log(data.metadata),
        ip_address=client_ip(request)[:80],
        user_agent=(request.headers.get("user-agent") or None),
    )
    return {
        "message": "Client error logged",
        "data": _to_read(row),
    }


async def list_client_error_logs(
    *,
    page: int = 1,
    page_size: int = 50,
    flow: str | None = None,
    email: str | None = None,
    account_id: str | None = None,
    created_after: datetime | None = None,
    created_before: datetime | None = None,
) -> ClientErrorLogListResponse:
    """Paginated inspection of client error logs (newest first)."""
    filters = Q()
    if flow:
        filters &= Q(flow=flow.strip())
    if email:
        filters &= Q(email=email.strip().lower())
    if account_id:
        filters &= Q(account_id=account_id.strip())
    if created_after is not None:
        filters &= Q(created_at__gte=created_after)
    if created_before is not None:
        filters &= Q(created_at__lte=created_before)

    query = ClientErrorLog.filter(filters)
    total = await query.count()
    offset = (page - 1) * page_size
    rows = await query.order_by("-created_at").offset(offset).limit(page_size)
    return ClientErrorLogListResponse(
        items=[_to_read(row) for row in rows],
        page=page,
        page_size=page_size,
        total=total,
    )
