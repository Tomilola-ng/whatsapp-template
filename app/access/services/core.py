"""Access control services: permissions, roles, and assignments."""

from __future__ import annotations

import logging
from typing import Iterable

from fastapi import HTTPException, status
from tortoise.transactions import in_transaction

from app.access.models import (
    AccessRole,
    AccessRolePermission,
    AccountAccessRole,
    AccountPermission,
    Permission,
)
from app.access.permission_registry import (
    bootstrap_registry,
    permission_matches,
    sync_permissions as _sync_permissions,
)
from app.accounts.enums import UserType
from app.accounts.models import Account

logger = logging.getLogger(__name__)

JWT_PERMISSIONS_CAP = 64

DEFAULT_ROLE_PERMISSIONS: dict[str, list[str]] = {
    "super_admin": ["*"],
    "accounts_manager": [
        "accounts.create",
        "accounts.read",
        "accounts.update",
        "accounts.delete",
        "accounts.assign_roles",
        "access.read",
    ],
    "content_admin": ["files.*", "contact.*", "app_releases.manage", "access.read"],
    "customer_basic": ["notifications.read", "notifications.manage"],
    "provider_basic": ["notifications.read", "files.create", "files.read"],
}

DEFAULT_ACCESS_ROLES: dict[str, dict] = {
    "super_admin": {
        "name": "Super Admin",
        "description": "Full platform access",
        "is_system": True,
    },
    "accounts_manager": {
        "name": "Accounts Manager",
        "description": "Manage accounts and role assignments",
        "is_system": True,
    },
    "content_admin": {
        "name": "Content Admin",
        "description": "Manage files, contact inbox, and app releases",
        "is_system": True,
    },
    "customer_basic": {
        "name": "Customer Basic",
        "description": "Default customer capabilities",
        "is_system": True,
    },
    "provider_basic": {
        "name": "Provider Basic",
        "description": "Default provider capabilities",
        "is_system": True,
    },
}

USER_TYPE_DEFAULT_ROLE: dict[UserType, str] = {
    UserType.CUSTOMER: "customer_basic",
    UserType.PROVIDER: "provider_basic",
    UserType.ADMIN: "super_admin",
}


async def sync_permissions() -> int:
    """Upsert registry permissions into the database."""
    return await _sync_permissions()


async def _permission_ids_for_codenames(codenames: Iterable[str]) -> list[Permission]:
    rows = await Permission.filter(codename__in=list(codenames)).all()
    found = {row.codename for row in rows}
    missing = set(codenames) - found
    if missing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown permissions: {', '.join(sorted(missing))}",
        )
    return rows


async def _set_role_permissions(role: AccessRole, codenames: list[str]) -> None:
    permissions = await _permission_ids_for_codenames(codenames)
    await AccessRolePermission.filter(access_role=role).delete()
    for perm in permissions:
        await AccessRolePermission.create(access_role=role, permission=perm)


async def seed_default_access_roles() -> None:
    """Idempotently seed system access roles and their permissions."""
    bootstrap_registry()
    await sync_permissions()
    for slug, meta in DEFAULT_ACCESS_ROLES.items():
        role, created = await AccessRole.update_or_create(
            defaults={
                "name": meta["name"],
                "description": meta["description"],
                "is_system": meta["is_system"],
            },
            slug=slug,
        )
        has_permissions = await AccessRolePermission.filter(access_role=role).exists()
        if created or not has_permissions:
            await _set_role_permissions(role, DEFAULT_ROLE_PERMISSIONS[slug])


def _permissions_cover(assigner_perms: set[str], required: set[str]) -> bool:
    if "*" in assigner_perms:
        return True
    return all(permission_matches(required_perm, assigner_perms) for required_perm in required)


async def _role_permission_codenames(role: AccessRole) -> set[str]:
    links = await AccessRolePermission.filter(access_role=role).prefetch_related(
        "permission"
    )
    return {link.permission.codename for link in links}


