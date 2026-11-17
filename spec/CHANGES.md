# Specification Reconciliation Ledger

Record differences among `docs/TEMPLATE_SCHEMA.dbml`, `spec/API.md`, live code, and any external product briefs.

## Format

Each entry should include:

- **Area** — feature or module
- **Spec expectation** — what the spec says
- **Repository reality** — what the code does today
- **Resolution** — chosen direction for implementation

## Entries

### 2026-11-10 - Selective root sync + WhatsApp hardening (single-WABA)

- **Area** — Platform CBV; WhatsApp services package and safety helpers.
- **Spec expectation** — WhatsApp starter stays single-number PyWa (no multi-tenant middleware, no mobile SSO/billing).
- **Repository reality** — Upstream mobile bases added CBV and multi-tenant WhatsApp middleware after the Sept 9 strip.
- **Resolution** — Ported CBV (`app/base/views.py`, app_releases admin). Extracted generic WhatsApp patterns (error classify, media allowlist, service window, template helper, soft retry, threat docs) into `app/whatsapp/services/`. Kept OAuth/Expo/RevenueCat/`app/billing` and multi-tenant Embedded Signup/usage out of this starter.

### 2026-09-09 - Strip mobile-app surface for WhatsApp starter

- **Area** — Auth SSO, billing, Expo push, mobile identity fields.
- **Spec expectation** — Starter should be a WhatsApp FastAPI base without mobile-store billing or social SSO.
- **Repository reality** — Google/Apple SSO, RevenueCat, Expo push tokens, and related settings/docs were still present.
- **Resolution** — Removed those modules/endpoints/settings. Kept email/OTP auth, in-app notifications (SSE), `app_releases`, R2/Resend/Paystack/Prembly, and `app/whatsapp`. Tortoise models updated; docs/spec reconciled; Aerich migrate still required for Postgres schema drift.

### 2026-08-05 - Generic production-wins backport

- **Area** — Authentication, observability, notifications, maintenance, and agent operations.
- **Spec expectation** — Reusable production hardening should remain generic and boot-safe.
- **Repository reality** — Audit/client diagnostics, SSE notifications, preferences/deletion, OTP login handoff, and regression coverage were absent or partial.
- **Resolution** — Backported and genericized those capabilities. No forms, generation, credits, collaboration, responses, exports, analytics, voice, or product admin suite was ported.

### 2026-07-04 - Infrastructure hardening batch

- **Area** — Dev outbox and E2E testing
- **Spec expectation** — Local OTP tests should fetch codes through HTTP, not database queries.
- **Repository reality** — The repo did not have a dev outbox or shell/curl E2E harness.
- **Resolution** — Added local-only email/SMS capture, `/dev/outbox/latest-otp`, and black-box shell runners under `app/base/tests` and module `tests/` folders.

### 2026-07-04 - File route auth truthfulness

- **Area** — File endpoints
- **Spec expectation** — `spec/API.md` claimed `/base/files` required active authentication.
- **Repository reality** — Initial starter shipped file routes without auth guards.
- **Resolution** — Starter file routes now require active authentication plus `files.create` / `files.read` permission codenames; docs and client checklists updated accordingly.

### 2026-07-04 - Service package layout

- **Area** — Module layout
- **Spec expectation** — Older task overview described a root `services.py`.
- **Repository reality** — The desired module layout now uses `services/` packages with `core.py`.
- **Resolution** — Converted supported starter service modules to package form and updated `startapp.py` plus Cursor rules.

### 2026-07-04 - RBAC and user_type rename

- **Area** — Access control
- **Spec expectation** — Single `Account.role` enum with coarse route guards.
- **Repository reality** — Starter needed granular permissions, access roles, and JWT-embedded permission checks.
- **Resolution** — Renamed `role` → `user_type`; added RBAC in standalone `app/access/` module (models, registry, JWT guards, `/access/*` routes); wired permission checks on files and notifications.

### 2026-07-04 - Access module extraction

- **Area** — Module layout
- **Spec expectation** — RBAC initially colocated under `app/accounts/`.
- **Repository reality** — Access control is cross-cutting and deserves its own package.
- **Resolution** — Moved models, services, registry, JWT guards, routes, tests, and handoff to `app/access/`. Accounts keeps identity/auth and active-user guards only.

### 2026-07-04 - RBAC security hardening (code review)

- **Area** — Access control enforcement
- **Spec expectation** — Permission checks honor session revocation; role assignment prevents self-escalation.
- **Repository reality** — Initial RBAC used JWT-only checks on admin routes; startup re-seeded system roles; `customer_basic` lacked `notifications.manage`.
- **Resolution** — `require_permission` validates `v`/`pv` and active status via DB; assignment policy blocks self-modification and over-privileged grants; startup seed only fills missing system role permissions; `/access/*` rate-limited. (Device-token permissions were later removed with the 2026-09-09 mobile surface strip.)

### 2026-07-04 - Aerich baseline migration

- **Area** — Database migrations
- **Spec expectation** — CI E2E runs `aerich upgrade` before smoke tests.
- **Repository reality** — Baseline migration not yet generated in-repo; local SQLite Aerich init fails (Tortoise `Connection.start`); Postgres URL must use `postgres://` scheme for Aerich.
- **Resolution** — Generate with `DATABASE_URL=postgres://... uv run aerich init-db` against PostgreSQL (see CI workflow), then commit `migrations/`. Local dev may still use `generate_schemas=True` when `ENVIRONMENT=local`.
