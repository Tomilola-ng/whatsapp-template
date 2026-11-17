# API Keys Guide

Generate signing and job secrets with:

```bash
uv run python scripts/generate_secrets.py --write .env
```

This template supports several third-party services. Auth and database setup are required for first boot; signing secrets are required in staging and production.

## Required signing secrets

| Variable | Purpose |
| -------- | ------- |
| `JWT_SECRET_KEY` | Signs access, refresh, and password-reset JWTs |
| `OTP_HMAC_SECRET` | HMAC key for OTP and admin setup codes at rest |

Generate values (48+ bytes recommended):

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Set **different** values for each variable in staging and production.

`API_AUTHORIZATION_TOKEN` is a deprecated alias used only when `JWT_SECRET_KEY` or `OTP_HMAC_SECRET` are unset. Do not rely on it for new deployments.

Startup fails in `staging` / `production` when signing secrets are missing, shorter than 32 characters, or match known placeholders (`change-me`, `change-me-in-real-projects`).

## Environment and security

| Variable | Notes |
| -------- | ----- |
| `ENVIRONMENT` | Use `local` for development, `production` in deployed environments |
| `OPENAPI_ENABLED` | Set `true` to expose `/docs` + `/docs/admin` outside `local` (not recommended publicly) |
| `CLIENT_APP_URL` | Frontend/app base URL used in email CTAs (falls back to `APP_BASE_URL`) |
| `STRUCTURED_LOGGING_ENABLED` | JSON request logs with `X-Request-ID` (default true) |
| `TRUSTED_PROXY_IPS` | Comma-separated IPs of reverse proxies allowed to set `X-Forwarded-For` |
| `PASSWORD_SETUP_URL` | Frontend URL for admin password setup (`?code=` query param) |
| `ADMIN_PASSWORD_SETUP_CODE_EXPIRE_HOURS` | Opaque setup code lifetime (default 2 hours) |
| `DEV_OUTBOX_ENABLED` | Local-only email/SMS capture for E2E tests; refused in staging/production |
| `INTERNAL_JOB_TOKEN` | Shared token expected in `X-Internal-Token` for internal job routes outside local development |

## Rate limiting

Tune public-endpoint limits via `.env`:

| Variable | Default | Typical use |
| -------- | ------- | ----------- |
| `RATE_LIMIT_LOGIN` | `10/minute` | Login |
| `RATE_LIMIT_REGISTER` | `5/minute` | Registration |
| `RATE_LIMIT_OTP_SEND` | `3/minute` | Send OTP / forgot password |
| `RATE_LIMIT_OTP_VERIFY` | `10/minute` | Verify OTP / exchange setup code |
| `RATE_LIMIT_REFRESH` | `30/minute` | Refresh token |
| `RATE_LIMIT_CONTACT` | `3/minute` | Contact form |
| `RATE_LIMIT_ACCESS` | `60/minute` | Access control admin routes |
| `OTP_RESEND_COOLDOWN_SECONDS` | `60` | Minimum gap between OTP sends per account |
| `RATE_LIMIT_ENABLED` | `true` | Master switch, usually false only in deterministic E2E runs |
| `RATE_LIMIT_STORAGE_URL` | empty | Optional shared backend URL such as Redis |
| `RATE_LIMIT_DEFAULT` | `100/minute` | Default per-client limit |

Limits are per API process unless `RATE_LIMIT_STORAGE_URL` points to a shared backend.

## Email branding

| Variable | Purpose |
| -------- | ------- |
| `BRAND_NAME` | Optional email/header brand override |
| `BRAND_LOGO_URL` | Optional logo displayed in transactional emails |
| `BRAND_PRIMARY_COLOR` | Optional email primary button color (hex) |
| `BRAND_DARK_COLOR` | Optional email header/dark color (hex) |
| `BRAND_ON_PRIMARY_COLOR` | Optional text color on primary buttons (hex) |
| `TERMS_URL` | Public terms URL returned by `GET /app/legal` |
| `PRIVACY_URL` | Public privacy URL returned by `GET /app/legal` |
| `SUPPORT_EMAIL` | Optional support contact shown in email footer |

## Integration status

- Available now in code: Resend, R2, Paystack helper client, Prembly helper client
- Scaffolded but not fully wired into default routes: Paystack, Prembly
- Future extension points: webhooks, payouts, identity-verification workflows

