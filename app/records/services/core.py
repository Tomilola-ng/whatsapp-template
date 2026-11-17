"""Service-layer helpers for notifications and record-oriented flows."""

from datetime import datetime, timezone

from fastapi import HTTPException

from app.accounts.models import Account
from app.records.models import Notification
from app.records.schemas import NotificationFull
from app.base.responses import success_response


async def list_user_notifications(
    current_user: Account,
    *,
    page: int = 1,
    page_size: int = 20,
) -> list[NotificationFull]:
    """Return paginated notifications for the authenticated user."""
    offset = (page - 1) * page_size
    notifications = await Notification.filter(account_id=current_user.id).order_by(
        "-created_at"
    ).offset(offset).limit(page_size)
    return [NotificationFull.model_validate(item) for item in notifications]


async def mark_notification_read(
    notification_id: str,
    current_user: Account,
) -> NotificationFull:
    """Mark a notification as read for its owner."""
    notification = await Notification.get_or_none(id=notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    if notification.account_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to modify this notification",
        )

    notification.is_read = True
    notification.read_at = datetime.now(timezone.utc)
    await notification.save()
    return NotificationFull.model_validate(notification)


async def get_unread_notification_count(current_user: Account) -> dict:
    count = await Notification.filter(
        account_id=current_user.id, is_read=False
    ).count()
    return success_response(
        data={"unread_count": count}, message="Unread notification count"
    )


async def mark_all_notifications_read(current_user: Account) -> dict:
    now = datetime.now(timezone.utc)
    updated = await Notification.filter(
        account_id=current_user.id, is_read=False
    ).update(is_read=True, read_at=now)
    return success_response(
        data={"updated_count": updated}, message="Notifications marked read"
    )
