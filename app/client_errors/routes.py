"""Client error log routes."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status
from fastapi.security import HTTPBearer

from app.access.permissions import require_permission
from app.accounts.auth import get_current_user_optional
from app.accounts.models import Account
from app.base.rate_limit import limiter
from app.client_errors import services as client_error_services
from app.client_errors.schemas import ClientErrorCreate, ClientErrorLogListResponse
from app.config.settings import settings

router = APIRouter(prefix="/client-errors", tags=["Client Errors"])
security = HTTPBearer()

_list_deps: list = []
if settings.ENVIRONMENT == "production":
    _list_deps = [
        Depends(security),
        Depends(require_permission("client_errors.read")),
    ]


@router.post("/", status_code=status.HTTP_200_OK)
@limiter.limit(settings.RATE_LIMIT_CLIENT_ERRORS)
async def ingest_client_error(
    request: Request,
    data: ClientErrorCreate,
    current_user: Annotated[Account | None, Depends(get_current_user_optional)],
):
    """Public ingest for client-reported errors. Optional Bearer attaches the account."""
    return await client_error_services.create_client_error_log(
        data,
        request=request,
        current_user=current_user,
    )


@router.get(
    "/",
    response_model=ClientErrorLogListResponse,
    dependencies=_list_deps,
)
@limiter.limit(settings.RATE_LIMIT_ACCESS)
async def list_client_errors(
    request: Request,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 50,
    flow: str | None = None,
    email: str | None = None,
    account_id: str | None = None,
    created_after: datetime | None = None,
    created_before: datetime | None = None,
):
    """List client errors. Open on local/staging; production requires ``client_errors.read``."""
    _ = request
    return await client_error_services.list_client_error_logs(
        page=page,
        page_size=page_size,
        flow=flow,
        email=email,
        account_id=account_id,
        created_after=created_after,
        created_before=created_before,
    )
