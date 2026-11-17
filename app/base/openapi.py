"""OpenAPI audiences: app (product JWT) and admin (platform RBAC).

Routes are classified from FastAPI dependencies and path rules (or an explicit
``openapi_extra`` override via :func:`openapi_audience`). Schema builders then
emit filtered OpenAPI documents with audience-specific titles and security.
"""

from __future__ import annotations

import copy
from typing import Any, Literal

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.routing import APIRoute

from app.config.settings import settings

Audience = Literal["app", "admin"]

_AUDIENCE_KEY = "x-openapi-audience"
_VALID_AUDIENCES = frozenset({"app", "admin"})

_APP_ONLY: tuple[Audience, ...] = ("app",)
_ADMIN_ONLY: tuple[Audience, ...] = ("admin",)
_BOTH: tuple[Audience, ...] = ("app", "admin")
_HIDDEN: tuple[Audience, ...] = ()

_AUTH_HEADERS_STRIP = frozenset({"authorization"})

_BEARER_SCHEME = {
    "type": "http",
    "scheme": "bearer",
    "bearerFormat": "JWT",
    "description": (
        "Access JWT from POST /auth/login (or refresh / verify-otp / verify-login-otp)."
    ),
}

_APP_INFO = {
    "title": f"{settings.PROJECT_NAME} — App API",
    "description": (
        "Product / mobile / client app surface. Authenticate with a Bearer JWT. "
        "Platform admin and access-management routes live under `/docs/admin`."
    ),
}
_ADMIN_INFO = {
    "title": f"{settings.PROJECT_NAME} — Admin API",
    "description": (
        "Platform admin console surface. Authenticate with a Bearer JWT for an "
        "account that holds the matching RBAC permission (`require_permission`)."
    ),
}

_AUDIENCE_INFO = {
    "app": _APP_INFO,
    "admin": _ADMIN_INFO,
}

OPENAPI_TAG_ORDER: list[dict[str, str]] = [
    {"name": "Accounts", "description": "Registration, login, profile, and password flows."},
    {"name": "Access Control", "description": "Permissions and access roles."},
    {"name": "Base", "description": "Shared file helpers."},
    {"name": "Notifications", "description": "In-app notifications and SSE."},
    {"name": "Contact", "description": "Public contact form."},
    {"name": "App Updates", "description": "Mobile release policy and legal URLs."},
    {"name": "Administration", "description": "Platform admin audit tools."},
    {"name": "Client Errors", "description": "Client error reporting."},
    {"name": "Internal Jobs", "description": "Internal job runners."},
    {"name": "Dev Outbox", "description": "Local development outbox helpers."},
]


def openapi_audience(*audiences: Audience) -> dict[str, Any]:
    """Return ``openapi_extra`` marking which docs surfaces include this route."""
    return {_AUDIENCE_KEY: list(audiences)}


def _walk_dependant_calls(dependant) -> list[Any]:
    calls: list[Any] = []
    for dep in dependant.dependencies:
        if dep.call is not None:
            calls.append(dep.call)
        calls.extend(_walk_dependant_calls(dep))
    return calls


def _call_module(call: Any) -> str:
    return getattr(call, "__module__", "") or ""


def _call_name(call: Any) -> str:
    return getattr(call, "__name__", "") or type(call).__name__


def _normalize_audiences(raw: Any) -> tuple[Audience, ...]:
    if not raw:
        return _HIDDEN
    return tuple(a for a in raw if a in _VALID_AUDIENCES)  # type: ignore[misc]


def _is_admin_path(path: str) -> bool:
    return "/admin/" in path or path.rstrip("/").endswith("/admin")


