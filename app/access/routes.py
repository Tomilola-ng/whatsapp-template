"""Access control management routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer

from app.access.models import AccessRolePermission
from app.access.permissions import (
    TokenAuth,
    get_validated_token_auth,
    require_permission,
)
from app.access.schemas import (
    AccessRoleCreate,
    AccessRoleRead,
    AccessRoleUpdate,
    AccountAccessRolesUpdate,
    AccountAccessSummary,
    AccountDirectPermissionsUpdate,
    MePermissionsRead,
    PermissionRead,
)
from app.access import services as access_services
from app.accounts.models import Account
from app.accounts.permissions import get_current_active_user
from app.base.rate_limit import limiter
from app.config.settings import settings

router = APIRouter(prefix="/access", tags=["Access Control"])
security = HTTPBearer()


async def _role_to_read(role) -> AccessRoleRead:
    links = await AccessRolePermission.filter(
        access_role=role
    ).prefetch_related("permission")
    codenames = sorted(link.permission.codename for link in links)
    return AccessRoleRead(
        id=role.id,
        slug=role.slug,
        name=role.name,
        description=role.description,
        is_system=role.is_system,
        permission_codenames=codenames,
    )


@router.get(
    "/me/permissions",
    response_model=MePermissionsRead,
    dependencies=[Depends(security)],
)
@limiter.limit(settings.RATE_LIMIT_ACCESS)
async def get_my_permissions(
    request: Request,
    auth: Annotated[TokenAuth, Depends(get_validated_token_auth)],
):
    """Return effective permissions embedded in the current access token."""
    _ = request
    return MePermissionsRead(user_type=auth.user_type, permissions=list(auth.perms))


@router.get(
    "/permissions",
    response_model=list[PermissionRead],
    dependencies=[Depends(security), Depends(require_permission("access.read"))],
)
@limiter.limit(settings.RATE_LIMIT_ACCESS)
async def list_permissions(request: Request):
    """List all registered permissions."""
    _ = request
    rows = await access_services.list_permissions()
    return [PermissionRead.model_validate(row) for row in rows]


@router.get(
    "/roles",
    response_model=list[AccessRoleRead],
    dependencies=[Depends(security), Depends(require_permission("access.read"))],
)
@limiter.limit(settings.RATE_LIMIT_ACCESS)
async def list_access_roles(request: Request):
    """List access roles."""
    _ = request
    roles = await access_services.list_access_roles()
    return [await _role_to_read(role) for role in roles]


@router.post(
    "/roles",
    response_model=AccessRoleRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(security), Depends(require_permission("access.manage"))],
)
@limiter.limit(settings.RATE_LIMIT_ACCESS)
async def create_access_role(request: Request, data: AccessRoleCreate):
    """Create a custom access role."""
    _ = request
    role = await access_services.create_access_role(
        slug=data.slug,
        name=data.name,
        description=data.description,
        permission_codenames=data.permission_codenames,
    )
    return await _role_to_read(role)


@router.patch(
    "/roles/{role_id}",
    response_model=AccessRoleRead,
    dependencies=[Depends(security), Depends(require_permission("access.manage"))],
)
@limiter.limit(settings.RATE_LIMIT_ACCESS)
async def update_access_role(request: Request, role_id: str, data: AccessRoleUpdate):
    """Update an access role."""
    _ = request
    role = await access_services.get_access_role_or_404(role_id)
    role = await access_services.update_access_role(
        role,
        name=data.name,
        description=data.description,
        permission_codenames=data.permission_codenames,
    )
    return await _role_to_read(role)


@router.delete(
    "/roles/{role_id}",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(security), Depends(require_permission("access.manage"))],
)
@limiter.limit(settings.RATE_LIMIT_ACCESS)
async def delete_access_role(request: Request, role_id: str):
    """Delete a non-system access role."""
    _ = request
    role = await access_services.get_access_role_or_404(role_id)
    await access_services.delete_access_role(role)
    return {"message": "Access role deleted."}


@router.get(
    "/accounts/{account_id}/roles",
    response_model=AccountAccessSummary,
    dependencies=[Depends(security), Depends(require_permission("accounts.read"))],
)
@limiter.limit(settings.RATE_LIMIT_ACCESS)
async def get_account_access(request: Request, account_id: str):
    """Return role slugs and effective permissions for an account."""
    _ = request
    account = await Account.filter(id=account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found.")
    role_slugs = await access_services.get_account_role_slugs(account)
    permissions = await access_services.resolve_effective_permissions(account)
    return AccountAccessSummary(
        account_id=str(account.id),
        role_slugs=role_slugs,
        permissions=permissions,
    )


@router.put(
    "/accounts/{account_id}/roles",
    response_model=AccountAccessSummary,
    dependencies=[Depends(security), Depends(require_permission("accounts.assign_roles"))],
)
@limiter.limit(settings.RATE_LIMIT_ACCESS)
async def set_account_access_roles(
    request: Request,
    account_id: str,
    data: AccountAccessRolesUpdate,
    current_user: Annotated[Account, Depends(get_current_active_user)],
):
    """Replace access role assignments for an account."""
    _ = request
    account = await Account.filter(id=account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found.")
    await access_services.assign_access_roles_to_account(
        account,
        data.role_slugs,
        assigned_by=current_user,
        replace=True,
    )
    role_slugs = await access_services.get_account_role_slugs(account)
    permissions = await access_services.resolve_effective_permissions(account)
    return AccountAccessSummary(
        account_id=str(account.id),
        role_slugs=role_slugs,
        permissions=permissions,
    )


@router.put(
    "/accounts/{account_id}/permissions",
    response_model=AccountAccessSummary,
    dependencies=[Depends(security), Depends(require_permission("accounts.assign_roles"))],
)
@limiter.limit(settings.RATE_LIMIT_ACCESS)
async def set_account_direct_permissions(
    request: Request,
    account_id: str,
    data: AccountDirectPermissionsUpdate,
    current_user: Annotated[Account, Depends(get_current_active_user)],
):
    """Replace direct permission grants for an account."""
    _ = request
    account = await Account.filter(id=account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found.")
    await access_services.set_direct_permissions(
        account,
        [grant.model_dump() for grant in data.grants],
        assigned_by=current_user,
        replace=True,
    )
    role_slugs = await access_services.get_account_role_slugs(account)
    permissions = await access_services.resolve_effective_permissions(account)
    return AccountAccessSummary(
        account_id=str(account.id),
        role_slugs=role_slugs,
        permissions=permissions,
    )
