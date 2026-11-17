"""Code-first permission registry for RBAC."""

from __future__ import annotations

from dataclasses import dataclass

from app.access.models import Permission


@dataclass(frozen=True, slots=True)
class PermissionDefinition:
    """Declarative permission entry synced to the database."""

    codename: str
    module: str
    action: str
    description: str = ""


_REGISTRY: list[PermissionDefinition] = []
_WILDCARD = PermissionDefinition("*", "*", "*", "Full platform access")


def register_module(
    module: str,
    actions: list[str],
    *,
    descriptions: dict[str, str] | None = None,
) -> list[PermissionDefinition]:
    """Register CRUD-style permissions for a module."""
    descriptions = descriptions or {}
    created: list[PermissionDefinition] = []
    for action in actions:
        codename = f"{module}.{action}"
        entry = PermissionDefinition(
            codename=codename,
            module=module,
            action=action,
            description=descriptions.get(action, f"{action.title()} {module}"),
        )
        _REGISTRY.append(entry)
        created.append(entry)
    wildcard = PermissionDefinition(
        codename=f"{module}.*",
        module=module,
        action="*",
        description=f"All {module} permissions",
    )
    _REGISTRY.append(wildcard)
    created.append(wildcard)
    return created


def all_permission_definitions() -> list[PermissionDefinition]:
    """Return every registered permission including the global wildcard."""
    return [* _REGISTRY, _WILDCARD]


def bootstrap_registry() -> None:
    """Register starter-module permissions (idempotent)."""
    if _REGISTRY:
        return
    register_module(
        "access",
        ["read", "manage", "broadcast"],
        descriptions={
            "read": "View permissions and access roles",
            "manage": "Create and update access roles",
        },
    )
    register_module(
        "accounts",
        ["create", "read", "update", "delete", "assign_roles"],
        descriptions={
            "create": "Create accounts",
            "read": "View accounts",
            "update": "Update accounts",
            "delete": "Delete or deactivate accounts",
            "assign_roles": "Assign access roles and direct permissions",
        },
    )
    register_module(
        "files",
        ["create", "read", "update", "delete"],
    )
    register_module(
        "notifications",
        ["read", "manage"],
        descriptions={
            "read": "List and read own notifications",
            "manage": "Manage notification delivery settings",
            "broadcast": "Broadcast notifications to active accounts",
        },
    )
    register_module("audit_logs", ["read"])
    register_module("client_errors", ["read"])
    register_module(
        "contact",
        ["read", "manage"],
        descriptions={
            "read": "View contact submissions",
            "manage": "Manage contact inbox",
        },
    )
    register_module(
        "app_releases",
        ["manage"],
        descriptions={
            "manage": "Create and update mobile/web app releases",
        },
    )


async def sync_permissions() -> int:
    """Upsert registry permissions into the database."""
    bootstrap_registry()
    synced = 0
    for entry in all_permission_definitions():
        _, created = await Permission.update_or_create(
            defaults={
                "module": entry.module,
                "action": entry.action,
                "description": entry.description or None,
            },
            codename=entry.codename,
        )
        if created:
            synced += 1
    return synced


def permission_matches(required: str, granted: set[str]) -> bool:
    """Return True when granted set satisfies required codename."""
    if "*" in granted:
        return True
    if required in granted:
        return True
    if required.endswith(".*"):
        return False
    module = required.split(".", 1)[0]
    return f"{module}.*" in granted
