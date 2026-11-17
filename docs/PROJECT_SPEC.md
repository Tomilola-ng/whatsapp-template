# WhatsApp FastAPI 2026 Template — Project Specification

## Product Overview

This repository is a **WhatsApp-oriented FastAPI starter base**, not a finished product. **WhatsApp (Meta Cloud API via PyWa) is the supported messaging channel.** It ships the cross-cutting backend pieces most API backends need first: email/OTP auth, RBAC, file uploads, in-app notifications (SSE), contact capture, optional integrations, and a stub WhatsApp inbound/outbound pipeline you extend in your fork.

Fork this repo when you want a bootable API skeleton. Replace generic copy, add domain modules (including WhatsApp), and grow `docs/TEMPLATE_SCHEMA.dbml` (or add a product `DATABASE.dbml` in your fork) as your product takes shape.

## Source Of Truth

Use sources in this order:

1. `docs/PROJECT_SPEC.md`, `docs/FEATURES.md`, `docs/API_CONTRACT.md`, and `docs/DATABASE_SPEC.md`
2. `docs/TEMPLATE_SCHEMA.dbml` for starter schema shape
3. `spec/TASKS/` for ordered hardening and verification work
4. Live repository code and `AGENTS.md`

Record intentional differences in `spec/CHANGES.md`.

## User Types

`Account.user_type` describes the product persona. It is **not** the same as access roles.

| User type  | Meaning                          | Default access role |
| ---------- | -------------------------------- | ------------------- |
| `customer` | Default end-user                 | `customer_basic`    |
| `provider` | Generic service-provider persona | `provider_basic`    |
| `admin`    | Staff / back-office persona      | `super_admin`       |

Any user type may receive additional access roles or direct permission grants.

## Business Rules

- Public registration creates a `pending_verification` account; OTP verification activates it.
- Login and protected starter routes require **active** account status.
- Access and refresh tokens are JWTs with session version fields; logout, password change, and permission changes revoke stale tokens.
- Permission checks use JWT snapshots plus live `auth_token_version` / `permissions_version` validation.
- Admin accounts are provisioned with `scripts/create_admin.py` — there is no HTTP `make-admin` route.
- Notifications are recipient-scoped; users may only read their own rows.
- File uploads require R2 credentials when used; listing is local-dev only by default.
- Optional integrations (Resend, R2, Paystack, Prembly) must not break import or startup when unset.
- Rate limiting is enabled by default; use a shared backend before horizontal scaling.

## In Scope (Starter)

| Area | Module | Summary |
| ---- | ------ | ------- |
| Auth & profiles | `app/accounts` | Password/email OTP auth, preferences, deletion, profiles |
| Access control | `app/access` | Permissions, access roles, JWT guards, `/access/*` admin API |
| Shared platform | `app/base` | Health, file assets, email helpers, rate limiting, E2E harness |
| Records | `app/records` | Notifications, OTP persistence |
| Contact | `app/contact` | Public contact form |
| Config | `app/config` | Settings, database, pagination, router registration |
| Integrations | `app/integration` | Optional R2, Resend, Paystack, Prembly wrappers |
| Jobs | `app/schedules` | Internal maintenance entrypoint pattern |
| Audit | `app/audit` | Redacted append-only staff trail |
| Client diagnostics | `app/client_errors` | Client error ingest and inspection |
| App releases | `app/app_releases` | Optional update policy and legal URLs |
| WhatsApp | `app/whatsapp` | Meta webhook, inbound handlers, stub brain, local test routes |

## Out Of Scope (Starter)

- Product-specific domains (marketplaces, rentals, wallets, social graphs, etc.)
- Mobile store billing and entitlements (RevenueCat and similar)
- Mobile SSO (Apple Sign-In, Google Sign-In) and Expo/native push delivery
- Payment collection and entitlement logic beyond optional Paystack/Prembly scaffolds
- Identity verification workflows (Prembly client is scaffolded only)
- Admin UI, multi-tenant org roles, row-level ABAC
- Committed Aerich baseline migrations (forks own `aerich init-db` for their deploy target)

## Supported Modules Layout

```text
app/<domain>/
  models.py
  schemas.py
  services/
    __init__.py
    core.py
  routes.py
  utils.py
  tests/
  handoff/
  permissions.py   # optional; register codenames via app.access.permission_registry
```

RBAC lives in `app/access/`. Account active-status guards stay in `app/accounts/permissions.py`.

## First Boot Expectations

1. Copy `.env.sample` → `.env`.
2. `uv sync`
3. `uv run fastapi dev main.py`
4. `GET /api/v1/health`

With `ENVIRONMENT=local` and SQLite, Tortoise may auto-create tables. Default access roles seed on startup. For production PostgreSQL, run Aerich in your fork and commit the generated history.

## Forking A New Product

When this template becomes the base for a real product:

1. Copy or extend `docs/PROJECT_SPEC.md` with your product overview and business rules.
2. Add `docs/FEATURES.md` entries for new capabilities and mark status honestly.
3. Extend `docs/API_CONTRACT.md` and `docs/DATABASE_SPEC.md` (or add a root `DATABASE.dbml` like product forks do).
4. Update `docs/IMPLEMENTATION_PLAN.md` with product milestones.
5. Scaffold modules with `python scripts/startapp.py <name> --extended`.
6. Register permissions, routes, and models only when modules are real.
7. Keep `spec/CHANGES.md` as the reconciliation ledger when starter assumptions change.

## Acceptance Criteria (Starter)

- App boots with default `.env.sample` on SQLite.
- Documented routes in `docs/API_CONTRACT.md` match registered routers.
- Schema in `docs/TEMPLATE_SCHEMA.dbml` matches supported Tortoise models.
- Shell E2E harness passes against PostgreSQL when `.env.e2e` is configured.
- Optional integration env vars left empty do not break startup.
