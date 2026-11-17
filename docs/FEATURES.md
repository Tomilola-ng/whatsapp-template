# WhatsApp FastAPI 2026 Template — Features

Status values: **existing** (shipped), **planned** (documented but not implemented), **stubbed** (scaffold only).

## Account & Auth

| Feature | Status | Module | Notes |
| ------- | ------ | ------ | ----- |
| Email/password registration | existing | `app/accounts` | Creates `pending_verification` account |
| Email OTP account verification | existing | `app/accounts` | Activates and returns login JWTs (auto-login) |
| Login / logout | existing | `app/accounts` | JWT access + refresh; logout revokes token version |
| Optional email MFA on login | existing | `app/accounts` | Preferences `email_login_mfa_enabled`; `POST /auth/verify-login-otp` |
| Refresh token | existing | `app/accounts` | Re-issues access token with current permissions |
| Current user profile | existing | `app/accounts` | `GET /auth/current-user`, `GET /auth/me` |
| Profile update | existing | `app/accounts` | `PATCH /auth/update-profile` (first/last/phone/state + optional username/display_name) |
| Profile image upload | existing | `app/accounts` | `PATCH /auth/update-user-image` |
| Forgot / reset password | existing | `app/accounts` | OTP → short-lived reset JWT → new password |
| Change password (authenticated) | existing | `app/accounts` | Revokes other sessions |
| Admin invite via setup code | existing | `app/accounts` | `exchange-setup-code` + `create_admin.py` script |
| Account preferences | existing | `app/accounts` | In-app/email/marketing notification prefs + optional email login MFA |
| Self-service account deletion | existing | `app/accounts` | Revokes auth, anonymizes PII, purges starter rows |
| Public signup for admin | planned | — | Intentionally excluded |

## Access Control (RBAC)

| Feature | Status | Module | Notes |
| ------- | ------ | ------ | ----- |
| Code-first permission registry | existing | `app/access` | `permission_registry.py` + `sync_permissions.py` |
| Access roles with permission bundles | existing | `app/access` | System roles seeded on startup |
| Direct permission grants/denies | existing | `app/access` | Per-account overrides |
| JWT permission snapshots (`ut`, `perms`, `pv`) | existing | `app/access` | Validated against DB on protected routes |
| `GET /access/me/permissions` | existing | `app/access` | Client permission cache endpoint |
| Staff role CRUD API | existing | `app/access` | `/access/roles` — blocked for system roles |
| Account role assignment API | existing | `app/access` | Self-escalation blocked |
| Default role: `super_admin` | existing | `app/access` | Full `*` permission |
| Default role: `accounts_manager` | existing | `app/access` | Account + assignment management |
| Default role: `content_admin` | existing | `app/access` | Files + contact inbox + app releases |
| Default role: `customer_basic` | existing | `app/access` | Notifications read/manage |
| Default role: `provider_basic` | existing | `app/access` | Notifications + file create/read |
| Row-level / object ABAC | planned | — | Out of scope for starter |
| Redis permission cache | planned | — | Out of scope for starter |

## Files

| Feature | Status | Module | Notes |
| ------- | ------ | ------ | ----- |
| R2 multipart upload | existing | `app/base` | Requires `files.create` + R2 env vars |
| Local file listing (paginated) | existing | `app/base` | `ENVIRONMENT=local` only; requires `files.read` |
| File ownership enforcement | planned | `app/base` | Upload stores asset; owner link optional in model |

## Notifications

| Feature | Status | Module | Notes |
| ------- | ------ | ------ | ----- |
| In-app notification persistence | existing | `app/records` | Recipient-scoped |
| List notifications (paginated) | existing | `app/records` | Requires `notifications.read` |
| Mark notification read | existing | `app/records` | Owner check + `notifications.read` |
| Per-account SSE stream | existing | `app/records` | `GET /notifications/stream` |
| Staff broadcast | existing | `app/records` | Requires `notifications.broadcast` |
| Email/SMS delivery worker | stubbed | `app/base` | Email helpers exist; delivery is integration-dependent |

## Contact

| Feature | Status | Module | Notes |
| ------- | ------ | ------ | ----- |
| Public contact form | existing | `app/contact` | Rate limited; emails via Resend when configured |
| Admin contact inbox API | planned | `app/contact` | Permissions registered; routes not wired |

