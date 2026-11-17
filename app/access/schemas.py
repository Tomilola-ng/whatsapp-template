"""Access control API schemas."""

from typing import Optional

from pydantic import BaseModel, Field


class PermissionRead(BaseModel):
    id: str
    codename: str
    module: str
    action: str
    description: Optional[str] = None

    class Config:
        from_attributes = True


class AccessRoleRead(BaseModel):
    id: str
    slug: str
    name: str
    description: Optional[str] = None
    is_system: bool
    permission_codenames: list[str] = Field(default_factory=list)

    class Config:
        from_attributes = True


class AccessRoleCreate(BaseModel):
    slug: str = Field(min_length=2, max_length=100)
    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    permission_codenames: list[str] = Field(default_factory=list)


class AccessRoleUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = None
    permission_codenames: Optional[list[str]] = None


class AccountAccessRolesUpdate(BaseModel):
    role_slugs: list[str] = Field(default_factory=list)


class DirectPermissionGrant(BaseModel):
    codename: str
    granted: bool = True


class AccountDirectPermissionsUpdate(BaseModel):
    grants: list[DirectPermissionGrant] = Field(default_factory=list)


class AccountAccessSummary(BaseModel):
    account_id: str
    role_slugs: list[str]
    permissions: list[str]


class MePermissionsRead(BaseModel):
    user_type: str
    permissions: list[str]
