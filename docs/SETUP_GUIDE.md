# Setup Guide

Generate `JWT_SECRET_KEY`, `OTP_HMAC_SECRET`, `API_AUTHORIZATION_TOKEN`, and
`INTERNAL_JOB_TOKEN` in one step:

```bash
uv run python scripts/generate_secrets.py --write .env
```

This guide is the supported first-run path for the base template.

## Prerequisites

- Python `3.13+`
- `uv`
- a writable local workspace
- optional: PostgreSQL if you do not want to use the default sqlite starter DSN

## Local development

1. Copy `.env.sample` to `.env`.
2. Keep `ENVIRONMENT=local` for SQLite first boot and automatic schema generation.
3. Install dependencies: `uv sync`.
4. Initialize or upgrade the database (see [Database](#database) below).
5. Start the API: `uv run fastapi dev main.py`.
6. Open `GET http://localhost:8000/api/v1/health`.

Local development may use placeholder signing secrets; the app logs a warning at startup when `JWT_SECRET_KEY` or `OTP_HMAC_SECRET` are weak.

## Production deployment

1. Set `ENVIRONMENT=production` (or `staging`).
2. Set strong `JWT_SECRET_KEY` and `OTP_HMAC_SECRET` (32+ characters each). See [API_KEYS_GUIDE.md](API_KEYS_GUIDE.md).
3. Configure `TRUSTED_PROXY_IPS` when running behind a load balancer or ingress.
4. Run database migrations after pulling schema changes: `uv run aerich upgrade` or `uv run python scripts/migrate.py`.
5. Confirm `/docs` and `/docs/admin` return 404 unless `OPENAPI_ENABLED=true`
   (or `ENVIRONMENT=local`). Schemas: `/openapi/app.json`, `/openapi/admin.json`.
6. Provision admins with `scripts/create_admin.py` — there is no HTTP `make-admin` route.

Startup fails in `staging` / `production` when signing secrets are missing, shorter than 32 characters, or match known placeholders.

## Rate limiting

The API uses `slowapi`. In-memory storage works for local development and single-process deployments. Multi-instance deployments should set `RATE_LIMIT_STORAGE_URL` to a shared backend before scaling horizontally.

Tune limits via `RATE_LIMIT_*` variables in `.env`. Clients should handle HTTP `429` responses and `Retry-After` headers.

## Dev outbox and E2E

For black-box HTTP smoke tests:

```powershell
Copy-Item .env.e2e.example .env.e2e
docker compose up -d
createdb fastapi_base_template_e2e
uv run aerich upgrade
bash app/base/tests/run_all.sh .env.e2e
```

`DEV_OUTBOX_ENABLED=true` captures local email/SMS sends and exposes `/api/v1/dev/outbox/latest-otp`. Startup refuses this flag in staging and production.

## Admin password setup

1. Run `uv run python scripts/create_admin.py --email admin@example.com`.
2. The invite email contains `PASSWORD_SETUP_URL?code=<opaque>`.
3. The web client calls `POST /api/v1/auth/exchange-setup-code` with `{ "email", "code" }`.
4. The client then calls `POST /api/v1/auth/reset-password` with `Authorization: Bearer <reset_token>`.

On first boot with `ENVIRONMENT=local`, Tortoise can auto-create tables including RBAC models. Default access roles are seeded at startup. After adding new permission codenames in code, run `uv run python scripts/sync_permissions.py`.

## Install Python

Recommended:

1. Install Python `3.13+` from [python.org](https://www.python.org/downloads/).
2. Confirm it is available:

```powershell
python --version
```

## Install uv

Recommended:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Confirm:

```powershell
uv --version
```

## Create the Environment File

```powershell
Copy-Item .env.sample .env
```

Minimum first-boot values:

- `DATABASE_URL`
- `ENVIRONMENT`
- `JWT_SECRET_KEY` and `OTP_HMAC_SECRET` (optional placeholders for local; required in staging/production)

You can leave R2, Resend, Paystack, and Prembly values empty until you actively use them.

## Install Dependencies

```powershell
uv sync
```

## Database

**Never manually edit files under `migrations/models/`.** Use Aerich only. See `spec/DATABASE.md`.

Fresh setup:

```powershell
uv run aerich init -t app.config.database.TORTOISE_ORM
uv run aerich init-db
```

Existing migrations:

```powershell
uv run aerich upgrade
```

Helper with safety warnings:

```powershell
uv run python scripts/migrate.py
```

After changing Tortoise models:

```powershell
uv run aerich migrate --name describe_your_change
uv run aerich upgrade
```

## Run the API

Development:

```powershell
uv run fastapi dev main.py
```

Alternative:

```powershell
uv run uvicorn main:app --reload --port 8000
```

## Smoke Checks

Health:

```text
GET http://localhost:8000/api/v1/health
```

Docs (local or when `OPENAPI_ENABLED=true`):

```text
http://localhost:8000/docs          # app API
http://localhost:8000/docs/admin    # admin API
```

Email HTML previews (no server):

```bash
uv run python scripts/preview_emails.py
```

## Docker

Start local PostgreSQL:

```powershell
docker compose up -d
```

Build the API image:

```powershell
docker build -t fastapi-base-template .
```

Run:

```powershell
docker run --env-file .env -p 8000:80 fastapi-base-template
```

## Common First-Run Issues

- `python` not found: install Python and reopen the terminal.
- `uv` not found: install `uv` and reopen the terminal.
- import errors for `fastapi`, `tortoise`, or other project packages: run `uv sync`.
- `CORS_ORIGINS` parsing incorrectly: use a comma-separated string, not JSON.
- R2 upload failures: set all `R2_*` values before using `/api/v1/base/files`.
- weak secret startup failure in production: set `JWT_SECRET_KEY` and `OTP_HMAC_SECRET` to 32+ character random strings.