async def _assert_can_modify_account_access(
    assigner: Account | None,
    target: Account,
    *,
    role_slugs: list[str] | None = None,
    direct_grants: list[dict] | None = None,
) -> None:
    if assigner is not None and str(assigner.id) == str(target.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot modify your own access roles or permissions.",
        )
    if assigner is None:
        return

    assigner_perms = set(await resolve_effective_permissions(assigner))

    if role_slugs is not None:
        for slug in role_slugs:
            if slug == "super_admin" and "*" not in assigner_perms:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You cannot assign the super_admin role.",
                )
            role = await AccessRole.filter(slug=slug).first()
            if not role:
                continue
            required = await _role_permission_codenames(role)
            if not _permissions_cover(assigner_perms, required):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"You cannot assign access role {slug!r}.",
                )

    if direct_grants is not None:
        for grant in direct_grants:
            if not grant.get("granted", True):
                continue
            codename = grant["codename"]
            if not permission_matches(codename, assigner_perms):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"You cannot grant permission {codename!r}.",
                )


async def assign_default_access_role(account: Account) -> None:
    """Ensure the account has its user-type default access role."""
    slug = USER_TYPE_DEFAULT_ROLE.get(account.user_type, "customer_basic")
    role = await AccessRole.filter(slug=slug).first()
    if not role:
        await seed_default_access_roles()
        role = await AccessRole.filter(slug=slug).first()
    if not role:
        logger.warning("Default access role %s missing; skipping assignment", slug)
        return
    await AccountAccessRole.get_or_create(account=account, access_role=role)


async def reconcile_user_type_default_roles(account: Account) -> None:
    """Ensure the current user-type default role and drop stale type-default roles."""
    expected_slug = USER_TYPE_DEFAULT_ROLE.get(account.user_type, "customer_basic")
    all_default_slugs = set(USER_TYPE_DEFAULT_ROLE.values())

    links = await AccountAccessRole.filter(account=account).prefetch_related("access_role")
    assigned_slugs = {link.access_role.slug for link in links}

    if expected_slug not in assigned_slugs:
        await assign_default_access_role(account)
        links = await AccountAccessRole.filter(account=account).prefetch_related("access_role")
        assigned_slugs = {link.access_role.slug for link in links}

    stale_slugs = (assigned_slugs & all_default_slugs) - {expected_slug}
    if not stale_slugs:
        return

    stale_roles = await AccessRole.filter(slug__in=list(stale_slugs)).all()
    if not stale_roles:
        return

    stale_ids = [role.id for role in stale_roles]
    await AccountAccessRole.filter(account=account, access_role_id__in=stale_ids).delete()
    await invalidate_account_sessions(account)


async def ensure_default_access_role(account: Account) -> None:
    """Ensure user-type default role assignments are current."""
    await reconcile_user_type_default_roles(account)


async def resolve_effective_permissions(account: Account) -> list[str]:
    """Compute sorted effective permission codenames for an account."""
    role_links = await AccountAccessRole.filter(account=account).prefetch_related(
        "access_role__role_permissions__permission"
    )
    direct_links = await AccountPermission.filter(account=account).prefetch_related(
        "permission"
    )

    granted: set[str] = set()
    for link in role_links:
        role = link.access_role
        for rp in role.role_permissions:
            granted.add(rp.permission.codename)

    denied: set[str] = set()
    for link in direct_links:
        codename = link.permission.codename
        if link.granted:
            granted.add(codename)
        else:
            denied.add(codename)

    effective = sorted(granted - denied)
    if len(effective) > JWT_PERMISSIONS_CAP:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                f"Account has {len(effective)} permissions; consolidate roles "
                f"(cap {JWT_PERMISSIONS_CAP})."
            ),
        )
    return effective


