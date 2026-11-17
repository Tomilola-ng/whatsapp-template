"""Notification creation and SSE broadcast."""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional

from app.accounts.models import Account
from app.records.enums import NotificationChannel, NotificationType
from app.records.models import Notification

logger = logging.getLogger(__name__)


class NotificationConnectionManager:
    """Manages SSE connections for real-time notifications."""

    def __init__(self) -> None:
        # Account IDs are prefixed strings (ACC...), not UUIDs.
        self.active_connections: Dict[str, List[asyncio.Queue]] = {}

    async def connect(self, user_id: str) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue()
        key = str(user_id)
        if key not in self.active_connections:
            self.active_connections[key] = []
        self.active_connections[key].append(queue)
        return queue

    async def disconnect(self, user_id: str, queue: asyncio.Queue) -> None:
        key = str(user_id)
        if key not in self.active_connections:
            return
        if queue in self.active_connections[key]:
            self.active_connections[key].remove(queue)
        if not self.active_connections[key]:
            del self.active_connections[key]

    async def broadcast_to_user(self, user_id: str, notification_data: dict) -> None:
        key = str(user_id)
        if key not in self.active_connections:
            return
        disconnected_queues: list[asyncio.Queue] = []
        for queue in self.active_connections[key]:
            try:
                await queue.put(notification_data)
            except Exception:
                logger.exception("sse_queue_put_failed user=%s", key)
                disconnected_queues.append(queue)
        for queue in disconnected_queues:
            await self.disconnect(key, queue)


notification_manager = NotificationConnectionManager()


async def create_notification(
    account: Account,
    title: str,
    message: str,
    notification_type: NotificationType = NotificationType.INFO,
    channel: NotificationChannel = NotificationChannel.PUSH,
    action_url: Optional[str] = None,
    broadcast: bool = True,
) -> Notification:
    """Create an in-app notification and optionally deliver via SSE."""
    notification = await Notification.create(
        account=account,
        type=notification_type,
        channel=channel,
        title=title,
        message=message,
        action_url=action_url,
        sent_at=datetime.utcnow(),
    )

    if broadcast and channel == NotificationChannel.PUSH:
        notification_data = {
            "id": str(notification.id),
            "type": notification.type.value,
            "channel": notification.channel.value,
            "title": notification.title,
            "message": notification.message,
            "action_url": notification.action_url,
            "is_read": notification.is_read,
            "sent_at": notification.sent_at.isoformat() if notification.sent_at else None,
            "created_at": notification.created_at.isoformat(),
        }
        try:
            await notification_manager.broadcast_to_user(account.id, notification_data)
        except Exception:
            logger.exception(
                "notification_sse_broadcast_failed account=%s notification=%s",
                account.id,
                notification.id,
            )

    return notification


async def notification_stream(user: Account):
    """SSE stream generator for user notifications."""
    queue = await notification_manager.connect(user.id)

    try:
        yield {
            "event": "connected",
            "data": json.dumps(
                {
                    "message": "Connected to notification stream",
                    "user_id": str(user.id),
                }
            ),
        }

        while True:
            try:
                notification_data = await asyncio.wait_for(queue.get(), timeout=30.0)
                yield {
                    "event": "notification",
                    "data": json.dumps(notification_data),
                }
            except asyncio.TimeoutError:
                yield {
                    "event": "heartbeat",
                    "data": json.dumps({"timestamp": datetime.utcnow().isoformat()}),
                }

    except asyncio.CancelledError:
        logger.info("sse_connection_cancelled user=%s", user.id)
    except Exception:
        logger.exception("sse_stream_error user=%s", user.id)
    finally:
        await notification_manager.disconnect(user.id, queue)
