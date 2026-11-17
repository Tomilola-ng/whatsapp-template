# Client handoff — Optional email MFA + dual OpenAPI

**Date:** 2026-08-29  
**Audience:** frontend / mobile integrators

## Register → OTP → session (unchanged, keep this)

1. `POST /api/v1/auth/register`
2. User receives activation OTP email
3. `POST /api/v1/auth/verify-otp` with `{ email, otp_code }`
4. Response includes **access + refresh tokens** — store them and enter the app. Do **not** force a second login.

## Login (default: no MFA)

`POST /api/v1/auth/login` with `{ email, password }` returns tokens immediately:

```json
{
  "message": "Login Successful",
  "data": {
    "access": "<jwt>",
    "refresh": "<jwt>",
    "user": { "...": "..." }
  }
}
```

## Login when the user enabled email MFA

Preferences field: `email_login_mfa_enabled` (default `false`).

Toggle via authenticated:

- `GET /api/v1/auth/preferences`
- `PATCH /api/v1/auth/preferences` with `{ "email_login_mfa_enabled": true }`

When enabled:

1. `POST /api/v1/auth/login` → **no tokens**:

```json
{
  "message": "If the credentials are correct, a sign-in verification code has been sent.",
  "data": {
    "login_pending": true,
    "email": "ada@example.com"
  }
}
```

2. User enters the email OTP
3. `POST /api/v1/auth/verify-login-otp` with `{ email, otp_code }` → tokens (same shape as a normal login)

**Client branch:** if `data.login_pending === true`, show OTP screen; otherwise store tokens.

## OpenAPI / Swagger

| Audience | Swagger | Schema |
| --- | --- | --- |
| App (product) | `/docs` or `/docs/app` | `/openapi/app.json` |
| Admin | `/docs/admin` | `/openapi/admin.json` |

Requires `OPENAPI_ENABLED=true` or `ENVIRONMENT=local`.
