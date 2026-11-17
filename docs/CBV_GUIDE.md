# Class-Based Views (CBV) Guide

`app/base/views.py` gives every module a Django-style way to expose a Tortoise
model as REST endpoints. A view says **which model, which schemas, who may call
it, what can be filtered** — the endpoints, validation, pagination, response
envelope, permissions, audit rows, and Swagger models are generated.

Plain CRUD → a view. Anything with real business logic → a function in
`services/`, called from a view hook or an `@action` method.

## Minimal view

```python
# app/<module>/views.py
from app.base.views import ModelView

class FirmAdminView(ModelView):
    model = Firm
    prefix = "/admin/firms"
    tags = ["Administration"]
    audience = ("admin",)               # which OpenAPI doc lists it: app | admin
    permission_module = "firms"         # firms.read / create / update / delete
    create_schema = FirmCreate
    update_schema = FirmPatch           # omit → every create field optional
    out_schema = FirmOut
    search_fields = ("name", "cmsa_firm_id")   # ?q=
    filter_fields = ("status", "category", "created_at__gte")
    ordering_fields = ("name", "created_at")   # ?ordering=-created_at
    audit = True

router = FirmAdminView.as_router()          # app/<module>/routes.py
```

Mount it in `app/config/routes.py` (`api_router.include_router(router)`).

Omit all schemas and they are generated from the model (flat models only).

## What you get

| Action | Method + path | Permission verb |
| --- | --- | --- |
| `list` | `GET {prefix}` | `read` |
| `create` | `POST {prefix}` | `create` |
| `retrieve` | `GET {prefix}/{id}` | `read` |
| `partial_update` | `PATCH {prefix}/{id}` | `update` |
| `update` | `PUT {prefix}/{id}` (opt-in) | `update` |
| `destroy` | `DELETE {prefix}/{id}` | `delete` |

Default `actions` = list, create, retrieve, partial_update, destroy. Narrow
with `actions = (...)`, or subclass `ReadOnlyModelView`.

Every response uses the standard envelope
`{"success": true, "message": "...", "data": ...}`; list `data` is
`{"items": [...], "meta": {page, page_size, total_items, ...}}` with
`?page=&page_size=`. Not found → `404 {code: "<slug>_not_found"}`; unique
violation → `409 {code: "<slug>_conflict"}` (override with `conflict_code`).

## Auth knobs

- `permission_module = "firms"` → `firms.<verb>` per action table above.
- `permissions = {"*": "x.manage", "list": "x.read"}` → explicit overrides.
- `public_actions = ("list", "retrieve")` → no auth (Swagger shows no lock).
- `authenticated_actions = ("list",)` → any active login, no RBAC codename.
- Register new codenames in `permissions.py`, then
  `uv run python scripts/sync_permissions.py`.

## Row scoping (firm isolation, "my records")

```python
async def get_queryset(self, ctx):
    return Invoice.filter(firm_id=await firm_id_for(ctx.account_id))
```

`get_queryset` feeds list **and** retrieve/update/delete, so out-of-scope rows
are simply 404.

## Hooks

| Hook | Default | Override to |
| --- | --- | --- |
| `get_queryset(ctx)` | `Model.all()` | scope rows |
| `filter_queryset(qs, ctx, filters)` | q / filters / ordering | custom filtering |
| `validate(values, ctx, instance=None)` | passthrough | business rules, derived values (calls services) |
| `perform_create(values, ctx)` | `Model.create` | delegate to a service |
| `perform_update(obj, values, ctx)` | setattr + save | delegate to a service |
| `perform_destroy(obj, ctx)` | delete / soft delete | cascade, guards |
| `serialize(obj, ctx, many=False)` | `out_schema.model_validate` | computed fields |

`soft_delete_field = "is_active"` (bool) or a datetime field flips the flag
instead of deleting.

## Custom endpoints

```python
from app.base.views import action, ViewContext

class FirmAdminView(ModelView):
    ...
    @action(detail=True, methods=("POST",), permission="firms.suspend",
            response_model=FirmOut)
    async def suspend(self, id: str, body: SuspendBody, ctx: ViewContext):
        return await firm_services.suspend_firm(id, body.reason, ctx.account_id)
```

`POST /admin/firms/{id}/suspend`. Parameters are normal FastAPI parameters;
`ctx` is injected. Return a dict/schema (enveloped) or a `Response` (raw).
`detail=False` gives a collection route (`/admin/firms/export`). Register the
codename (`firms.suspend`) in `permissions.py`.

## Public + admin from one model

Declare two subclasses. They land in different docs (`/docs` vs `/docs/admin`,
`/openapi/app.json` vs `/openapi/admin.json`):

```python
class FirmPublicView(ReadOnlyModelView):
    prefix = "/public/firms"; audience = ("app",)
    public_actions = ("retrieve",); actions = ("retrieve",)
    lookup_field = "cmsa_firm_id"; out_schema = FirmPublicOut
```

## Rules

- Do not add `from __future__ import annotations` in `app/base/views.py`.
  Other modules may; hook/action annotations are resolved from their own module.
- Keep views declarative. If a hook grows past ~10 lines, move it to `services/`.
- Reference implementation: `app/app_releases/views.py`; behaviour tests:
  `app/base/tests/unit/test_views.py`.
