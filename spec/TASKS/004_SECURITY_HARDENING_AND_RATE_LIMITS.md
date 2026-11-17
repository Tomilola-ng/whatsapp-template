# Task 004 - Security Hardening And Rate Limits

## Purpose

Harden secrets, rate limiting, OpenAPI exposure, and trusted-proxy behavior for production-ready starter deployments.

## Source Of Truth

`spec/AUTH_AND_PERMISSIONS.md`; `app/config/settings.py`; `main.py`; `.env.sample`; `docs/SETUP_GUIDE.md` and `docs/API_KEYS_GUIDE.md`.

## Depends On

001, 002, 003.

## Scope

- Add `JWT_SECRET_KEY` and `OTP_HMAC_SECRET` with production validation (32+ chars, no placeholders).
- Wire `slowapi` rate limits on login, register, OTP, refresh, contact, and other sensitive public routes.
- Disable `/docs` and `/openapi.json` outside `local` unless `OPENAPI_ENABLED=true`.
- Resolve client IP via `TRUSTED_PROXY_IPS` for rate limiting and audit metadata.
- Document `429` handling and per-process limit caveats.

## Out Of Scope

Redis-backed distributed rate limits (document as future scaling step), WAF rules, CAPTCHA.

## Backend Files To Create Or Update

`app/config/settings.py`, `main.py`, `app/base/rate_limit.py`, `app/base/client_ip.py`, `app/accounts/routes.py`, `app/contact/routes.py`, `pyproject.toml`, `.env.sample`, setup docs.

## Business Rules

- Staging/production startup fails on weak signing secrets.
- Local development may use placeholders with a startup warning.
- Rate limits apply per API process unless a shared backend is configured.

## Completion Checklist

- [ ] `JWT_SECRET_KEY` / `OTP_HMAC_SECRET` validated in staging/production.
- [ ] Rate limits applied to documented public endpoints.
- [ ] OpenAPI disabled by default in non-local environments.
- [ ] Docs describe admin provisioning without `make-admin` HTTP route.

## Schema Gap

None.
