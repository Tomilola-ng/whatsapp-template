# Deployment Readiness

Use this checklist before shipping a starter fork.

## Required

- PostgreSQL is provisioned and `uv run aerich upgrade` succeeds against a clean rehearsal database.
- `GET /api/v1/health` succeeds through the production proxy.
- `bash app/base/tests/run_all.sh .env.e2e` passes against a real server and database.
- `JWT_SECRET_KEY`, `OTP_HMAC_SECRET`, `API_AUTHORIZATION_TOKEN`, and `INTERNAL_JOB_TOKEN` are strong and distinct.
- `OPENAPI_ENABLED=false` unless public API documentation is intentional.
- `DEV_OUTBOX_ENABLED=false`; application validation refuses the dev outbox in staging/production.
- `RATE_LIMIT_STORAGE_URL` uses shared Redis-compatible storage when more than one application process is deployed.

## Optional features

- Configure R2 only when file uploads are enabled.
- Configure Resend only when outbound email is required.
- Configure WhatsApp (`WHATSAPP_ENABLED=true` and Meta Cloud API secrets) when the messaging channel is live. See `docs/WHATSAPP_INTEGRATION.md`.

## Intentionally not required for starter deploy

- Apple / Google Sign-In, RevenueCat, Expo push, or other mobile-app-only integrations.
- Store billing webhooks or device push token registration.

## Release evidence

Record the migration output, E2E output, health response, environment review,
rollback target, and responsible operator in the fork's release notes.
