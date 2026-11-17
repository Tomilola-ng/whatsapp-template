"""Minimal staff notification broadcast endpoint."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import HTTPBearer

from app.access.permissions import require_permission
from app.accounts.models import Account
from app.accounts.permissions import get_current_active_user
from app.accounts.enums import UserStatus
from app.audit.enums import AuditActorType
from app.audit.services import record_audit_event
from app.base.responses import success_response
from app.records.enums import NotificationChannel, NotificationType
from app.records.notification_service import create_notification
from app.records.schemas import StaffNotificationBroadcast

logger = logging.getLogger(__name__)
security = HTTPBearer()
router = APIRouter(prefix="/admin/notifications", tags=["Administration"])


@router.post(
    "/broadcast",
    dependencies=[
        Depends(security),
        Depends(require_permission("notifications.broadcast")),
    ],
)
async def broadcast_notification(
    data: StaffNotificationBroadcast,
    staff: Annotated[Account, Depends(get_current_active_user)],
):
    query = Account.filter(status=UserStatus.ACTIVE)
    if data.account_ids is not None:
        query = query.filter(id__in=data.account_ids)
    recipients = await query.all()
    created = 0
    failed = 0
    for recipient in recipients:
        try:
            await create_notification(
                recipient,
                data.title,
                data.message,
                NotificationType.INFO,
                NotificationChannel.PUSH,
                data.action_url,
            )
            created += 1
        except Exception:
            failed += 1
            logger.exception("notification_broadcast_failed account=%s", recipient.id)
    await record_audit_event(
        action="admin.notifications.broadcast",
        entity_type="notification",
        actor_type=AuditActorType.ACCOUNT,
        actor_account_id=staff.id,
        metadata={
            "title": data.title,
            "recipient_count": len(recipients),
            "created_count": created,
            "failed_count": failed,
        },
    )
    return success_response(
        data={
            "recipient_count": len(recipients),
            "created_count": created,
            "failed_count": failed,
        },
        message="Notifications broadcast",
    )
