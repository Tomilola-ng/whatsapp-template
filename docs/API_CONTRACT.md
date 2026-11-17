# WhatsApp FastAPI 2026 Template — API Contract

## Status

This contract describes the **currently registered** starter API surface. Implementations must keep routers, services, schemas, models, DBML, and this document aligned when behavior changes.

## Conventions

- Base prefix: `/api/v1`.
- Unless marked public, endpoints require an active authenticated user with `Authorization: Bearer <access_token>`.
- Many protected routes also require a permission codename from JWT claims; `require_permission` validates session version fields against the database.
- Success envelopes: newer helpers return `{ "success": boolean, "message": string, "data": ... }`; some legacy starter endpoints return `{ "message": string, "data": ... }`.
- Paginated lists use `page` and `page_size`, returning `{ "items": [...], "meta": { ... } }`.
- Application-owned record IDs are prefixed strings (for example `ACC_…`). File asset IDs are integers.
- Account responses expose `user_type` (`customer`, `provider`, `admin`), not `role`.

## Error Response Format

FastAPI validation errors use the default structured `422` response. Application errors commonly return:

```json
{ "detail": "Human-readable error" }
```

Common statuses:

| Status | Meaning |
| ------ | ------- |
| `400` | Invalid state, bad OTP, validation conflict |
| `401` | Missing, invalid, expired, or revoked credential |
| `403` | Authenticated but inactive, missing permission, or policy violation |
| `404` | Resource not found |
| `409` | Valid-state conflict (duplicate, stale transition) |
| `422` | Request validation failed |
| `429` | Rate limit exceeded — honor `Retry-After` when present |

See `spec/AUTH_AND_PERMISSIONS.md` for auth and permission failure semantics.

## Health

| Method | Path | Auth | Notes |
| ------ | ---- | ---- | ----- |
| GET | `/health` | Public | Liveness check |

## Auth

| Method | Path | Auth | Permission | Notes |
| ------ | ---- | ---- | ---------- | ----- |
| POST | `/auth/register` | Public | — | Rate limited |
| POST | `/auth/login` | Public | — | Active accounts only |
| POST | `/auth/logout` | Bearer | — | Revokes token version |
| GET | `/auth/current-user` | Active | — | Profile |
| GET | `/auth/me` | Active | — | Alias of current-user |
| POST | `/auth/refresh-token` | Refresh body | — | No Authorization header |
| POST | `/auth/send-otp` | Public | — | Account verification |
| POST | `/auth/verify-otp` | Public | — | Activates; returns `access`, `refresh`, `user` |
| POST | `/auth/forgot-password` | Public | — | Sends reset OTP |
| POST | `/auth/verify-reset-otp` | Public | — | Returns reset JWT |
| POST | `/auth/reset-password` | Reset JWT | — | Password-reset scope only |
| POST | `/auth/change-password` | Active | — | Revokes other sessions |
| POST | `/auth/exchange-setup-code` | Public | — | Admin invite flow |
| PATCH | `/auth/update-profile` | Active | — | Partial update (`first_name`, `last_name`, `phone_number`, `state`, optional `display_name`, `username`) |
| PATCH | `/auth/update-user-image` | Active | — | Multipart image |
| GET/PATCH | `/auth/preferences` | Active | — | Generic notification preferences |
| DELETE | `/auth/account` | Active | — | Explicit phrase confirmation |

Admin promotion is handled by `scripts/create_admin.py` only.

## Access Control

| Method | Path | Auth | Permission | Notes |
| ------ | ---- | ---- | ---------- | ----- |
| GET | `/access/me/permissions` | Bearer | — | `{ user_type, permissions }` from JWT |
| GET | `/access/permissions` | Active | `access.read` | All registered codenames |
| GET | `/access/roles` | Active | `access.read` | List access roles |
| POST | `/access/roles` | Active | `access.manage` | Create custom role |
| PATCH | `/access/roles/{role_id}` | Active | `access.manage` | Update role |
| DELETE | `/access/roles/{role_id}` | Active | `access.manage` | Blocked for system roles |
| GET | `/access/accounts/{id}/roles` | Active | `accounts.read` | Role slugs + effective perms |
| PUT | `/access/accounts/{id}/roles` | Active | `accounts.assign_roles` | Replace assignments |
| PUT | `/access/accounts/{id}/permissions` | Active | `accounts.assign_roles` | Replace direct grants |

Assignment policy: users cannot modify their own roles or grants; only `*` holders can assign `super_admin`; assigners cannot grant permissions they do not hold.

## Files

| Method | Path | Auth | Permission | Notes |
| ------ | ---- | ---- | ---------- | ----- |
| POST | `/base/files` | Active | `files.create` | Multipart upload to R2 |
| GET | `/base/files` | Active; local only | `files.read` | Paginated list |

