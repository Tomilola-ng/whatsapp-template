# Task 001 - Check And Balance Auth, Sessions, And OTP

## Purpose

Verify the starter's authentication, token, OTP, protected-route, active-user, and session-revocation foundations. Preserve working flows and define the smallest security-compatible changes.

## Source Of Truth

`spec/API.md` auth section; `spec/AUTH_AND_PERMISSIONS.md`; `docs/TEMPLATE_SCHEMA.dbml` (`accounts`, `otps`); live `app/accounts` and `app/records` code.

## Depends On

None.

## Scope

- Test register, activation, login, access token, refresh token, logout, current user, password reset, and change-password behavior.
- Confirm Bearer handling, token scopes/expiry, `auth_token_version` revocation, and account status checks.
- Ensure new OTPs use HMAC hashing at rest with attempt limits; legacy plaintext rows remain readable.
- Make protected starter routes use `get_current_active_user` where appropriate.
- Add `/auth/me` alias for `/auth/current-user` if missing.

## Out Of Scope

Social login, MFA, passkeys, persisted `auth_sessions` tables, or new product domains.

## Database Tables

`accounts`, `otps` (optional `password_setup_codes` handled in task 005).

## Backend Files To Review

`app/accounts/auth.py`, `models.py`, `schemas.py`, `services/`, `routes.py`, `permissions.py`, `utils.py`; `app/records/models.py`; `app/config/settings.py`; `.env.sample`.

## API Endpoints

Audit all existing `/auth/*` routes listed in `spec/API.md`.

## Business Rules

- Only active verified users may log in or access protected starter routes.
- Access, refresh, and reset tokens have distinct scopes.
- Logout and password changes revoke sessions via `auth_token_version`.
- OTPs expire, are purpose-scoped, attempt-limited, and single-use.

## Permissions

Public auth mutations are narrowly scoped. Current-user/logout/change-password require the current user.

## Testing Requirements

- Token scope, expiry, and revocation paths.
- OTP purpose, expiry, attempts, and reuse rejection.
- Protected routes return `403` for inactive users and `401` for invalid credentials.

## Completion Checklist

- [ ] Existing behavior documented against `spec/API.md`.
- [ ] OTP hashing and attempt limits implemented or explicitly deferred in `spec/CHANGES.md`.
- [ ] Active-user guard applied to protected starter routes.
- [ ] `/auth/me` alias available when clients expect it.

## Schema Gap

None for core starter tables. Hashed OTP storage may require a generated Aerich migration.
