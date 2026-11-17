# Task 005 - Admin Provisioning And Setup Codes

## Purpose

Replace local-only HTTP admin promotion with script-based provisioning and opaque setup-code exchange for password setup.

## Source Of Truth

`spec/AUTH_AND_PERMISSIONS.md` admin section; `spec/API.md` (`/auth/exchange-setup-code`); `scripts/create_admin.py`.

## Depends On

001, 004.

## Scope

- Implement `password_setup_codes` model and `exchange-setup-code` route.
- Update `scripts/create_admin.py`: email-primary (`--email` required), optional `--phone-number`, no username field.
- Send invite/upgrade emails with opaque `?code=` links (not JWT in URL).
- Remove HTTP `make-admin` route if present.

## Out Of Scope

Admin dashboards, RBAC tables, multi-tenant org admins.

## Database Tables

`password_setup_codes`.

## Backend Files To Create Or Update

`app/records/models.py`, `app/accounts/services/`, `app/accounts/routes.py`, `app/accounts/schemas.py`, `app/accounts/auth.py`, `scripts/create_admin.py`, `.env.sample` (`PASSWORD_SETUP_URL`, `ADMIN_PASSWORD_SETUP_CODE_EXPIRE_HOURS`).

## Business Rules

- Setup codes are single-use, hashed at rest, and expire per settings.
- Exchanging a code issues a short-lived `admin_password_setup` JWT for `reset-password`.
- `create_admin.py` uses the same Account model and email helpers as the API.

## Completion Checklist

- [ ] `create_admin.py` is email-primary and matches Account model fields.
- [ ] `exchange-setup-code` documented in `spec/API.md` and implemented.
- [ ] No `make-admin` HTTP route remains.
- [ ] Aerich migration generated for `password_setup_codes` (task 006).

## Schema Gap

Add `password_setup_codes` via Aerich — never hand-write migration files.
