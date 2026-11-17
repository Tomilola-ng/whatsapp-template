"""Django-style class-based CRUD views for Tortoise models.

Declare a model, its schemas, and the permission module; ``as_router()`` returns a
ready-to-mount ``APIRouter`` with typed request/response models for Swagger::

    class AppReleaseAdminView(ModelView):
        model = AppRelease
        prefix = "/admin/app/releases"
        tags = ["Administration"]
        audience = ("admin",)
        permissions = {"*": "app_releases.manage"}
        create_schema = ReleaseCreate
        update_schema = ReleasePatch
        out_schema = ReleaseOut
        filter_fields = ("platform", "is_active")

    router = AppReleaseAdminView.as_router()

Anything beyond plain CRUD belongs in a ``services/`` module: override a hook
(``validate``, ``perform_create``, ``get_queryset`` ...) to call it, or add a custom
endpoint with ``@action``. See ``docs/CBV_GUIDE.md``.

NOTE: do not add ``from __future__ import annotations`` to this module — FastAPI
signatures are assembled dynamically from real type objects.
"""

import inspect
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, ClassVar, Literal

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import Response
from tortoise.contrib.pydantic import pydantic_model_creator
from tortoise.exceptions import IntegrityError
from tortoise.expressions import Q
from tortoise.models import Model
from pydantic import BaseModel, ConfigDict, create_model

from app.access.permissions import TokenAuth, get_validated_token_auth, require_permission
from app.base.client_ip import client_ip
from app.base.http_errors import api_error
from app.base.openapi import openapi_audience
from app.base.rate_limit import limiter
from app.base.responses import EnvelopeResponse, success_response
from app.config.pagination import (
    PaginatedResponse,
    PaginationHelper,
    PaginationParams,
    get_pagination_params,
)

Action = Literal["list", "retrieve", "create", "update", "partial_update", "destroy"]

CRUD_ACTIONS: tuple[str, ...] = ("list", "retrieve", "create", "partial_update", "destroy")
READ_ONLY_ACTIONS: tuple[str, ...] = ("list", "retrieve")

_PERMISSION_VERB = {
    "list": "read",
    "retrieve": "read",
    "create": "create",
    "update": "update",
    "partial_update": "update",
    "destroy": "delete",
}
_SCHEMA_CACHE: dict[type, dict[str, type[BaseModel]]] = {}
_LOOKUP_SUFFIX_TYPES: dict[str, type] = {
    "icontains": str,
    "contains": str,
    "startswith": str,
    "istartswith": str,
    "isnull": bool,
    "in": str,
}


# ─────────────────────────────────────────────────────────────
# Context + custom-action decorator
# ─────────────────────────────────────────────────────────────


@dataclass(slots=True)
class ViewContext:
    """Per-request context handed to every hook and ``@action`` method."""

    request: Request
    auth: TokenAuth | None
    action: str

    @property
    def account_id(self) -> str | None:
        """Authenticated account id (JWT ``sub``) or ``None`` for public actions."""
        return self.auth.sub if self.auth else None


@dataclass(frozen=True, slots=True)
class _ActionMeta:
    methods: tuple[str, ...]
    detail: bool
    path: str | None
    permission: str | None
    public: bool
    status_code: int
    response_model: Any
    summary: str | None
    rate_limit: str | None
    envelope: bool


def action(
    *,
    methods: tuple[str, ...] = ("POST",),
    detail: bool = True,
    path: str | None = None,
    permission: str | None = None,
    public: bool = False,
    status_code: int = 200,
    response_model: Any = None,
    summary: str | None = None,
    rate_limit: str | None = None,
    envelope: bool = True,
):
    """Mark a view method as an extra endpoint (``/{prefix}/{id}/{name}`` when ``detail``).

    The method may declare ``ctx: ViewContext`` plus ordinary FastAPI parameters (body
    models, query params, ``id: str`` for detail actions). Return a dict / pydantic
    object (wrapped in the standard envelope) or a ``Response`` (returned untouched).
    ``permission`` defaults to ``<permission_module>.update``.
    """

    def decorator(fn: Callable) -> Callable:
        fn._action_meta = _ActionMeta(  # type: ignore[attr-defined]
            methods=tuple(m.upper() for m in methods),
            detail=detail,
            path=path,
            permission=permission,
            public=public,
            status_code=status_code,
            response_model=response_model,
            summary=summary,
            rate_limit=rate_limit,
            envelope=envelope,
        )
        return fn

    return decorator


