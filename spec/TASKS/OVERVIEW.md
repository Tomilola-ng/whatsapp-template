# Starter Task Overview

## Purpose

Provide an ordered, implementation-ready path for hardening and verifying the generic FastAPI starter without adding product-specific domains.

## Source Of Truth

Use sources in this order:

1. `docs/API_CONTRACT.md`, `docs/DATABASE_SPEC.md`, and `spec/AUTH_AND_PERMISSIONS.md`
2. `docs/TEMPLATE_SCHEMA.dbml` for schema shape
3. Live repository code and conventions
4. `AGENTS.md`

Conflicts belong in `spec/CHANGES.md` and task Schema Gap sections.

## Execution Model

1. Complete tasks 001–004 as check-and-balance work. Inspect first; preserve working systems; make only evidence-based changes.
2. Complete admin provisioning (005) and migration baseline (006) before broad feature additions.
3. Run smoke and doc audit (007) after substantive changes.
4. Keep the app bootable after every task.

## Repository Shape

```text
app/<domain>/
  models.py
  schemas.py
  services/
    __init__.py
    core.py
  routes.py
  utils.py
  tests/
  handoff/
  permissions.py  # optional; register codenames via app.access.permission_registry
```

RBAC lives in `app/access/` (models, registry, JWT guards, `/access/*` routes). Account active-status guards stay in `app/accounts/permissions.py`.

## Global Rules

- Routes stay thin; business logic belongs in `services/` modules.
- Keep models and `docs/TEMPLATE_SCHEMA.dbml` synchronized.
- Require active authentication on protected starter routes.
- Persist notifications before any future broadcast layer.
- Update `.env.sample` and docs only when implementation introduces real configuration.
- **Never hand-edit** files under `migrations/models/` — use Aerich only.

## Dependency Logic

| Task | Depends on | Why |
| ---- | ---------- | --- |
| 001  | None       | Establish trustworthy auth/session/OTP contract |
| 002  | 001        | File ownership requires authenticated identity |
| 003  | 001        | Notification ownership and contact abuse controls |
| 004  | 001–003    | Rate limits, secrets, OpenAPI, proxy IP trust |
| 005  | 001, 004   | Admin setup codes and `create_admin.py` alignment |
| 006  | 001–005    | Aerich baseline and migration discipline |
| 007  | 001–006    | Smoke checks and documentation audit |
| 008  | 006        | RBAC tables, JWT permissions, access admin API |

## Task Files

1. `001_CHECK_AND_BALANCE_AUTH_SESSIONS_AND_OTP.md`
2. `002_CHECK_AND_BALANCE_FILE_UPLOADS.md`
3. `003_CHECK_AND_BALANCE_NOTIFICATIONS.md`
4. `004_SECURITY_HARDENING_AND_RATE_LIMITS.md`
5. `005_ADMIN_PROVISIONING_AND_SETUP_CODES.md`
6. `006_MIGRATIONS_AND_SCHEMA_BASELINE.md`
7. `007_STARTER_SMOKE_AND_DOC_AUDIT.md`
8. `008_RBAC_AND_ACCESS_CONTROL.md`

## Completion Standard

A task is complete only when its code, applicable migrations, docs, and smoke checks agree. Mark checklist items honestly — use `planned` for documented-but-unimplemented work.
