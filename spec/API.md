# Starter API Specification

The 2026-08-05 generic backport added token-returning OTP verification,
preferences/deletion, audit and client-error routes, notification
unread/bulk/SSE routes, and staff broadcast. The 2026-09-09 WhatsApp starter
strip removed Google/Apple SSO, RevenueCat, and device push token routes.
WhatsApp (Meta Cloud API) is the supported external messaging channel.

## Conventions

- Base prefix: `/api/v1`.
- Unless marked public, endpoints require an active authenticated user with `Authorization: Bearer <access_token>`.
- Many protected routes also require a permission codename from JWT claims; `require_permission` validates session version fields against the database.
- New envelope helpers return `{ "success": boolean, "message": string, "data": ... }`; some legacy starter endpoints still return `{ "message": string, "data": ... }`.
- Validation errors use FastAPI's structured error response.
- Paginated list endpoints use `page` and `page_size`, returning `{items, meta}` through the shared pagination helper.
- Application-owned record IDs are prefixed strings (for example `ACC_…`). File asset IDs remain integers.
- Account responses expose `user_type` (`customer`, `provider`, `admin`), not `role`.

## Health

| Group  | Method | Path      | Auth | Request | Response        | Notes  | Task |
| ------ | ------ | --------- | ---- | ------- | --------------- | ------ | ---- |
| Health | GET    | `/health` | No   | None    | Health message  | Public | 007  |

## Auth

| Group | Method | Path                    | Auth                 | Request summary              | Response summary                    | Permission notes              | Task |
| ----- | ------ | ----------------------- | -------------------- | ---------------------------- | ----------------------------------- | ----------------------------- | ---- |
| Auth  | POST   | `/auth/register`        | No                   | Name, email, password, optional phone/state | Account data; verification required | Public; rate limited          | 001  |
| Auth  | POST   | `/auth/login`           | No                   | Email/password               | Access, refresh, user               | Active account only           | 001  |
| Auth  | POST   | `/auth/logout`          | Yes                  | None                         | Message                             | Revokes account tokens        | 001  |
| Auth  | GET    | `/auth/current-user`    | Yes                  | None                         | Account/profile data                | Active user                   | 001  |
| Auth  | GET    | `/auth/me`              | Yes                  | None                         | Same as current-user                | Active user alias             | 001  |
| Auth  | POST   | `/auth/refresh-token`   | No credential header | Refresh token JSON           | New access token                    | Validate refresh scope/version | 001 |
| Auth  | POST   | `/auth/send-otp`        | No                   | Email                        | Message                             | Account verification purpose  | 001  |
| Auth  | POST   | `/auth/verify-otp`      | No                   | Email/OTP                    | Message                             | Activates account             | 001  |
| Auth  | POST   | `/auth/forgot-password` | No                   | Email                        | Message                             | Optional flow                 | 001  |
| Auth  | POST   | `/auth/verify-reset-otp`| No                   | Email/OTP                    | Short-lived reset token             | Password-reset scope only     | 001  |
| Auth  | POST   | `/auth/reset-password`  | Reset JWT            | New/confirm password         | Message                             | Password-reset scope only     | 001  |
| Auth  | POST   | `/auth/change-password` | Yes                  | Old/new/confirm password     | Message                             | Revokes other sessions        | 001  |
| Auth  | POST   | `/auth/exchange-setup-code` | No               | Email + opaque setup code    | Short-lived password-setup JWT      | Admin invite flow             | 005  |
| Auth  | PATCH  | `/auth/update-profile`  | Yes                  | Partial profile fields       | Updated account                     | Active current user           | 001  |
| Auth  | PATCH  | `/auth/update-user-image` | Yes                | Multipart image              | Updated account                     | Current user only             | 002  |
| Auth  | GET/PATCH | `/auth/preferences`  | Yes                  | Notification preference fields | Preference snapshot               | In-app/email/marketing prefs  | 001  |
| Auth  | DELETE | `/auth/account`         | Yes                  | Confirmation phrase          | Deletion result                     | Self-service purge            | 001  |

Admin promotion is handled by `scripts/create_admin.py` only; there is no HTTP `make-admin` route.

## Access control

| Group  | Method | Path                                | Auth | Permission              | Notes                          | Task |
| ------ | ------ | ----------------------------------- | ---- | ----------------------- | ------------------------------ | ---- |
| Access | GET    | `/access/me/permissions`            | Yes  | None (JWT snapshot)     | `{ user_type, permissions }`   | 008  |
| Access | GET    | `/access/permissions`               | Yes  | `access.read`           | List permission codenames      | 008  |
| Access | GET    | `/access/roles`                     | Yes  | `access.read`           | List access roles              | 008  |
| Access | POST   | `/access/roles`                     | Yes  | `access.manage`         | Create custom role             | 008  |
| Access | PATCH  | `/access/roles/{role_id}`           | Yes  | `access.manage`         | Update role permissions        | 008  |
| Access | DELETE | `/access/roles/{role_id}`           | Yes  | `access.manage`         | Blocked for system roles       | 008  |
| Access | GET    | `/access/accounts/{id}/roles`       | Yes  | `accounts.read`         | Role slugs + effective perms   | 008  |
| Access | PUT    | `/access/accounts/{id}/roles`       | Yes  | `accounts.assign_roles` | Replace role assignments       | 008  |
| Access | PUT    | `/access/accounts/{id}/permissions` | Yes  | `accounts.assign_roles` | Replace direct grants          | 008  |

