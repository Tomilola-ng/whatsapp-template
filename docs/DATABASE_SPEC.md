# WhatsApp FastAPI 2026 Template — Database Specification

## Source Of Truth

`docs/TEMPLATE_SCHEMA.dbml` is the starter schema source of truth. PostgreSQL is recommended for production; local first boot may use SQLite via `DATABASE_URL=sqlite://db.sqlite3`.

When you fork for a product, you may add a root `DATABASE.dbml` for product tables (see crowdrental-api pattern) and keep `docs/TEMPLATE_SCHEMA.dbml` as historical starter reference or merge deliberately. Record conflicts in `spec/CHANGES.md`.

**Never manually create or edit files under `migrations/models/`.** Use Aerich only.

The template commits an Aerich-generated baseline containing the supported
starter schema. Forks apply it with `aerich upgrade` and generate later changes
with `aerich migrate`.

## Mapping Schema To Modules

| Schema area | Tables | Module |
| ----------- | ------ | ------ |
| Identity / auth | `accounts`, `otps`, `password_setup_codes` | `app/accounts`, `app/records` |
| Access control | `permissions`, `access_roles`, join tables | `app/access` |
| Files | `fileasset` | `app/base` |
| Notifications | `notifications` | `app/records` |
| Preferences | `account_preferences` | `app/accounts` |
| Audit | `audit_logs` | `app/audit` |
| Client diagnostics | `client_error_logs` | `app/client_errors` |
| App releases | `app_releases` | `app/app_releases` |

Keep route handlers thin. Business rules live in `services/` modules; request/response contracts in `schemas.py`.

## Key Tables

### Accounts

- Prefixed string primary key (`ACC_…`).
- `user_type`: `customer`, `provider`, or `admin`.
- `status`: `active`, `suspended`, `pending_verification`, `deactivated`, `banned`.
- `auth_token_version` and `permissions_version` invalidate JWTs on logout or access changes.
- `email` unique when present.
- Optional `username` (unique) and `display_name_override` for profile display.
- Optional `image_id` FK to `fileasset`.

### Access Control

- `permissions` — code-first registry rows (`codename`, `module`, `action`).
- `access_roles` — named bundles (`slug` unique, `is_system` flag).
- `access_role_permissions` — role ↔ permission join.
- `account_access_roles` — account ↔ role assignments with `assigned_by_id`.
- `account_permissions` — direct grants/denies per account.

Default system roles (seeded on startup): `super_admin`, `accounts_manager`, `content_admin`, `customer_basic`, `provider_basic`.

### OTPs

- Linked to `accounts` for verification and password-reset flows.
- Prefer `code_hash` (HMAC with `OTP_HMAC_SECRET`); legacy plaintext `code` supported during transition.
- Track `attempts`, `max_attempts`, `expires_at`, `status`.

### Password Setup Codes

- Opaque admin invite codes stored hashed.
- Used by `exchange-setup-code` flow.

### File Assets

- Integer primary key.
- `key` stores R2 object path; responses include presigned URLs.

### Notifications

- Recipient-scoped via `account_id`.
- `type`, `channel`, `title`, `message`, optional `action_url`.
- `is_read` / `read_at` for client state.
- `channel` values include a legacy `push` enum label meaning **in-app** delivery (list + SSE), not mobile device push. There is no `push_device_tokens` table in this starter.

### Account preferences

- `push_enabled` controls in-app notification delivery preference (not FCM/APNs/Expo).
- `email_notifications_enabled` and `marketing_email_enabled` gate optional email channels.

### Platform Records

- `audit_logs` is append-only and stores redacted metadata.
- `client_error_logs` stores redacted reports with nullable account linkage.
- `app_releases` stores per-platform version/build floors, force-update flags, and store URLs.

## ID Conventions

Application-owned IDs except `fileasset.id` are opaque prefixed strings. Clients must not parse ID prefixes.

Use `make_id_default(IDPrefix.X)` for Tortoise `default=` callables. **Do not** use `functools.partial` for ID defaults — Aerich cannot serialize partial objects reliably.

## Aerich Workflow

After changing Tortoise models:

```powershell
uv run aerich migrate --name describe_your_change
uv run aerich upgrade
```

Fresh database:

```powershell
uv run aerich init -t app.config.database.TORTOISE_ORM
uv run aerich init-db
```

Or use the helper:

```powershell
uv run python scripts/migrate.py
```

### Rules

1. Use `uv run aerich migrate` and `uv run aerich upgrade` only.
2. Check in generated Aerich history for your fork's schema baseline.
3. Review generated SQL before applying to staging or production PostgreSQL.
4. Take backups and rehearse migrations on a copy before upgrading populated databases.

### Never Do This

- Manually write or edit `migrations/models/*.py`.
- Run `init-db` against a populated production database.

## PostgreSQL Verification (Before Production)

- Fresh `aerich upgrade`, application startup, and endpoint smoke tests.
- Timezone-aware timestamp round trips.
- Unique email constraint behavior.
- FK `ON DELETE` behavior matches model definitions.

Local SQLite remains valid for development; verify constraints on PostgreSQL before production deploy.

## Related Docs

- Visual schema: `docs/TEMPLATE_SCHEMA.dbml`
- Agent reconciliation: `spec/DATABASE.md` (kept in sync with this spec)
