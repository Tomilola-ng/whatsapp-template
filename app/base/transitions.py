"""Generic state-transition registry and enforcement.

Stateful resources declare allowed ``from -> to`` edges. ``assert_transition``
rejects any transition not explicitly registered.
"""

from __future__ import annotations

from enum import Enum
from typing import Hashable


class InvalidTransitionError(Exception):
    """Raised when a state change is not in the registered edge set."""

    def __init__(
        self,
        *,
        resource: str,
        from_state: Hashable,
        to_state: Hashable,
    ) -> None:
        self.resource = resource
        self.from_state = from_state
        self.to_state = to_state
        super().__init__(
            f"Invalid {resource} transition: {from_state!r} -> {to_state!r}"
        )


# resource_name -> frozenset of (from, to) edges
_REGISTRY: dict[str, frozenset[tuple[Hashable, Hashable]]] = {}


def register_transitions(
    resource: str,
    edges: list[tuple[Hashable, Hashable]] | set[tuple[Hashable, Hashable]],
) -> None:
    """Register or replace allowed transitions for a resource name."""
    _REGISTRY[resource] = frozenset(edges)


def assert_transition(
    resource: str,
    from_state: Hashable,
    to_state: Hashable,
) -> None:
    """Raise InvalidTransitionError when the edge is not registered."""
    from_value = from_state.value if isinstance(from_state, Enum) else from_state
    to_value = to_state.value if isinstance(to_state, Enum) else to_state
    edges = _REGISTRY.get(resource)
    if edges is None:
        raise InvalidTransitionError(
            resource=resource, from_state=from_value, to_state=to_value
        )
    # Allow matching either enum instances or their values.
    candidates = {
        (from_state, to_state),
        (from_value, to_value),
        (from_state, to_value),
        (from_value, to_state),
    }
    if not candidates & edges:
        # Also compare edge members by .value when they are enums.
        normalized = {
            (
                a.value if isinstance(a, Enum) else a,
                b.value if isinstance(b, Enum) else b,
            )
            for a, b in edges
        }
        if (from_value, to_value) not in normalized:
            raise InvalidTransitionError(
                resource=resource, from_state=from_value, to_state=to_value
            )


__all__ = [
    "InvalidTransitionError",
    "assert_transition",
    "register_transitions",
]
