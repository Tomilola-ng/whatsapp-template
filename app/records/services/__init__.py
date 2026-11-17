"""Public records service API."""

from app.records.services.core import (
    get_unread_notification_count,
    list_user_notifications,
    mark_all_notifications_read,
    mark_notification_read,
)

__all__ = [
    "get_unread_notification_count",
    "list_user_notifications",
    "mark_all_notifications_read",
    "mark_notification_read",
]
