"""Audit domain enums."""

from enum import Enum


class AuditActorType(str, Enum):
    ACCOUNT = "account"
    SYSTEM = "system"
    PUBLIC = "public"