## Platform & Operations

| Feature | Status | Module | Notes |
| ------- | ------ | ------ | ----- |
| Health check | existing | `app/base` | `GET /health` |
| Dual OpenAPI (app + admin) | existing | `app/base` | `/docs`, `/docs/admin`; `scripts/export_openapi.py` |
| Class-based CRUD views | existing | `app/base/views.py` | `ModelView`; guide in `docs/CBV_GUIDE.md` |
| Modern email kit + preview | existing | `app/base` | Shared shell/helpers; `scripts/preview_emails.py` + `email-preview/` |
| App update policy + legal URLs | existing | `app/app_releases` | `GET /app/update-policy`, `GET /app/legal`, admin CBV CRUD, optional SSE |
| Request ID + structured logs | existing | `main.py` | `X-Request-ID` middleware |
| Container ops roles | existing | `scripts/ops` | `api` / `worker` / `migrate` entrypoint |
| Rate limiting (slowapi) | existing | `app/base` | Per-route limits; optional Redis backend |
| Dev email/SMS outbox | existing | `app/integration` | Local + `DEV_OUTBOX_ENABLED` only |
| Shell/curl E2E harness | existing | `app/base/tests` | Black-box HTTP tests |
| Internal maintenance job | existing | `app/schedules` | `X-Internal-Token` pattern |
| Audit logging | existing | `app/audit` | Redacted metadata + idempotency key |
| Client error logging | existing | `app/client_errors` | Public ingest; staff read in production |
| OpenAPI docs gate | existing | `app/config` | Hidden unless `OPENAPI_ENABLED=true` |
| Module scaffolder (`startapp.py`) | existing | `scripts/` | Standard and `--extended` layouts |
| Committed Aerich migration baseline | existing | `migrations/` | Generated from the supported starter models |

## Optional Integrations

| Feature | Status | Module | Notes |
| ------- | ------ | ------ | ----- |
| Resend email | existing | `app/base` | Auth, contact, admin invite emails |
| Cloudflare R2 storage | existing | `app/config` | File uploads |
| Paystack client | stubbed | `app/integration` | Helper only; no payment routes |
| Prembly client | stubbed | `app/integration` | Helper only; no verification routes |

## WhatsApp

| Feature | Status | Module | Notes |
| ------- | ------ | ------ | ----- |
| PyWa attach + Meta webhook | existing | `app/whatsapp` | Off until `WHATSAPP_ENABLED=true` |
| Inbound text / image / voice pipeline | existing | `app/whatsapp/services` | Media allowlist + stub LLM unless Gemini wired |
| Stub brain (`process_message`) | existing | `app/whatsapp/brain.py` | Product extension point |
| Soft outbound retry + error classify | existing | `app/whatsapp/services` | Transient Meta codes only; no durable queue |
| Template send helper | existing | `app/whatsapp/services/templates.py` | Approved template name + params |
| Service window helpers | existing | `app/whatsapp/services/service_window.py` | In-memory 24h window |
| Callback + flow registries | existing | `app/whatsapp/services` | Sample `help:` + generic contact flow |
| Status + local test routes | existing | `app/whatsapp` | `test-agent` / `test-message` local/staging only |

## Out Of Scope (Mobile App)

| Feature | Status | Notes |
| ------- | ------ | ----- |
| Apple / Google Sign-In | excluded | Use email/OTP auth; WhatsApp is the messaging channel |
| Expo push / native device push | excluded | In-app notifications + SSE only |
| RevenueCat / store billing | excluded | Add in a mobile fork if needed |

## MVP Acceptance Criteria (Starter)

- Fresh clone boots locally with `.env.sample` and passes `GET /api/v1/health`.
- Register → verify OTP → login → current-user flow works.
- Default customer receives `notifications.read` and `notifications.manage`.
- Admin provisioned via `create_admin.py` can access `/access/*` management routes after setup.
- `docs/API_CONTRACT.md`, `docs/DATABASE_SPEC.md`, and live routers agree.
- Optional integration env vars unset do not prevent startup.
- With WhatsApp disabled, import and boot succeed; with WhatsApp enabled + secrets, webhook attaches.
