"""Pure access-control helpers (no database or service imports)."""

from collections.abc import Iterable

from app.access.permission_registry import permission_matches


def check_permission(required: str, granted: Iterable[str]) -> bool:
    """Return True when `required` is satisfied by the granted codename set."""
    return permission_matches(required, set(granted))
