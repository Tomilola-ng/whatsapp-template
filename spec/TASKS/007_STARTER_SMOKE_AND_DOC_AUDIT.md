# Task 007 - Starter Smoke And Doc Audit

## Purpose

Verify the starter boots, core endpoints respond, and documentation matches repository reality after tasks 001–006.

## Source Of Truth

`README.md`, `AGENTS.md`, `docs/API_CONTRACT.md`, `docs/SETUP_GUIDE.md`, `docs/API_KEYS_GUIDE.md`, live router registration.

## Depends On

001–006.

## Scope

- Run `uv sync` and `uv run python -m compileall app scripts main.py startapp.py`.
- Smoke-test documented endpoints (health, auth flow, notifications, contact).
- Verify documented env vars exist on `AppSettings`.
- Verify `README.md` API surface matches `app/config/routes.py`.
- Confirm no references to removed docs (`docs/archive/`, `EXECUTION_PROMPTS`, `SERVICES_CHECKLIST`).

## Smoke Checklist

```text
GET  /api/v1/health
GET  /docs                    # local only unless OPENAPI_ENABLED
POST /api/v1/auth/register    # optional full flow
POST /api/v1/contact/         # with rate limit awareness
```

## Completion Checklist

- [ ] Compileall passes.
- [ ] Health endpoint returns success.
- [ ] Documented routes match registered routers.
- [ ] Env sample aligns with `AppSettings`.
- [ ] Spec and AGENTS.md list correct first-read files.

## Schema Gap

None — this is a verification gate only.
