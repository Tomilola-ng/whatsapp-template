# AGENTS.md

This file is the working guide for coding agents in this repository.

## Mission

Treat this repo as a **WhatsApp FastAPI starter base**, not as a delivery product clone.

The supported core template surface is:

- `app/access`
- `app/accounts`
- `app/base`
- `app/contact`
- `app/records`
- `app/config`
- `app/integration`
- `app/audit`
- `app/client_errors`
- `app/app_releases`
- `app/whatsapp`

## Core Principles

1. Keep the starter truthful.
   - Only document or register modules that actually exist and are intended to ship in the base template.
   - If a route, model module, or integration is not ready, do not wire it into startup just because a future plan mentions it.

2. Keep the starter generic.
   - Prefer `provider` over delivery-specific role language like `rider`.
   - Avoid product-branded copy, domain-specific onboarding flows, or vertical assumptions in reusable helpers.

3. Keep first boot simple.
   - The default `.env.sample` should remain usable for local boot.
   - Optional integrations must fail clearly when used, but should not break import or startup when unset.

4. Keep route handlers thin — prefer class-based views for CRUD.
   - Plain CRUD over a model is a `ModelView` in `app/<module>/views.py` (built on `app/base/views.py`, guide: `docs/CBV_GUIDE.md`); do not hand-write list/get/create/patch/delete route functions.
   - Put business logic in `services/` modules and call it from a view hook (`validate`, `perform_create`, ...) or an `@action` method.
   - Use `schemas.py` for request and response contracts.
   - Keep shared helpers in `app/base` or `app/config` when they are truly cross-cutting.

5. Prefer a thin public surface over deleting modules.
   - To ship a mobile-only or API-only launch, **omit routers from** `app/config/routes.py` (and Tortoise model paths only when tables are truly unused).
   - Do **not** delete `app/records`, email/OTP services, or purge logic just because those routes are offline.
   - Keep the permission registry and account deletion purge complete for modules that remain in the tree.
   - Optional pattern: a smaller router module (for example `mvp_routes.py`) that mounts only the endpoints you are launching, while the full `routes.py` stays available to re-enable later.

6. Keep planning honest.
   - Do not mark work as complete unless it is actually implemented and verified.
   - Do not let docs overstate repo reality.
   - Make assumptions explicit instead of silently inventing behavior.

## Spec-Driven Development

Product and starter hardening work is planned under `spec/` and documented for humans under `docs/`:

- `docs/PROJECT_SPEC.md` — project overview, scope, fork guidance
- `docs/FEATURES.md` — feature inventory with status
- `docs/API_CONTRACT.md` — HTTP contract for registered routes
- `docs/DATABASE_SPEC.md` — schema and migration rules
- `docs/IMPLEMENTATION_PLAN.md` — phased build and fork milestones
- `spec/README.md` — agent reconciliation layer introduction
- `spec/API.md` — endpoint contract mirror
- `spec/AUTH_AND_PERMISSIONS.md` — user types, RBAC, admin provisioning
- `spec/DATABASE.md` — schema mirror
- `spec/CHANGES.md` — reconciliation ledger
- `spec/TASKS/OVERVIEW.md` — ordered starter tasks

When implementing features:

1. Read the relevant task file under `spec/TASKS/`.
2. Update `docs/API_CONTRACT.md` or `docs/DATABASE_SPEC.md` when contracts change (mirror in `spec/` when needed).
3. Record intentional differences in `spec/CHANGES.md`.

## Migrations

**Never manually create or edit files under `migrations/models/`.**

Schema changes flow:

1. Update Tortoise models and `docs/TEMPLATE_SCHEMA.dbml`.
2. Run `uv run aerich migrate --name describe_change`.
3. Run `uv run aerich upgrade`.
4. Check in the generated Aerich history.

Use `uv run python scripts/migrate.py` for a guided wrapper. See `spec/DATABASE.md` and task `006_MIGRATIONS_AND_SCHEMA_BASELINE.md`.

## Current Architecture

- `main.py`
  - Creates the FastAPI app
  - Registers Tortoise and optional rate limiting
  - Mounts the API router under `settings.API_V1_PREFIX`
  - When OpenAPI is enabled: app + admin schemas (`/docs`, `/docs/admin`)
  - Request ID + structured request logging middleware

