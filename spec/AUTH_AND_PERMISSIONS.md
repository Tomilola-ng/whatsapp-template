# Authentication And Permissions

## Auth assumptions

- Passwords are hashed with Argon2; access and refresh tokens are HS256 JWTs signed with `JWT_SECRET_KEY`.
- Access tokens expire after 30 days; refresh tokens after 90 days (tune in `app/accounts/auth.py` if needed).
- Tokens carry account subject, `auth_token_version`, and permission snapshot claims; logout or access changes increment versions and revoke issued tokens.
- Account verification and password reset use five-minute, purpose-scoped OTPs. New rows store an HMAC hash (`OTP_HMAC_SECRET`) and enforce attempt limits; legacy plaintext `code` rows remain readable until migrated.
- The current-user dependency accepts `Bearer` and legacy `JWT` schemes.
- Login and starter protected routes require **active** status via `get_current_active_user`. Generic `get_current_user` remains available for narrow flows such as logout.

## Two-layer access model

### User type (persona)

`Account.user_type` describes **who** the account is in the product:

| User type  | Meaning                                |
| ---------- | -------------------------------------- |
| `customer` | Default end-user                       |
| `provider` | Generic service-provider persona       |
| `admin`    | Staff/back-office persona              |

User type is not the same as access roles. Any user type may receive granular permissions.

### Permissions and access roles

| Concept        | Meaning                                              |
| -------------- | ---------------------------------------------------- |
| **Permission** | Atomic capability (`accounts.edit`, `files.create`)  |
| **AccessRole** | Named bundle (`super_admin`, `content_admin`, …)     |
| **Effective permissions** | Union of role permissions + direct grants |

Permissions are registered in code ([`app/access/permission_registry.py`](app/access/permission_registry.py)) and synced to the `permissions` table. Default system roles are seeded on startup.

## Access JWT claims

Access tokens include:

| Claim   | Meaning                                      |
| ------- | -------------------------------------------- |
| `sub`   | Account ID                                   |
| `v`     | `auth_token_version` at issuance             |
| `pv`    | `permissions_version` at issuance            |
| `ut`    | `user_type` value                            |
| `perms` | Sorted list of effective permission codenames |

Permission checks use `require_permission(...)`, which validates JWT claims **and** live `auth_token_version` / `permissions_version` against the database. Routes that also need the full `Account` model still use `get_current_user` / `get_current_active_user`.

When access roles or direct grants change, the API bumps `auth_token_version` and `permissions_version`. Clients must sign in again (or refresh) to pick up new permissions.

## Route protection

| Route group                         | Access                                      |
| ----------------------------------- | ------------------------------------------- |
| Register, login, OTP/password reset | Public; rate limiting on sensitive endpoints |
| Health, contact                     | Public                                      |
| Profile routes                      | Authenticated **active** user                 |
| Notifications, files                | Active user + required permission codename  |
| `/access/*` management              | Active user + `access.read` / `access.manage` / `accounts.assign_roles` |

## Admin provisioning

1. Run `uv run python scripts/create_admin.py --email admin@example.com` (optional `--phone-number`, `--name`).
2. Script sets `user_type=admin`, assigns the `super_admin` access role, and sends invite/upgrade email.
3. Recipient completes setup via `exchange-setup-code` and `reset-password`.

There is no HTTP `make-admin` route.

## File permissions

- Upload requires `files.create` and an active account.
- Local file listing requires `files.read` and an active account.

## Notification permissions

- List and mark read require `notifications.read`.
- Device token management requires `notifications.manage`.
- Users may only access their own notification rows (owner check in services).

## Failure semantics

- `401`: missing, invalid, expired, revoked, or wrong-scope credential.
- `403`: authenticated but inactive, missing permission, or wrong user type.
- `404`: resource absent.
- `409`: valid-state conflict defined by the endpoint contract.
- `429`: rate limit exceeded (see task 004).

Permission checks belong in route dependencies (`require_permission`) or services before mutation.
