"""Public access service API."""

from app.access.services.core import (
    assign_access_roles_to_account,
    assign_default_access_role,
    build_token_auth_payload,
    create_access_role,
    delete_access_role,
    ensure_default_access_role,
    get_access_role_or_404,
    get_account_role_slugs,
    list_access_roles,
    list_permissions,
    resolve_effective_permissions,
    seed_default_access_roles,
    set_direct_permissions,
    sync_permissions,
    update_access_role,
)
from app.access.utils import check_permission

__all__ = [
    "assign_access_roles_to_account",
    "assign_default_access_role",
    "build_token_auth_payload",
    "check_permission",
    "create_access_role",
    "delete_access_role",
    "ensure_default_access_role",
    "get_access_role_or_404",
    "get_account_role_slugs",
    "list_access_roles",
    "list_permissions",
    "resolve_effective_permissions",
    "seed_default_access_roles",
    "set_direct_permissions",
    "sync_permissions",
    "update_access_role",
]