def classify_route(route: APIRoute) -> tuple[Audience, ...]:
    """Infer OpenAPI audiences for a route from auth dependencies / path."""
    extra = route.openapi_extra or {}
    if _AUDIENCE_KEY in extra:
        return _normalize_audiences(extra[_AUDIENCE_KEY])

    path = route.path
    if "/internal/jobs" in path:
        return _HIDDEN
    if "/dev/" in path:
        return _HIDDEN

    calls = _walk_dependant_calls(route.dependant)
    modules = {_call_module(c) for c in calls}
    names = {_call_name(c) for c in calls}

    has_jwt_user = any(
        n
        in {
            "get_current_user",
            "get_current_active_user",
            "get_user_from_password_reset_token",
        }
        for n in names
    )
    has_platform_rbac = any(
        "access.permissions" in m or m.endswith("access.permissions") for m in modules
    ) or any(n in {"get_validated_token_auth", "require_permission"} for n in names)
    has_internal_token = any(n == "verify_internal_job_token" for n in names)

    if has_internal_token and not has_jwt_user and not has_platform_rbac:
        return _HIDDEN

    if _is_admin_path(path):
        return _ADMIN_ONLY

    if has_platform_rbac and "/access" in path:
        # /access/me/permissions is for every authenticated app user.
        if path.rstrip("/").endswith("/me/permissions"):
            return _BOTH
        return _ADMIN_ONLY

    if has_platform_rbac and not has_jwt_user:
        return _ADMIN_ONLY

    if path.rstrip("/").endswith("/health"):
        return _BOTH
    if "/auth" in path:
        return _BOTH
    if "/contact" in path:
        return _APP_ONLY

    if has_jwt_user or has_platform_rbac:
        return _APP_ONLY

    return _APP_ONLY


def stamp_route_audiences(app: FastAPI) -> None:
    """Write inferred ``x-openapi-audience`` onto every APIRoute."""
    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        extra = dict(route.openapi_extra or {})
        extra.pop(_AUDIENCE_KEY, None)
        route.openapi_extra = extra or None
        audiences = classify_route(route)
        route.openapi_extra = {
            **(route.openapi_extra or {}),
            _AUDIENCE_KEY: list(audiences),
        }


def _operation_audiences(operation: dict[str, Any]) -> tuple[Audience, ...]:
    return _normalize_audiences(operation.get(_AUDIENCE_KEY))


def _strip_header_params(
    operation: dict[str, Any], header_names: frozenset[str]
) -> None:
    params = operation.get("parameters")
    if not params:
        return
    kept = []
    for param in params:
        if (
            param.get("in") == "header"
            and str(param.get("name", "")).lower() in header_names
        ):
            continue
        kept.append(param)
    if kept:
        operation["parameters"] = kept
    else:
        operation.pop("parameters", None)


def _operation_requires_auth(operation: dict[str, Any]) -> bool:
    if operation.get("security"):
        return True
    for param in operation.get("parameters") or []:
        if param.get("in") != "header":
            continue
        if str(param.get("name", "")).lower() in _AUTH_HEADERS_STRIP:
            return True
    return False


def _rewrite_operation_for_audience(operation: dict[str, Any]) -> dict[str, Any]:
    op = copy.deepcopy(operation)
    op.pop(_AUDIENCE_KEY, None)
    requires_auth = _operation_requires_auth(operation)
    _strip_header_params(op, _AUTH_HEADERS_STRIP)
    op["security"] = [{"BearerAuth": []}] if requires_auth else []
    return op


def _collect_refs(obj: Any, refs: set[str]) -> None:
    if isinstance(obj, dict):
        ref = obj.get("$ref")
        if isinstance(ref, str) and ref.startswith("#/components/"):
            refs.add(ref)
        for value in obj.values():
            _collect_refs(value, refs)
    elif isinstance(obj, list):
        for item in obj:
            _collect_refs(item, refs)


def _prune_unused_components(schema: dict[str, Any]) -> None:
    components = schema.get("components") or {}
    if not components:
        return
    changed = True
    while changed:
        changed = False
        refs: set[str] = set()
        _collect_refs(schema.get("paths"), refs)
        _collect_refs(schema.get("components"), refs)
        for section, items in list(components.items()):
            if section == "securitySchemes":
                continue
            if not isinstance(items, dict):
                continue
            for name in list(items.keys()):
                needle = f"#/components/{section}/{name}"
                if needle not in refs:
                    del items[name]
                    changed = True
            if not items:
                del components[section]
                changed = True