## Required for first boot

### `DATABASE_URL`

- Purpose: database connection for Tortoise ORM
- Required: yes
- Default in sample: `sqlite://db.sqlite3`
- Production recommendation: PostgreSQL DSN

## Email: Resend

### `RESEND_API_KEY`

- Purpose: sends account emails and contact form notifications
- Required: only if you want working outbound email
- Where to get it: Resend dashboard

### `EMAIL_SENDER`

- Purpose: from-address used by email helpers
- Required: yes when Resend is enabled

### `CONTACT_RECIPIENT_EMAIL`

- Purpose: inbox for `/api/v1/contact/`
- Required: yes when the public contact endpoint should deliver mail

## File storage: Cloudflare R2

### `R2_ENDPOINT_URL`
### `R2_ACCESS_KEY_ID`
### `R2_SECRET_ACCESS_KEY`
### `R2_BUCKET_NAME`
### `R2_PUBLIC_URL`

- Purpose: file upload and presigned URL generation for `app/base`
- Required: all required together when you use `/api/v1/base/files`
- Local testing: leave empty until you need uploads

## Payments: Paystack

### `PAYSTACK_SECRET_KEY`
### `PAYSTACK_PUBLIC_KEY`
### `PAYSTACK_BASE_URL`
### `PAYSTACK_CALLBACK_URL`
### `PAYSTACK_SUBACCOUNT_PERCENTAGE_CHARGE`
### `PAYSTACK_BANKS_JSON_PATH`

- Purpose: server-side Paystack API calls and future payment modules
- Required: only when enabling payment features

## Identity verification: Prembly

### `PREMBLY_SECRET_KEY`
### `PREMBLY_PUBLIC_KEY`
### `PREMBLY_BASE_URL`
### `PREMBLY_NIN_PATH`
### `PREMBLY_TIMEOUT_SECONDS`

- Purpose: server-side identity verification requests
- Required: only when enabling identity verification features

## Webhook and callback values to prepare

- Paystack callback URL: set `PAYSTACK_CALLBACK_URL` before you add payment routes
- API base URL: keep a stable base domain ready before enabling third-party callback workflows

## WhatsApp Cloud API (PyWa)

Leave `WHATSAPP_ENABLED=false` for first boot. When `true`, these are required:

| Variable | Purpose |
| -------- | ------- |
| `WHATSAPP_PHONE_NUMBER_ID` | Meta Cloud phone number id |
| `WHATSAPP_BUSINESS_ACCOUNT_ID` | WABA id |
| `WHATSAPP_ACCESS_TOKEN` | Permanent / system-user token |
| `WHATSAPP_APP_ID` | Meta app id |
| `WHATSAPP_VERIFY_TOKEN` | Webhook verify token you choose |
| `WHATSAPP_APP_SECRET` | Meta app secret (signature validation) |

Optional:

| Variable | Purpose |
| -------- | ------- |
| `WHATSAPP_CALLBACK_URL` | Public HTTPS origin (not the full webhook path) |
| `WHATSAPP_WEBHOOK_ENDPOINT` | Default `/api/v1/webhooks/whatsapp` |
| `WHATSAPP_AUTO_REGISTER_CALLBACK` | Default `false` — prefer Meta UI on PaaS |
| `WHATSAPP_DISPLAY_NUMBER` | Human-readable number for docs / status |
| `WHATSAPP_MEDIA_MAX_BYTES` | Inbound media size cap (default 25MB) |
| `WHATSAPP_MEDIA_FETCH_ALLOWLIST_HOSTS` | Comma-separated CDN hosts for media download |
| `WHATSAPP_MEDIA_ALLOWED_MIME_TYPES` | Comma-separated MIME allowlist |
| `WHATSAPP_SERVICE_WINDOW_HOURS` | Free-form reply window helper (default 24) |
| `WHATSAPP_OUTBOUND_MAX_ATTEMPTS` | Soft in-process retry attempts (default 3) |
| `GEMINI_ENABLED` / `GEMINI_API_KEY` | Optional media describe/transcribe (stubbed until wired) |

See [WHATSAPP_INTEGRATION.md](WHATSAPP_INTEGRATION.md) and [WHATSAPP_THREAT_MODEL.md](WHATSAPP_THREAT_MODEL.md).
