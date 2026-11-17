"""Notification Routes"""

from typing import Annotated, List

from fastapi import (
    APIRouter,
    status,
    Depends,
    Query,
    Path,
    Request,
)
from fastapi.security import HTTPBearer
from starlette.responses import StreamingResponse

from app.accounts.models import Account
from app.access.permissions import require_permission
from app.accounts.permissions import get_current_active_user
from app.records import services as record_services
from app.records.schemas import (
    NotificationFull,
)
from app.records.notification_service import notification_stream

security = HTTPBearer()
router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get(
    "/",
    response_model=List[NotificationFull],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(security), Depends(require_permission("notifications.read"))],
)
async def get_notifications(
    current_user: Annotated[Account, Depends(get_current_active_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
):
    """
    Get all notifications for the logged-in user.

    - Returns notifications ordered by created_at descending (most recent first)
    - Supports pagination
    """
    return await record_services.list_user_notifications(
        current_user,
        page=page,
        page_size=page_size,
    )


@router.get("/unread-count", dependencies=[Depends(security)])
async def get_unread_notification_count(
    current_user: Annotated[Account, Depends(get_current_active_user)],
):
    return await record_services.get_unread_notification_count(current_user)


@router.post("/mark-all-read", dependencies=[Depends(security)])
async def mark_all_notifications_read(
    current_user: Annotated[Account, Depends(get_current_active_user)],
):
    return await record_services.mark_all_notifications_read(current_user)


@router.get("/stream", dependencies=[Depends(security)])
async def stream_notifications(
    request: Request,
    current_user: Annotated[Account, Depends(get_current_active_user)],
):
    async def encoded_events():
        async for event in notification_stream(current_user):
            if await request.is_disconnected():
                break
            yield f"event: {event['event']}\ndata: {event['data']}\n\n"

    return StreamingResponse(
        encoded_events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.patch(
    "/{notification_id}/read",
    response_model=NotificationFull,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(security), Depends(require_permission("notifications.read"))],
    responses={
        404: {"description": "Notification not found"},
        403: {"description": "Not authorized to modify this notification"},
    },
)
async def mark_notification_as_read(
    notification_id: Annotated[str, Path(...)],
    current_user: Annotated[Account, Depends(get_current_active_user)],
):
    """
    Mark a notification as read.

    - Only the notification owner can mark it as read
    - Updates is_read to True
    - Sets read_at to current timestamp
    """
    return await record_services.mark_notification_read(
        notification_id,
        current_user,
    )