## Notifications

| Method | Path | Auth | Permission | Notes |
| ------ | ---- | ---- | ---------- | ----- |
| GET | `/notifications/` | Active | `notifications.read` | Own notifications only |
| PATCH | `/notifications/{id}/read` | Active | `notifications.read` | Owner check |
| GET | `/notifications/unread-count` | Active | — | Own unread count |
| POST | `/notifications/mark-all-read` | Active | — | Idempotent bulk mark |
| GET | `/notifications/stream` | Active | — | SSE stream |
| POST | `/admin/notifications/broadcast` | Active | `notifications.broadcast` | Staff broadcast |

## Platform Logs

| Method | Path | Auth | Permission | Notes |
| ------ | ---- | ---- | ---------- | ----- |
| GET | `/admin/audit-logs` | Active | `audit_logs.read` | Paginated audit trail |
| POST | `/client-errors/` | Optional | — | Redacted client report |
| GET | `/client-errors/` | Environment-dependent | `client_errors.read` in production | Open local/staging |

## Contact

| Method | Path | Auth | Permission | Notes |
| ------ | ---- | ---- | ---------- | ----- |
| POST | `/contact/` | Public | — | Rate limited |

## WhatsApp

Optional messaging channel (`WHATSAPP_ENABLED=true`). Meta webhook is attached at startup when configured. See `docs/WHATSAPP_INTEGRATION.md`.

| Method | Path | Auth | Notes |
| ------ | ---- | ---- | ----- |
| GET | `/whatsapp/status` | Public | Non-secret wiring check |
| POST | `/whatsapp/test-message` | Public | Local/staging only; outbound test send |
| POST | `/whatsapp/test-agent` | Public | Local/staging only; run inbound pipeline without Meta webhook |

## App Updates And Legal

| Method | Path | Auth | Permission | Notes |
| ------ | ---- | ---- | ---------- | ----- |
| GET | `/app/update-policy` | Public | — | Query: `platform`, `version`, `build`; rate limited |
| GET | `/app/legal` | Public | — | `terms_url`, `privacy_url` from env |
| GET | `/app/events/stream` | Public | — | SSE `app_update` events |
| POST | `/admin/app/releases` | Active | `app_releases.manage` | Create release (envelope) |
| GET | `/admin/app/releases` | Active | `app_releases.manage` | List releases; `page`, `page_size`, `platform`, `is_active`, `published_at__isnull`, `ordering` |
| GET | `/admin/app/releases/{id}` | Active | `app_releases.manage` | Retrieve release |
| PATCH | `/admin/app/releases/{id}` | Active | `app_releases.manage` | Patch release |

## Dev Outbox (local only)

Mounted when `ENVIRONMENT=local` and `DEV_OUTBOX_ENABLED=true`.

| Method | Path | Auth | Notes |
| ------ | ---- | ---- | ----- |
| GET | `/dev/outbox/` | Public | Recent captured sends |
| GET | `/dev/outbox/latest-otp` | Public | `recipient`, optional `purpose` |

## Internal Jobs

| Method | Path | Auth | Notes |
| ------ | ---- | ---- | ----- |
| POST | `/internal/jobs/run-maintenance` | `X-Internal-Token` | Local may omit token when unset |

## Registered Permission Codenames

Synced from `app/access/permission_registry.py`:

| Module | Actions | Wildcard |
| ------ | ------- | -------- |
| `access` | `read`, `manage` | `access.*` |
| `accounts` | `create`, `read`, `update`, `delete`, `assign_roles` | `accounts.*` |
| `files` | `create`, `read`, `update`, `delete` | `files.*` |
| `notifications` | `read`, `manage`, `broadcast` | `notifications.*` |
| `audit_logs` | `read` | `audit_logs.*` |
| `client_errors` | `read` | `client_errors.*` |
| `contact` | `read`, `manage` | `contact.*` |
| `app_releases` | `manage` | `app_releases.*` |
| global | — | `*` |

## Out Of Scope

Payment collection/entitlement logic, marketplace modules, social graphs, and
product-specific admin dashboards are intentionally excluded.

Mobile-app-only surfaces are also excluded from this WhatsApp starter: Apple/Google
Sign-In, RevenueCat (or other store billing webhooks), and Expo/native device push
token routes. Use WhatsApp for outbound messaging; use in-app notifications (SSE)
for authenticated web/dashboard clients.

## Related Docs

- Client integration: `app/<module>/handoff/CLIENT_HANDOFF.md`
- Auth deep dive: `spec/AUTH_AND_PERMISSIONS.md`
- Agent reconciliation: `spec/API.md` (kept in sync with this contract)
