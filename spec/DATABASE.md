# Database Specification

## Starter shape

`docs/TEMPLATE_SCHEMA.dbml` describes the supported Tortoise models for the base template. PostgreSQL is recommended for production; local first boot uses SQLite via `DATABASE_URL=sqlite://db.sqlite3`.

Registered starter tables:

| Area            | Tables              | Notes                                      |
| --------------- | ------------------- | ------------------------------------------ |
| Identity/auth   | `accounts`, `otps`, `password_setup_codes` | Prefixed string IDs on accounts |
| Access control  | `permissions`, `access_roles`, join tables (`app/access/models.py`) | RBAC layer |
| Files           | `fileasset`         | Integer primary key; optional owner link   |
| Notifications   | `notifications`     | Recipient-scoped in-app rows; no device push tokens |
| Preferences     | `account_preferences` | In-app/email/marketing toggles; `push_enabled` is not mobile push |
| Platform        | `audit_logs`, `client_error_logs`, `app_releases` | Append-only audit, client diagnostics, optional update policy |

Application-owned IDs except `fileasset.id` are opaque prefixed strings. Clients must not parse ID prefixes.

Use `make_id_default(IDPrefix.X)` for Tortoise `default=` callables. Do not use `functools.partial` for ID defaults; Aerich cannot serialize partial objects reliably when generating migration metadata.

## Important constraints

- `accounts.email` is unique when present.
- `accounts.user_type` is one of `customer`, `provider`, `admin`.
- `permissions.codename` and `access_roles.slug` are unique.
- OTP rows may store `code_hash` (preferred) or legacy plaintext `code` during migration.
- `password_setup_codes` store hashed opaque codes for admin invite links.

## Aerich workflow — required

**Always use Aerich to manage schema changes. Never hand-edit migration files.**

```powershell
# After changing Tortoise models:
uv run aerich migrate --name describe_your_change
uv run aerich upgrade
```

For a fresh database:

```powershell
uv run aerich init -t app.config.database.TORTOISE_ORM
uv run aerich init-db
```

Or use the helper:

```powershell
uv run python scripts/migrate.py
```

### Rules

1. Use `uv run aerich migrate` and `uv run aerich upgrade` **only** — do not create or edit files under `migrations/models/` by hand.
2. Check in generated Aerich history for the starter schema baseline.
3. Review generated SQL before applying to staging or production PostgreSQL.
4. Take backups and rehearse migrations on a copy before upgrading populated databases.

### Never do this

- Manually write `migrations/models/*.py` migration files.
- Edit existing migration files to "fix" schema drift — change models and generate a new migration instead.
- Run `init-db` against a populated production database.

## PostgreSQL verification (before production)

- Fresh `aerich upgrade`, application startup, and endpoint smoke tests.
- Timezone-aware `timestamptz` round trips.
- Unique email constraint behavior.
- FK `ON DELETE` behavior matches model definitions.

Local SQLite remains valid for development and compile checks; verify constraints on PostgreSQL before production deploy.
