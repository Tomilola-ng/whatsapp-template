# Shell E2E Tests

These tests exercise the running API over HTTP with `curl` and `jq`. They do not use pytest, TestClient, or in-process mocks.

Shell/curl E2E is the source of truth for HTTP behavior. Unit tests are limited
to deterministic helpers and wiring checks. The current allowlist is:

- `app.audit.tests.unit.test_audit_redaction`
- `app.integration.tests.unit.test_dev_outbox_otp`
- `app.accounts.tests.unit.test_profile_validation`
- `app.app_releases.tests.unit.test_update_policy`
- `app.base.tests.unit.test_views` (class-based view wiring + behaviour, in-memory SQLite)

## Quick Start

```bash
cp .env.e2e.example .env.e2e
docker compose up -d
createdb fastapi_base_template_e2e
uv run aerich upgrade
bash app/base/tests/run_all.sh .env.e2e
```

Runtime state is written to `app/base/tests/.session.env` and `app/base/tests/api-test.log`; both are ignored.

## Safety

- `DATABASE_URL` must be PostgreSQL.
- `ENVIRONMENT=staging` and `ENVIRONMENT=production` are refused.
- OTPs are fetched only from `/api/v1/dev/outbox/latest-otp`.
- The default `.env.e2e.example` disables rate limits for stable auth tests. Set `RATE_LIMIT_ENABLED=true` and `E2E_RATE_LIMIT_PROBE=true` for a focused 429 probe.