def _prune_unused_tags(schema: dict[str, Any]) -> None:
    used: set[str] = set()
    for path_item in (schema.get("paths") or {}).values():
        for operation in path_item.values():
            if not isinstance(operation, dict):
                continue
            for tag in operation.get("tags") or []:
                used.add(tag)
    ordered = [t for t in OPENAPI_TAG_ORDER if t["name"] in used]
    known = {t["name"] for t in OPENAPI_TAG_ORDER}
    extras = [{"name": name, "description": ""} for name in sorted(used - known)]
    schema["tags"] = ordered + extras


def _openapi_tags_for_build() -> list[dict[str, str]]:
    return [dict(item) for item in OPENAPI_TAG_ORDER]


def build_openapi_for_audience(
    app: FastAPI,
    audience: Audience,
    *,
    base_schema: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a filtered OpenAPI schema for ``app`` or ``admin``."""
    stamp_route_audiences(app)
    if base_schema is None:
        base_schema = get_openapi(
            title=app.title,
            version=app.version,
            routes=app.routes,
            description=app.description,
            tags=_openapi_tags_for_build(),
        )

    info_extra = _AUDIENCE_INFO[audience]
    schema: dict[str, Any] = {
        "openapi": base_schema.get("openapi", "3.1.0"),
        "info": {
            **copy.deepcopy(base_schema.get("info") or {}),
            "title": info_extra["title"],
            "description": info_extra["description"],
            "version": (base_schema.get("info") or {}).get("version") or app.version,
        },
        "paths": {},
        "components": {
            "schemas": copy.deepcopy(
                (base_schema.get("components") or {}).get("schemas") or {}
            ),
            "securitySchemes": {"BearerAuth": copy.deepcopy(_BEARER_SCHEME)},
        },
    }

    if "servers" in base_schema:
        schema["servers"] = copy.deepcopy(base_schema["servers"])
    schema["tags"] = _openapi_tags_for_build()

    for path, path_item in (base_schema.get("paths") or {}).items():
        filtered_item: dict[str, Any] = {}
        for method, operation in path_item.items():
            if method.startswith("x-") or not isinstance(operation, dict):
                continue
            if method == "parameters":
                continue
            audiences = _operation_audiences(operation)
            if audience not in audiences:
                continue
            filtered_item[method] = _rewrite_operation_for_audience(operation)
        if filtered_item:
            schema["paths"][path] = filtered_item

    _prune_unused_components(schema)
    _prune_unused_tags(schema)
    return schema


def attach_dual_openapi(app: FastAPI) -> None:
    """Cache app/admin OpenAPI builders on the app."""
    stamp_route_audiences(app)
    app.state.openapi_app = None
    app.state.openapi_admin = None

    def _base() -> dict[str, Any]:
        stamp_route_audiences(app)
        return get_openapi(
            title=app.title,
            version=app.version,
            routes=app.routes,
            description=app.description,
            tags=_openapi_tags_for_build(),
        )

    def app_openapi() -> dict[str, Any]:
        if app.state.openapi_app is None:
            app.state.openapi_app = build_openapi_for_audience(
                app, "app", base_schema=_base()
            )
        return app.state.openapi_app

    def admin_openapi() -> dict[str, Any]:
        if app.state.openapi_admin is None:
            app.state.openapi_admin = build_openapi_for_audience(
                app, "admin", base_schema=_base()
            )
        return app.state.openapi_admin

    app.openapi_app = app_openapi  # type: ignore[attr-defined]
    app.openapi_admin = admin_openapi  # type: ignore[attr-defined]
    app.openapi = app_openapi  # type: ignore[method-assign]


__all__ = [
    "OPENAPI_TAG_ORDER",
    "attach_dual_openapi",
    "build_openapi_for_audience",
    "classify_route",
    "openapi_audience",
    "stamp_route_audiences",
]