async def build_token_auth_payload(account: Account) -> dict:
    """JWT claims fragment for access tokens."""
    perms = await resolve_effective_permissions(account)
    user_type = account.user_type
    ut = user_type.value if hasattr(user_type, "value") else str(user_type)
    return {
        "sub": str(account.id),
        "v": int(account.auth_token_version),
        "pv": int(account.permissions_version),
        "ut": ut,
        "perms": perms,
    }


async def invalidate_account_sessions(account: Account) -> None:
    """Revoke tokens after access changes."""
    account.auth_token_version = int(account.auth_token_version or 0) + 1
    account.permissions_version = int(account.permissions_version or 0) + 1
    await account.save()


async def assign_access_roles_to_account(
    account: Account,
    role_slugs: list[str],
    *,
    assigned_by: Account | None = None,
    replace: bool = True,
) -> list[str]:
    """Assign access roles by slug; optionally replace existing assignments."""
    if replace and not role_slugs:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one access role is required.",
        )

    roles = await AccessRole.filter(slug__in=role_slugs).all()
    found = {role.slug for role in roles}
    missing = set(role_slugs) - found
    if missing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Access roles not found: {', '.join(sorted(missing))}",
        )

    await _assert_can_modify_account_access(
        assigned_by,
        account,
        role_slugs=role_slugs,
    )

    async with in_transaction():
        if replace:
            await AccountAccessRole.filter(account=account).delete()
        for role in roles:
            await AccountAccessRole.get_or_create(
                account=account,
                access_role=role,
                defaults={"assigned_by": assigned_by},
            )
        await invalidate_account_sessions(account)
    return role_slugs


async def set_direct_permissions(
    account: Account,
    grants: list[dict],
    *,
    assigned_by: Account | None = None,
    replace: bool = True,
) -> list[str]:
    """Set direct permission grants/denies: [{codename, granted}]."""
    await _assert_can_modify_account_access(
        assigned_by,
        account,
        direct_grants=grants,
    )

    async with in_transaction():
        if replace:
            await AccountPermission.filter(account=account).delete()
        codenames: list[str] = []
        for item in grants:
            codename = item["codename"]
            perm = await Permission.filter(codename=codename).first()
            if not perm:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Permission not found: {codename}",
                )
            await AccountPermission.create(
                account=account,
                permission=perm,
                granted=bool(item.get("granted", True)),
                assigned_by=assigned_by,
            )
            codenames.append(codename)
        await invalidate_account_sessions(account)
    return codenames


async def list_permissions() -> list[Permission]:
    return await Permission.all().order_by("module", "codename")


async def list_access_roles() -> list[AccessRole]:
    return await AccessRole.all().order_by("slug")


async def get_access_role_or_404(role_id: str) -> AccessRole:
    role = await AccessRole.filter(id=role_id).first()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Access role not found.")
    return role


async def create_access_role(
    *,
    slug: str,
    name: str,
    description: str | None,
    permission_codenames: list[str],
) -> AccessRole:
    if await AccessRole.filter(slug=slug).exists():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Slug already exists.")
    async with in_transaction():
        role = await AccessRole.create(
            slug=slug,
            name=name,
            description=description,
            is_system=False,
        )
        await _set_role_permissions(role, permission_codenames)
    return role


async def update_access_role(
    role: AccessRole,
    *,
    name: str | None = None,
    description: str | None = None,
    permission_codenames: list[str] | None = None,
) -> AccessRole:
    if role.is_system:
        if permission_codenames is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="System access role permissions cannot be modified.",
            )
        if name is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="System access roles cannot be renamed.",
            )

    async with in_transaction():
        if name is not None:
            role.name = name
        if description is not None:
            role.description = description
        if permission_codenames is not None:
            await _set_role_permissions(role, permission_codenames)
        await role.save()
    return role


async def delete_access_role(role: AccessRole) -> None:
    if role.is_system:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="System access roles cannot be deleted.",
        )
    await role.delete()


async def get_account_role_slugs(account: Account) -> list[str]:
    links = await AccountAccessRole.filter(account=account).prefetch_related("access_role")
    return [link.access_role.slug for link in links]

