# Accounts Client Handoff

Base path: `/api/v1/auth`

## Register

`POST /register`

Public. Body:

```json
{
  "first_name": "Ada",
  "last_name": "Lovelace",
  "phone_number": "+15550101010",
  "email": "ada@example.com",
  "password": "Password123!",
  "state": "Lagos"
}
```

Returns `201` when created. If the email already exists, clients receive `400`.

## Verify Account OTP (auto-login)

`POST /verify-otp`

Public. Body:

```json
{ "email": "ada@example.com", "otp_code": "123456" }
```

Returns `200`, activates the account, and returns **access + refresh tokens**
(same shape as a completed login). Clients should store tokens and skip a
separate login after first-time activation.

Invalid, expired, or over-attempted codes return `400`.

## Login

`POST /login`

Public. Body:

```json
{ "email": "ada@example.com", "password": "Password123!" }
```

### Default (email MFA off)

Returns tokens immediately:

```json
{
  "message": "Login Successful",
  "data": {
    "access": "<jwt>",
    "refresh": "<jwt>",
    "user": {
      "id": "ACC_...",
      "first_name": "Ada",
      "last_name": "Lovelace",
      "user_type": "customer",
      "email": "ada@example.com",
      "status": "active"
    }
  }
}
```

### When `email_login_mfa_enabled` is true

Returns **no tokens** — only a pending flag — and emails a sign-in OTP:

```json
{
  "message": "If the credentials are correct, a sign-in verification code has been sent.",
  "data": {
    "login_pending": true,
    "email": "ada@example.com"
  }
}
```

Then call `POST /verify-login-otp`.

Wrong password returns `401`. Inactive (unverified) accounts return `403` — use
`/verify-otp` instead.

## Verify Login OTP (optional email MFA step 2)

`POST /verify-login-otp`

Public. Body:

```json
{ "email": "ada@example.com", "otp_code": "123456" }
```

Returns the same token envelope as a successful login.

**Client flow when MFA is on:** `POST /login` → enter email OTP →
`POST /verify-login-otp` → store tokens.

## Preferences

`GET/PATCH /preferences` (bearer). Fields:

- `push_enabled`
- `email_notifications_enabled`
- `marketing_email_enabled`
- `email_login_mfa_enabled` — when `true`, password login requires the email OTP step

## Account deletion

`DELETE /account` requires
`{"confirm":true,"confirmation_phrase":"DELETE MY ACCOUNT"}`.

Use `Authorization: Bearer <access>` for protected endpoints.

For permissions and access-role management, see
[`app/access/handoff/CLIENT_HANDOFF.md`](../../access/handoff/CLIENT_HANDOFF.md)
(`GET /access/me/permissions`, `/access/*` admin routes).

## Current User

`GET /current-user` or `GET /me`

Requires active bearer token. Returns the current user profile. Missing/invalid
tokens return `401`; inactive accounts return `403`.

Profile payloads may include optional `username` and computed `display_name`
(override when set, otherwise first + last).

## Update profile

`PATCH /update-profile`

Partial body. Existing fields: `first_name`, `last_name`, `phone_number`,
`state`. Additive optional fields:

- `username` — unique `^[a-z0-9_]{3,32}$` (409 `username_taken` if taken)
- `display_name` — 1–80 chars; stored as display override

## Refresh Token

`POST /refresh-token`

Body:

```json
{ "refresh_token": "<refresh>" }
```

Returns a new access token. If the user logged out or changed password, old
refresh tokens return `401`.

## Logout

`POST /logout`

Requires bearer token. Revokes the current token version, so clients should
delete stored access and refresh tokens.

## Password Reset

`POST /forgot-password` sends a reset OTP. `POST /verify-reset-otp` validates it
and returns a short-lived reset bearer token. `POST /reset-password` requires
that bearer token and accepts:

```json
{ "new_password": "NewPassword123!", "confirm_password": "NewPassword123!" }
```

## OpenAPI

- App docs: `/docs` · `/openapi/app.json`
- Admin docs: `/docs/admin` · `/openapi/admin.json`
