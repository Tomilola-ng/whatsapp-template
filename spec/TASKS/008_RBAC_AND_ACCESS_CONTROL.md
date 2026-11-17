# Task 008 - RBAC And Access Control

## Purpose

Replace coarse single-field role checks with a two-layer access model: **user_type** (product persona) plus granular **permissions** bundled in assignable **access roles**.

## Source Of Truth

`spec/AUTH_AND_PERMISSIONS.md`; `spec/API.md` (Access section); `spec/DATABASE.md`; `docs/TEMPLATE_SCHEMA.dbml`.

## Depends On

006 (Aerich migration baseline recommended before production deploy).

## Scope

- Rename `Account.role` → `user_type` (`customer`, `provider`, `admin`).
- Add `permissions`, `access_roles`, join tables, optional direct grants.
- Code-first permission registry with `sync_permissions()` and default role seed.
- Embed `ut` and `perms` in access JWT at login/refresh; bump `auth_token_version` on access changes.
- Route guards: `require_permission`, `require_any_permission`, `require_user_type` (JWT snapshot plus live version/active checks).
- Admin HTTP API under `/access/*` in dedicated `app/access/` module.
- Wire starter routes (notifications, files) to permission guards.
- Shell E2E coverage for forbidden/allowed access after role assignment.

## Out Of Scope

Admin UI, multi-tenant org roles, row-level ABAC, Redis permission cache, OAuth group mapping.

## Completion Checklist

- [x] `user_type` replaces `role` in models, schemas, and API responses.
- [x] Permission registry syncs codenames to DB; default roles seeded idempotently on startup.
- [x] Access JWT carries `ut` and `perms`; assignment changes revoke sessions.
- [x] `/access/*` routes implemented with permission guards.
- [x] Notifications and files routes require documented permissions.
- [x] `spec/API.md`, `AUTH_AND_PERMISSIONS.md`, and handoff docs updated.
- [ ] Aerich migration generated for schema changes (see `spec/CHANGES.md` baseline entry).
