"""Client error log request/response schemas."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, EmailStr, Field


class ClientErrorCreate(BaseModel):
    """Public ingest body. Only ``message`` is required."""

    message: str = Field(min_length=1, max_length=4000)
    flow: Optional[str] = Field(default=None, max_length=120)
    screen: Optional[str] = Field(default=None, max_length=255)
    email: Optional[EmailStr] = None
    account_id: Optional[str] = Field(default=None, max_length=50)
    platform: Optional[str] = Field(default=None, max_length=40)
    app_version: Optional[str] = Field(default=None, max_length=80)
    client_timestamp: Optional[datetime] = None
    stack: Optional[str] = Field(default=None, max_length=8000)
    metadata: Optional[dict[str, Any]] = None


class ClientErrorLogRead(BaseModel):
    id: str
    message: str
    flow: Optional[str] = None
    screen: Optional[str] = None
    email: Optional[str] = None
    account_id: Optional[str] = None
    platform: Optional[str] = None
    app_version: Optional[str] = None
    client_timestamp: Optional[datetime] = None
    stack: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ClientErrorLogListResponse(BaseModel):
    items: list[ClientErrorLogRead]
    page: int
    page_size: int
    total: int
