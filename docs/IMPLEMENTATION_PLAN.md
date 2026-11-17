# FastAPI Base Template — Implementation Plan

## Guiding Approach

Keep the starter **bootable after every change**. Prefer small, module-oriented diffs. Do not register routes or models in startup until the backing module exists and is intended to ship.

Use `docs/FEATURES.md` to declare what you are building. Use `spec/TASKS/` for granular check-and-balance work. Record conflicts in `spec/CHANGES.md`.

## Phase 0: Verify The Starter (Day 0)

1. Copy `.env.sample` → `.env`.
2. `uv sync`
3. `uv run fastapi dev main.py`
4. Confirm `GET /api/v1/health`.
5. Read `docs/PROJECT_SPEC.md`, `docs/FEATURES.md`, and `docs/API_CONTRACT.md`.

Optional full smoke (PostgreSQL):

```bash
cp .env.e2e.example .env.e2e
docker compose up -d
createdb fastapi_base_template_e2e
uv run aerich upgrade   # after your fork has migrations
bash app/base/tests/run_all.sh .env.e2e
```

## Phase 1: Starter Hardening (Tasks 001–008)

Complete in order. Each task file lives under `spec/TASKS/`.

| Task | Focus | Depends on |
| ---- | ----- | ---------- |
| 001 | Auth, sessions, OTP | — |
| 002 | File uploads | 001 |
| 003 | Notifications, contact | 001 |
| 004 | Security, rate limits, secrets | 001–003 |
| 005 | Admin provisioning, setup codes | 001, 004 |
| 006 | Aerich discipline, schema baseline | 001–005 |
| 007 | Smoke checks, doc audit | 001–006 |
| 008 | RBAC, JWT permissions, `/access/*` | 006 |

See `spec/TASKS/OVERVIEW.md` for the full dependency graph and completion standard.

### Task 008 status (RBAC)

Implemented in code. Remaining fork work: generate and commit Aerich migrations when you choose a production database target.

## Phase 2: Fork For Your Product

When this repo becomes the base for a real API:

### Milestone A — Product Specification

- Rewrite or extend `docs/PROJECT_SPEC.md` with product overview, roles, and business rules.
- Add product features to `docs/FEATURES.md` with honest status.
- Add `DATABASE.dbml` at repo root if the product schema diverges from the starter.
- Document starter reconciliation decisions in `spec/CHANGES.md`.

### Milestone B — Schema & Models

- Add Tortoise models matching your DBML.
- Register model paths in `AppSettings.tortoise_models` only when modules compile.
- Update `docs/DATABASE_SPEC.md` (or add product `docs/DATABASE_SPEC.md` sections).
- Generate Aerich migrations; never hand-edit `migrations/models/`.

### Milestone C — API Surface

- Scaffold modules: `python scripts/startapp.py <name> --extended`.
- Register permissions in `app/<module>/permissions.py` via `register_module()`.
- Protect routes with `require_permission(...)`.
- Run `uv run python scripts/sync_permissions.py` after adding codenames.
- Extend `docs/API_CONTRACT.md` and module `handoff/CLIENT_HANDOFF.md` files.
- Register routers in `app/config/routes.py` only when ready.

### Milestone D — Integrations & Ops

- Configure Resend, R2, or other integrations as needed.
- Set `JWT_SECRET_KEY`, `OTP_HMAC_SECRET`, `TRUSTED_PROXY_IPS` for staging/production.
- Wire cron/worker to `POST /internal/jobs/run-maintenance` with `X-Internal-Token`.
- Run E2E harness for new modules under `app/<module>/tests/`.

### Milestone E — Hardening & Launch

- Rate-limit public endpoints.
- Audit OpenAPI exposure (`OPENAPI_ENABLED`).
- Verify docs against registered routes and models.
- Run `uv run python -m compileall app scripts main.py startapp.py`.

## Migration Plan (Forks)

1. Decide PostgreSQL vs SQLite for each environment.
2. For PostgreSQL production: `uv run aerich init-db` (fresh) or `aerich upgrade` (existing history).
3. Review generated SQL before staging/production apply.
4. When replacing starter tables, document the path in `spec/CHANGES.md` before cutting migrations.
5. Never hand-edit files under `migrations/models/`.

## Seed Data Plan (Local Dev)

Minimum useful starter data:

- One admin via `uv run python scripts/create_admin.py --email admin@example.com`.
- One verified customer (register + verify OTP flow).
- Optional: assign `content_admin` or custom role via `/access/*` API.

Product forks should add their own seed scripts under `scripts/` once domain models exist.

## Documentation Checklist (Per Feature)

When adding or changing a feature:

- [ ] `docs/FEATURES.md` status updated
- [ ] `docs/API_CONTRACT.md` endpoint row added or changed
- [ ] `docs/DATABASE_SPEC.md` / DBML updated if schema changed
- [ ] `spec/API.md` and `spec/DATABASE.md` kept in sync (agent layer)
- [ ] `app/<module>/handoff/CLIENT_HANDOFF.md` updated for client-visible changes
- [ ] `spec/CHANGES.md` entry if starter assumptions changed

## Related Docs

| Doc | Purpose |
| --- | ------- |
| `docs/PROJECT_SPEC.md` | What the project is and business rules |
| `docs/FEATURES.md` | Feature inventory and status |
| `docs/API_CONTRACT.md` | HTTP contract |
| `docs/DATABASE_SPEC.md` | Schema and migration rules |
| `docs/SETUP_GUIDE.md` | First-run and deployment |
| `docs/API_KEYS_GUIDE.md` | Environment variables |
| `spec/TASKS/` | Granular implementation tasks |
| `AGENTS.md` | Agent working guide |
