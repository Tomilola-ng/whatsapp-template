# Starter Endpoint Checklist

- [x] `GET /api/v1/health` - public
- [x] `POST /api/v1/auth/register` - public
- [x] `POST /api/v1/auth/login` - public (tokens, or `login_pending` when email MFA on)
- [x] `POST /api/v1/auth/verify-login-otp` - public (optional email MFA step 2)
- [x] `POST /api/v1/auth/logout` - bearer token
- [x] `GET /api/v1/auth/current-user` - active bearer token
- [x] `GET /api/v1/auth/me` - active bearer token (alias)
- [x] `GET /api/v1/auth/preferences` - active bearer token
- [x] `PATCH /api/v1/auth/preferences` - active bearer token
- [x] `PATCH /api/v1/auth/update-profile` - active bearer token
- [x] `PATCH /api/v1/auth/update-user-image` - active bearer token
- [x] `POST /api/v1/auth/send-otp` - public
- [x] `POST /api/v1/auth/verify-otp` - public
- [x] `POST /api/v1/auth/forgot-password` - public
- [x] `POST /api/v1/auth/verify-reset-otp` - public
- [x] `POST /api/v1/auth/reset-password` - password reset bearer token
- [x] `POST /api/v1/auth/change-password` - active bearer token
- [x] `POST /api/v1/auth/refresh-token` - refresh token body
- [x] `POST /api/v1/auth/exchange-setup-code` - public setup code exchange
- [x] `GET /api/v1/access/me/permissions` - bearer token; returns JWT permission snapshot
- [x] `GET /api/v1/access/permissions` - active bearer + `access.read`
- [x] `GET /api/v1/access/roles` - active bearer + `access.read`
- [x] `POST /api/v1/access/roles` - active bearer + `access.manage`
- [x] `PATCH /api/v1/access/roles/{role_id}` - active bearer + `access.manage`
- [x] `DELETE /api/v1/access/roles/{role_id}` - active bearer + `access.manage`
- [x] `GET /api/v1/access/accounts/{account_id}/roles` - active bearer + `accounts.read`
- [x] `PUT /api/v1/access/accounts/{account_id}/roles` - active bearer + `accounts.assign_roles`
- [x] `PUT /api/v1/access/accounts/{account_id}/permissions` - active bearer + `accounts.assign_roles`
- [x] `POST /api/v1/base/files` - active bearer + `files.create`
- [x] `GET /api/v1/base/files` - local only; active bearer + `files.read`
- [x] `GET /api/v1/notifications/` - active bearer + `notifications.read`
- [x] `PATCH /api/v1/notifications/{notification_id}/read` - active bearer + `notifications.read` + owner
- [x] `POST /api/v1/contact/` - public
- [x] `GET /api/v1/dev/outbox/latest-otp` - local dev outbox only
- [x] `POST /api/v1/internal/jobs/run-maintenance` - internal token outside local dev

See [`app/access/handoff/CLIENT_HANDOFF.md`](../../access/handoff/CLIENT_HANDOFF.md) for access-control request/response details.