# ─────────────────────────────────────────────────────────────
# Schema helpers
# ─────────────────────────────────────────────────────────────


def partial_schema(schema: type[BaseModel], name: str | None = None) -> type[BaseModel]:
    """Return ``schema`` with every field optional (for PATCH bodies)."""
    fields: dict[str, Any] = {}
    for field_name, info in schema.model_fields.items():
        fields[field_name] = (info.annotation | None, None)
    return create_model(
        name or f"{schema.__name__}Patch",
        __config__=ConfigDict(from_attributes=True),
        **fields,
    )


def _python_type(model: type[Model], field_name: str) -> type:
    field = model._meta.fields_map.get(field_name)
    py_type = getattr(field, "field_type", None)
    if isinstance(py_type, type) and (
        py_type in (str, int, float, bool, datetime) or issubclass(py_type, Enum)
    ):
        return py_type
    return str


# ─────────────────────────────────────────────────────────────
# ModelView
# ─────────────────────────────────────────────────────────────


class ModelView:
    """Declarative CRUD view over one Tortoise model.

    Class attributes (all optional except ``model`` / ``prefix``):

    - ``actions``: which of list/retrieve/create/update/partial_update/destroy to expose.
    - ``permission_module``: ``"firms"`` → ``firms.read|create|update|delete``.
    - ``permissions``: explicit overrides by action, ``"*"`` as the fallback.
    - ``public_actions`` / ``authenticated_actions``: no auth / login-only (no RBAC).
    - ``create_schema`` / ``update_schema`` / ``out_schema`` / ``list_schema``: pydantic
      models; generated from the model when omitted (flat models only).
    - ``search_fields`` (``?q=``), ``filter_fields`` (``?field=``), ``ordering_fields``
      (``?ordering=-field``), ``ordering`` (default order).
    - ``soft_delete_field``: bool/datetime field flipped instead of deleting the row.
    - ``audit``: write an audit-log row for create/update/delete.
    """

    model: ClassVar[type[Model]]
    prefix: ClassVar[str]
    tags: ClassVar[list[str]] = []
    audience: ClassVar[tuple[str, ...]] = ("app",)
    actions: ClassVar[tuple[str, ...]] = CRUD_ACTIONS

    label: ClassVar[str | None] = None  # "App release" (defaults from model name)
    slug: ClassVar[str | None] = None  # "app_release" (error-code prefix)

    permission_module: ClassVar[str | None] = None
    permissions: ClassVar[dict[str, str]] = {}
    public_actions: ClassVar[tuple[str, ...]] = ()
    authenticated_actions: ClassVar[tuple[str, ...]] = ()

    create_schema: ClassVar[type[BaseModel] | None] = None
    update_schema: ClassVar[type[BaseModel] | None] = None
    out_schema: ClassVar[type[BaseModel] | None] = None
    list_schema: ClassVar[type[BaseModel] | None] = None

    lookup_field: ClassVar[str] = "id"
    search_fields: ClassVar[tuple[str, ...]] = ()
    filter_fields: ClassVar[tuple[str, ...]] = ()
    ordering_fields: ClassVar[tuple[str, ...]] = ()
    ordering: ClassVar[tuple[str, ...]] = ("-id",)
    select_related: ClassVar[tuple[str, ...]] = ()

    soft_delete_field: ClassVar[str | None] = None
    audit: ClassVar[bool] = False
    conflict_code: ClassVar[str | None] = None
    conflict_message: ClassVar[str] = "A record with these values already exists."
    rate_limit: ClassVar[str | None] = None

    # ── identity helpers ─────────────────────────────────────

    @classmethod
    def _label(cls) -> str:
        if cls.label:
            return cls.label
        name = cls.model.__name__
        words = "".join(f" {c.lower()}" if c.isupper() else c for c in name).strip()
        return words.capitalize()

    @classmethod
    def _slug(cls) -> str:
        return cls.slug or cls._label().lower().replace(" ", "_")

    @classmethod
    def _schemas(cls) -> dict[str, type[BaseModel]]:
        """Resolve schemas, generating missing ones from the model (cached per view)."""
        if cls not in _SCHEMA_CACHE:
            _SCHEMA_CACHE[cls] = cls._build_schemas()
        return _SCHEMA_CACHE[cls]

    @classmethod
    def _build_schemas(cls) -> dict[str, type[BaseModel]]:
        name = cls.model.__name__
        out = cls.out_schema or pydantic_model_creator(cls.model, name=f"{name}Out")
        create = cls.create_schema or pydantic_model_creator(
            cls.model, name=f"{name}Create", exclude_readonly=True
        )
        update = cls.update_schema or partial_schema(create, f"{name}Update")
        return {
            "out": out,
            "list": cls.list_schema or out,
            "create": create,
            "update": update,
        }

    # ── permissions / auth ──────────────────────────────────

    @classmethod
    def permission_for(cls, action_name: str) -> str | None:
        """Permission codename for ``action_name`` or ``None`` when not RBAC-guarded."""
        if action_name in cls.public_actions or action_name in cls.authenticated_actions:
            return None
        if action_name in cls.permissions:
            return cls.permissions[action_name]
        if "*" in cls.permissions:
            return cls.permissions["*"]
        if cls.permission_module:
            verb = _PERMISSION_VERB.get(action_name, "update")
            return f"{cls.permission_module}.{verb}"
        raise RuntimeError(
            f"{cls.__name__}: set permission_module/permissions, or mark "
            f"'{action_name}' in public_actions / authenticated_actions."
        )

    @classmethod
    def _auth_dependency(
        cls, action_name: str, *, public: bool = False, permission: str | None = None
    ):
        if public or action_name in cls.public_actions:

            async def _public() -> None:
                return None

            return _public
        codename = permission or cls.permission_for(action_name)
        if codename is None:
            return get_validated_token_auth
        return require_permission(codename)

    @classmethod
    def _ctx_dependency(cls, action_name: str, auth_dep: Callable):
        async def _ctx(request: Request, auth=Depends(auth_dep)) -> ViewContext:
            return ViewContext(request=request, auth=auth, action=action_name)

        return _ctx

    # ── hooks (override these) ──────────────────────────────

    async def get_queryset(self, ctx: ViewContext):
        """Base queryset. Override to scope rows (e.g. to the caller's firm)."""
        queryset = self.model.all()
        if self.select_related:
            queryset = queryset.select_related(*self.select_related)
        return queryset

    async def filter_queryset(self, queryset, ctx: ViewContext, filters: dict[str, Any]):
        """Apply ``?q=``, field filters and ordering. Override for custom filtering."""
        search = filters.pop("q", None)
        ordering = filters.pop("ordering", None)
        if search and self.search_fields:
            query = Q()
            for field_name in self.search_fields:
                query |= Q(**{f"{field_name}__icontains": search})
            queryset = queryset.filter(query)
        for key, value in filters.items():
            if value is None:
                continue
            if key.endswith("__in"):
                value = [item.strip() for item in str(value).split(",") if item.strip()]
            queryset = queryset.filter(**{key: value})
        return queryset.order_by(*self._resolve_ordering(ordering))

    def _resolve_ordering(self, raw: str | None) -> tuple[str, ...]:
        if not raw:
            return self.ordering
        requested = [part.strip() for part in raw.split(",") if part.strip()]
        allowed = set(self.ordering_fields)
        bad = [part for part in requested if part.lstrip("-") not in allowed]
        if bad:
            raise api_error(
                422,
                "invalid_ordering",
                f"Cannot order by: {', '.join(bad)}.",
                {"allowed": sorted(allowed)},
            )
        return tuple(requested) or self.ordering

    async def get_object(self, ctx: ViewContext, lookup: str):
        """Fetch one row from ``get_queryset`` or raise 404."""
        queryset = await self.get_queryset(ctx)
        obj = await queryset.filter(**{self.lookup_field: lookup}).first()
        if obj is None:
            raise api_error(404, f"{self._slug()}_not_found", f"{self._label()} was not found.")
        return obj

    async def validate(
        self, values: dict[str, Any], ctx: ViewContext, instance: Model | None = None
    ) -> dict[str, Any]:
        """Business validation / value shaping before create or update.

        ``values`` holds the submitted fields (only the sent ones on PATCH);
        ``instance`` is the existing row on updates. Return the values to persist.
        """
        return values

    async def perform_create(self, values: dict[str, Any], ctx: ViewContext) -> Model:
        return await self.model.create(**values)

    async def perform_update(self, obj: Model, values: dict[str, Any], ctx: ViewContext) -> Model:
        for key, value in values.items():
            setattr(obj, key, value)
        await obj.save()
        return obj

    async def perform_destroy(self, obj: Model, ctx: ViewContext) -> None:
        field_name = self.soft_delete_field
        if not field_name:
            await obj.delete()
            return
        current = getattr(obj, field_name)
        if isinstance(current, bool) or self.model._meta.fields_map[field_name].field_type is bool:
            setattr(obj, field_name, False)
        else:
            setattr(obj, field_name, datetime.now(timezone.utc))
        await obj.save()

    async def serialize(self, obj: Model, ctx: ViewContext, *, many: bool = False):
        """Model → output schema. Override to add computed fields."""
        schema = self._schemas()["list" if many else "out"]
        return schema.model_validate(obj, from_attributes=True)

    # ── internals ───────────────────────────────────────────

    async def _audit(self, ctx: ViewContext, verb: str, obj: Model, fields: list[str] | None):
        if not self.audit:
            return
        from app.audit.enums import AuditActorType
        from app.audit.services import record_audit_event

        await record_audit_event(
            action=f"{self._slug()}.{verb}",
            entity_type=self.model._meta.db_table,
            entity_id=str(obj.pk),
            actor_type=AuditActorType.ACCOUNT if ctx.account_id else AuditActorType.PUBLIC,
            actor_account_id=ctx.account_id,
            metadata={"fields": fields} if fields else None,
            ip_address=client_ip(ctx.request),
            user_agent=ctx.request.headers.get("user-agent"),
        )

    async def _save(self, ctx: ViewContext, call):
        try:
            return await call
        except IntegrityError as exc:
            raise api_error(
                409,
                self.conflict_code or f"{self._slug()}_conflict",
                self.conflict_message,
            ) from exc

    @classmethod
    def _filter_dependency(cls) -> Callable:
        """Build a dependency whose signature exposes q/ordering/filter query params."""
        params = [inspect.Parameter("request", inspect.Parameter.KEYWORD_ONLY, annotation=Request)]
        if cls.search_fields:
            params.append(
                inspect.Parameter(
                    "q",
                    inspect.Parameter.KEYWORD_ONLY,
                    annotation=str | None,
                    default=Query(None, description=f"Search: {', '.join(cls.search_fields)}"),
                )
            )
        if cls.ordering_fields:
            params.append(
                inspect.Parameter(
                    "ordering",
                    inspect.Parameter.KEYWORD_ONLY,
                    annotation=str | None,
                    default=Query(
                        None,
                        description=(
                            f"Comma-separated; prefix '-' for descending. One of: "
                            f"{', '.join(cls.ordering_fields)}"
                        ),
                    ),
                )
            )
        for key in cls.filter_fields:
            base, _, lookup = key.partition("__")
            py_type = _LOOKUP_SUFFIX_TYPES.get(lookup) or _python_type(cls.model, base)
            params.append(
                inspect.Parameter(
                    key,
                    inspect.Parameter.KEYWORD_ONLY,
                    annotation=py_type | None,
                    default=Query(None, description=f"Filter on `{key}`"),
                )
            )

        async def _filters(**kwargs) -> dict[str, Any]:
            kwargs.pop("request", None)
            return {k: v for k, v in kwargs.items() if v is not None}

        _filters.__signature__ = inspect.Signature(params)  # type: ignore[attr-defined]
        return _filters

    # ── router assembly ─────────────────────────────────────

    @classmethod
    def as_router(cls) -> APIRouter:
        """Build the ``APIRouter`` for this view (custom actions first, then CRUD)."""
        view = cls()
        router = APIRouter(prefix=cls.prefix, tags=cls.tags)
        extra = openapi_audience(*cls.audience)  # type: ignore[arg-type]
        schemas = cls._schemas()
        label = cls._label()

        def register(path, endpoint, methods, *, response_model, status_code, summary, rate_limit):
            if rate_limit:
                endpoint = limiter.limit(rate_limit)(endpoint)
            router.add_api_route(
                path,
                endpoint,
                methods=methods,
                response_model=response_model,
                status_code=status_code,
                summary=summary,
                openapi_extra=extra,
            )

        for name in dir(cls):
            meta = getattr(getattr(cls, name, None), "_action_meta", None)
            if meta is not None:
                cls._register_custom_action(view, name, meta, register)

        create_body = schemas["create"]
        wanted = set(cls.actions)
        rl = cls.rate_limit

        if "list" in wanted:
            ctx_dep = cls._ctx_dependency("list", cls._auth_dependency("list"))
            filter_dep = cls._filter_dependency()

            async def list_endpoint(
                request: Request,
                ctx: ViewContext = Depends(ctx_dep),
                pagination: PaginationParams = Depends(get_pagination_params),
                filters: dict = Depends(filter_dep),
            ):
                queryset = await view.get_queryset(ctx)
                queryset = await view.filter_queryset(queryset, ctx, dict(filters))
                rows, meta = await PaginationHelper.paginate_queryset(queryset, pagination)
                items = [await view.serialize(row, ctx, many=True) for row in rows]
                return success_response(
                    PaginatedResponse(items=items, meta=meta), f"{label} list retrieved"
                )

            register(
                "",
                list_endpoint,
                ["GET"],
                response_model=EnvelopeResponse[PaginatedResponse[schemas["list"]]],
                status_code=200,
                summary=f"List {label.lower()}s",
                rate_limit=rl,
            )

        if "create" in wanted:
            ctx_dep = cls._ctx_dependency("create", cls._auth_dependency("create"))

            async def create_endpoint(
                request: Request,
                data: create_body,  # type: ignore[valid-type]
                ctx: ViewContext = Depends(ctx_dep),
            ):
                values = await view.validate(data.model_dump(), ctx)
                obj = await view._save(ctx, view.perform_create(values, ctx))
                await view._audit(ctx, "create", obj, None)
                return success_response(await view.serialize(obj, ctx), f"{label} created")

            register(
                "",
                create_endpoint,
                ["POST"],
                response_model=EnvelopeResponse[schemas["out"]],
                status_code=201,
                summary=f"Create {label.lower()}",
                rate_limit=rl,
            )

        if "retrieve" in wanted:
            ctx_dep = cls._ctx_dependency("retrieve", cls._auth_dependency("retrieve"))

            async def retrieve_endpoint(
                request: Request, id: str, ctx: ViewContext = Depends(ctx_dep)
            ):
                obj = await view.get_object(ctx, id)
                return success_response(await view.serialize(obj, ctx), f"{label} retrieved")

            register(
                "/{id}",
                retrieve_endpoint,
                ["GET"],
                response_model=EnvelopeResponse[schemas["out"]],
                status_code=200,
                summary=f"Get {label.lower()}",
                rate_limit=rl,
            )

        for name, method, body in (
            ("update", "PUT", schemas["create"]),
            ("partial_update", "PATCH", schemas["update"]),
        ):
            if name not in wanted:
                continue
            ctx_dep = cls._ctx_dependency(name, cls._auth_dependency(name))
            partial = name == "partial_update"

            async def update_endpoint(
                request: Request,
                id: str,
                data: body,  # type: ignore[valid-type]
                ctx: ViewContext = Depends(ctx_dep),
                _partial: bool = partial,
            ):
                obj = await view.get_object(ctx, id)
                submitted = data.model_dump(exclude_unset=_partial)
                values = await view.validate(submitted, ctx, obj)
                obj = await view._save(ctx, view.perform_update(obj, values, ctx))
                await view._audit(ctx, "update", obj, sorted(values))
                return success_response(await view.serialize(obj, ctx), f"{label} updated")

            update_endpoint.__signature__ = inspect.signature(update_endpoint).replace(
                parameters=[
                    p
                    for p in inspect.signature(update_endpoint).parameters.values()
                    if p.name != "_partial"
                ]
            )
            register(
                "/{id}",
                update_endpoint,
                [method],
                response_model=EnvelopeResponse[schemas["out"]],
                status_code=200,
                summary=f"{'Partially update' if partial else 'Replace'} {label.lower()}",
                rate_limit=rl,
            )

        if "destroy" in wanted:
            ctx_dep = cls._ctx_dependency("destroy", cls._auth_dependency("destroy"))

            async def destroy_endpoint(
                request: Request, id: str, ctx: ViewContext = Depends(ctx_dep)
            ):
                obj = await view.get_object(ctx, id)
                await view.perform_destroy(obj, ctx)
                await view._audit(ctx, "delete", obj, None)
                return success_response(None, f"{label} deleted")

            register(
                "/{id}",
                destroy_endpoint,
                ["DELETE"],
                response_model=EnvelopeResponse[None],
                status_code=200,
                summary=f"Delete {label.lower()}",
                rate_limit=rl,
            )

        return router

    @classmethod
    def _register_custom_action(
        cls, view: "ModelView", name: str, meta: _ActionMeta, register: Callable
    ) -> None:
        bound = getattr(view, name)
        sig = inspect.signature(bound, eval_str=True)
        permission = meta.permission
        if permission is None and not meta.public:
            permission = cls.permissions.get(name) or cls.permission_for("update")
        auth_dep = cls._auth_dependency(name, public=meta.public, permission=permission)
        ctx_dep = cls._ctx_dependency(name, auth_dep)

        params = []
        for param in sig.parameters.values():
            if param.name == "ctx":
                param = param.replace(annotation=ViewContext, default=Depends(ctx_dep))
            params.append(param)
        if "request" not in sig.parameters and meta.rate_limit:
            params.insert(
                0,
                inspect.Parameter(
                    "request", inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=Request
                ),
            )

        async def endpoint(**kwargs):
            call_kwargs = {k: v for k, v in kwargs.items() if k in sig.parameters}
            result = await bound(**call_kwargs)
            if isinstance(result, Response) or not meta.envelope:
                return result
            return success_response(result, meta.summary or name.replace("_", " ").capitalize())

        endpoint.__name__ = name
        endpoint.__signature__ = inspect.Signature(  # type: ignore[attr-defined]
            params, return_annotation=inspect.Signature.empty
        )
        sub_path = meta.path if meta.path is not None else name.replace("_", "-")
        path = f"/{{id}}/{sub_path}" if meta.detail else f"/{sub_path}"
        if meta.detail and "id" not in sig.parameters:
            raise RuntimeError(f"{cls.__name__}.{name}: detail actions must accept `id: str`")
        model = (
            EnvelopeResponse[meta.response_model]
            if (meta.envelope and meta.response_model is not None)
            else (EnvelopeResponse[Any] if meta.envelope else meta.response_model)
        )
        register(
            path,
            endpoint,
            list(meta.methods),
            response_model=model,
            status_code=meta.status_code,
            summary=meta.summary or name.replace("_", " ").capitalize(),
            rate_limit=meta.rate_limit,
        )


class ReadOnlyModelView(ModelView):
    """List + retrieve only."""

    actions: ClassVar[tuple[str, ...]] = READ_ONLY_ACTIONS


__all__ = [
    "CRUD_ACTIONS",
    "READ_ONLY_ACTIONS",
    "ModelView",
    "ReadOnlyModelView",
    "ViewContext",
    "action",
    "partial_schema",
]