- `app/config/settings.py`
  - Single source of truth for env vars
  - Owns the supported Tortoise model list
  - Validates signing secrets in staging/production

- `app/config/routes.py`
  - Only include routers for supported starter modules

- `docs/BUGFIX_LOG.md` before patching a user-facing bug
- `docs/PRODUCT_CHANGELOG.md` + `client-handoff/` for intentional client-facing changes
- `docs/DECISIONS.md` for locked starter defaults
- `docs/E2E_COVERAGE.md` before claiming E2E green means client-complete

- `app/accounts`
  - Auth, OTP, password reset, profile updates
  - Register OTP auto-login; optional email MFA via preferences
  - Admin invite/upgrade helpers live in `services/core.py`
  - Admin provisioning via `scripts/create_admin.py` and `exchange-setup-code`

- `app/access`
  - Permission registry, access roles, JWT authorization guards, `/access/*` management routes
  - Default roles seeded on startup; run `scripts/sync_permissions.py` after adding codenames

- `app/base`
  - `views.py`: Django-style class-based CRUD views (`ModelView`, `ReadOnlyModelView`, `@action`)
  - Shared IDs, email sending, health check, file helpers, rate limiting
  - Modern email template helpers + OpenAPI audience split + transition helper

- `app/records`
  - Notifications, OTP records, password setup codes

- `app/contact`
  - Public contact form endpoint

- `app/integration`
  - Thin wrappers around optional third-party services such as R2, Paystack, and Prembly

- `app/audit`
  - Append-only redacted audit trail and `audit_logs.read` staff route

- `app/client_errors`
  - Public client-error ingest and environment-aware staff inspection

- `app/app_releases`
  - Optional mobile/web update policy, legal URLs, admin release CRUD, optional SSE

## Files Agents Should Read First

- `README.md`
- `docs/PROJECT_SPEC.md`
- `docs/DECISIONS.md`
- `docs/FEATURES.md`
- `docs/API_CONTRACT.md`
- `docs/CBV_GUIDE.md`
- `docs/DATABASE_SPEC.md`
- `docs/IMPLEMENTATION_PLAN.md`
- `docs/SETUP_GUIDE.md`
- `docs/API_KEYS_GUIDE.md`
- `docs/BUGFIX_LOG.md`
- `docs/PRODUCT_CHANGELOG.md`
- `docs/E2E_COVERAGE.md`
- `spec/TASKS/OVERVIEW.md`
- `app/config/settings.py`
- `app/config/routes.py`

If the task touches schema or long-term template shape, also read:

- `docs/TEMPLATE_SCHEMA.dbml`
- `spec/AUTH_AND_PERMISSIONS.md`

## Source-of-Truth Rules

When working from a product prompt, use sources in this order unless the user explicitly changes it:

1. Attached functional specification or `spec/` docs
2. Existing repo code and current repo conventions
3. `AGENTS.md`
4. Public website or product copy, only as supporting context

Rules:

- Do not invent backend behavior from website copy alone.
- If the functional spec is missing, incomplete, or contradictory, say so clearly.
- Prefer the smallest reasonable assumption and document it in `spec/CHANGES.md`.

## Guardrails

### Startup and settings

- Do not add imports in `main.py` or `app/config/routes.py` for modules that do not exist.
- Do not add model paths to `AppSettings.tortoise_models` until those model modules are real and intended to be part of the starter.
- Keep `.env.sample` aligned with `AppSettings`.
- Preserve first boot. Optional product modules must not break import or startup unless the user explicitly wants the repo converted into a product-specific app.

### Integrations

- R2, Resend, Paystack, and Prembly are supported integrations, but they are optional.
- Integration clients should avoid eager failures during module import when env vars are absent.
- When adding new integration settings, update:
  - `.env.sample`
  - `docs/API_KEYS_GUIDE.md`
  - `docs/SETUP_GUIDE.md` if first-run behavior changes

### Naming

- Use `provider`, not `rider`, in active code and active docs unless the user explicitly requests a domain-specific feature.
- Keep user-facing copy generic and reusable.
- Avoid hardcoded company names, product URLs, and branded support addresses in reusable templates.

