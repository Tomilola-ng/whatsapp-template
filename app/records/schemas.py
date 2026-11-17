"""Records schemas"""

from typing import Optional
from pydantic import BaseModel, Field
from tortoise.contrib.pydantic import pydantic_model_creator

from app.records.enums import NotificationType
from app.records.models import Notification, OTP

# Pydantic creators for Notification
NotificationFull = pydantic_model_creator(
    Notification,
    name="NotificationFull",
    include=(
        "id",
        "account",
        "type",
        "channel",
        "title",
        "message",
        "action_url",
        "is_read",
        "sent_at",
        "read_at",
        "created_at",
        "updated_at",
    ),
)


class NotificationCreate(BaseModel):
    """
    Schema for creating a new notification.
    """
    type: NotificationType
    title: str
    message: str
    action_url: Optional[str] = None


NotificationUpdate = pydantic_model_creator(
    Notification,
    name="NotificationUpdate",
    include=(
        "type",
        "channel",
        "title",
        "message",
        "action_url",
        "is_read",
        "sent_at",
        "read_at",
    ),
)

# Pydantic creators for OTP
OTPFull = pydantic_model_creator(
    OTP,
    name="OTPFull",
    include=(
        "id",
        "account",
        "code",
        "purpose",
        "status",
        "attempts",
        "max_attempts",
        "expires_at",
        "verified_at",
        "created_at",
        "updated_at",
    ),
)

OTPCreate = pydantic_model_creator(
    OTP,
    name="OTPCreate",
    include=(
        "account",
        "code",
        "purpose",
        "max_attempts",
        "expires_at",
    ),
)

OTPUpdate = pydantic_model_creator(
    OTP,
    name="OTPUpdate",
    include=(
        "code",
        "purpose",
        "status",
        "attempts",
        "max_attempts",
        "expires_at",
        "verified_at",
    ),
)


class StaffNotificationBroadcast(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    message: str = Field(min_length=1, max_length=4000)
    action_url: Optional[str] = Field(default=None, max_length=500)
    account_ids: Optional[list[str]] = None
