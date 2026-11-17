"""Admin audit-log inspection routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from fastapi.security import HTTPBearer

from app.access.permissions import require_permission
from app.audit.schemas import AuditLogListResponse
from app.audit import services as audit_services
from app.base.rate_limit import limiter
from app.config.settings import settings

router = APIRouter(prefix="/admin", tags=["Administration"])
security = HTTPBearer()


@router.get(
    "/audit-logs",
    response_model=AuditLogListResponse,
    dependencies=[Depends(security), Depends(require_permission("audit_logs.read"))],
)
@limiter.limit(settings.RATE_LIMIT_ACCESS)
async def get_audit_logs(
    request: Request,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 50,
    action: str | None = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
    actor_account_id: str | None = None,
):
    """List append-only audit logs for authorized platform staff."""
    _ = request
    return await audit_services.list_audit_logs(
        page=page,
        page_size=page_size,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        actor_account_id=actor_account_id,
    )