### Services and module structure

- Prefer standardized global services for cross-cutting concerns.
- Reuse global service conventions before inventing one-off helpers inside a feature module.
- For small starter modules, a single `services/core.py` is fine.
- Route handlers stay thin.
- New modules with protected routes should register permissions in `permissions.py` via `app.access.permission_registry.register_module()` and protect routes with `app.access.permissions.require_permission(...)`.
- Run `uv run python scripts/sync_permissions.py` after adding permission codenames.

### Data model

- Prefer prefixed string IDs for application-owned records.
- Keep `docs/TEMPLATE_SCHEMA.dbml` aligned with the supported core starter model set.
- Never hand-edit Aerich migration files.

### Planning docs and status rules

- Keep generic template docs under `docs/` and `spec/`.
- Product-specific planning artifacts should live under `docs/<product-or-domain>/` in forks.

Allowed checklist statuses:

- `planned`
- `existing`
- `needs_refactor`
- `stubbed`

## Common Workflows

### Add a new module

1. Scaffold with `python startapp.py <module_name> --extended` or `python scripts/startapp.py <module_name> --extended`.
2. Replace the placeholder example model and view (`views.py`); add schemas/services only where behaviour is non-trivial.
3. Register the router only when the module is real.
4. Add the model path to `AppSettings.tortoise_models` only if the module owns DB tables.
5. Run Aerich migrate/upgrade and update docs if the public template surface changed.

### Add a new env var

1. Add it to `AppSettings`.
2. Add it to `.env.sample`.
3. Update the relevant docs.
4. Make sure missing values produce a clear runtime error only where needed.

### Add an admin or utility script

- Prefer using the existing application model and service layer rather than inventing a parallel data shape.
- Keep scripts import-safe by ensuring the repo root is on `sys.path`.
- Admin accounts: `uv run python scripts/create_admin.py --email admin@example.com` (optional `--phone-number`, `--name`). No HTTP `make-admin` route.

### Plan product work

1. Audit the repo first.
2. Add or update tasks under `spec/TASKS/`.
3. Reuse current helpers before adding new abstractions.
4. Preserve bootability unless the user explicitly wants a repo-wide product conversion.

## Verification

Preferred when dependencies are installed:

```powershell
uv sync
uv run python -m compileall app scripts main.py startapp.py
uv run fastapi dev main.py
```

Useful smoke checks:

- `GET /api/v1/health`
- `GET /docs` (local or when `OPENAPI_ENABLED=true`)

Shell/curl E2E is the source of truth for HTTP behavior. Keep unit tests to the
allowlist in `app/base/tests/README.md`. After fixing a user-facing bug, add a
verified entry to `docs/BUGFIX_LOG.md`.

For planning-heavy work:

- verify documented env vars against `AppSettings`
- verify documented endpoints against actual router registration
- verify claimed existing functionality against real files and symbols
- verify migration files were generated by Aerich, not hand-written

## Scripts

Current utility scripts:

- `scripts/generate_secrets.py`
  - generates signing/job secrets; use `--write .env`

- `scripts/create_admin.py`
  - creates or promotes an admin account by **email** (required)
  - optional `--phone-number` and `--name`
  - sends an invite or upgrade email with an opaque setup code link

- `scripts/migrate.py`
  - Rich-powered wrapper around Aerich (`init`, `init-db`, `migrate`, `upgrade`, `heads`, `history`)
  - prints warnings never to hand-edit `migrations/models/`

- `scripts/clear_model.py`
  - deletes all rows for a fully-qualified Tortoise model path

- `scripts/startapp.py`
  - scaffolds a new module

- `scripts/sync_permissions.py`
  - syncs code-first permission registry rows and default access roles into the database

- `scripts/e2e_issue_token.py`
  - creates/activates an account and prints access + refresh JWTs (no email/OTP)

There is also a root `startapp.py` shim; keep script behavior consistent if one copy changes.

## When Unsure

- Prefer the simpler starter shape.
- Prefer optional integrations over required ones.
- Prefer compile-safe, boot-safe changes over speculative architecture.
- Prefer updating `spec/` and docs along with code so future agents do not inherit drift.
- Prefer explicit assumptions in `spec/CHANGES.md` over hidden guesses.