## Files

| Group | Method | Path           | Auth   | Request summary        | Response summary              | Permission notes | Task |
| ----- | ------ | -------------- | ------ | ---------------------- | ----------------------------- | ---------------- | ---- |
| Files | POST   | `/base/files`  | Yes    | Multipart upload       | File metadata and presigned URL | `files.create` | 008  |
| Files | GET    | `/base/files`  | Yes; local only  | `page`, `page_size`    | Paginated file assets | `files.read` | 008  |

## Notifications

| Group         | Method  | Path                                    | Auth | Request summary                    | Response summary           | Permission notes     | Task |
| ------------- | ------- | --------------------------------------- | ---- | ---------------------------------- | -------------------------- | -------------------- | ---- |
| Notifications | GET     | `/notifications/`                       | Yes  | `page`, `page_size`, `unread_only` | `{items, meta}`            | `notifications.read` | 008 |
| Notifications | PATCH   | `/notifications/{notification_id}/read` | Yes  | None                               | Updated notification       | `notifications.read` + owner | 008 |
| Notifications | GET     | `/notifications/unread-count`           | Yes  | None                               | Unread count               | Own notifications    | 008 |
| Notifications | POST    | `/notifications/mark-all-read`          | Yes  | None                               | Bulk mark result           | Own notifications    | 008 |
| Notifications | GET     | `/notifications/stream`                 | Yes  | None (SSE)                         | Live notification events   | Own notifications    | 008 |
| Notifications | POST    | `/admin/notifications/broadcast`        | Yes  | Broadcast payload                  | Created notifications      | `notifications.broadcast` | 008 |

## WhatsApp

| Group    | Method | Path                      | Auth | Request summary     | Response summary      | Notes                              | Task |
| -------- | ------ | ------------------------- | ---- | ------------------- | --------------------- | ---------------------------------- | ---- |
| WhatsApp | GET    | `/whatsapp/status`        | No   | None                | Wiring check          | Public; no secrets                 | —    |
| WhatsApp | POST   | `/whatsapp/test-message`  | No   | MSISDN + text       | Provider message id   | Local/staging only                 | —    |
| WhatsApp | POST   | `/whatsapp/test-agent`    | No   | MSISDN + text       | Pipeline reply        | Local/staging only                 | —    |

Meta webhook attaches at startup when `WHATSAPP_ENABLED=true`. See `docs/WHATSAPP_INTEGRATION.md`.

## Contact

| Group   | Method | Path        | Auth | Request summary     | Response summary | Permission notes | Task |
| ------- | ------ | ----------- | ---- | ------------------- | ---------------- | ---------------- | ---- |
| Contact | POST   | `/contact/` | No   | Name, email, message | Message          | Public; rate limited | 003 |

## Dev Outbox

| Group      | Method | Path                         | Auth | Request summary                 | Response summary       | Permission notes                          | Task |
| ---------- | ------ | ---------------------------- | ---- | ------------------------------- | ---------------------- | ----------------------------------------- | ---- |
| Dev outbox | GET    | `/dev/outbox/`               | No   | Optional `limit`                | Recent captured sends  | Local + `DEV_OUTBOX_ENABLED=true` only    | 007  |
| Dev outbox | GET    | `/dev/outbox/latest-otp`     | No   | `recipient`, optional `purpose` | Latest captured OTP    | Local + `DEV_OUTBOX_ENABLED=true` only    | 007  |

## Internal Jobs

| Group | Method | Path                             | Auth           | Request summary | Response summary      | Permission notes                                    | Task |
| ----- | ------ | -------------------------------- | -------------- | --------------- | --------------------- | --------------------------------------------------- | ---- |
| Jobs  | POST   | `/internal/jobs/run-maintenance` | Internal token | None            | Maintenance counters  | `X-Internal-Token`; local bypass only when unset    | 007  |

## Out of scope for the starter

Payment flows, marketplace modules, social graphs, and product-specific admin dashboards are intentionally excluded. Mobile-app-only surfaces — Apple/Google Sign-In, RevenueCat (or other store billing), and Expo/native device push token routes — are also excluded. Use WhatsApp for outbound messaging and in-app notifications (SSE) for authenticated clients. Add mobile integrations in your fork with new spec tasks and DBML updates.
