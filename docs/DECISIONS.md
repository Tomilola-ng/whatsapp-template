# Product defaults ledger

Resolved starter defaults when the project spec leaves choices open. Forks
should update this file when they lock product policy — do not invent silent
defaults in service code without recording them here.

## Auth

| Decision | Value | Notes |
| --- | --- | --- |
| Register OTP auto-login | yes | `POST /auth/verify-otp` returns access + refresh |
| Email MFA on login | **opt-in** | `email_login_mfa_enabled` on account preferences; default off |
| OTP validity | 5 minutes | Shared across activation / login MFA / password reset |
| Profile fields | first/last + optional username / display override | `display_name` prefers override, then first+last |

## Public surface

| Decision | Value | Notes |
| --- | --- | --- |
| Thin launch surface | mount less, do not delete | Omit routers in `routes.py`; keep modules in the tree |
| App update policy | included | `GET /app/update-policy` + admin release CRUD (class-based view) |
| Legal URLs | env-backed | `TERMS_URL` / `PRIVACY_URL` via `GET /app/legal` |

## Views

| Decision | Value | Notes |
| --- | --- | --- |
| CRUD endpoints | class-based (`ModelView`) | `app/<module>/views.py`; guide in `docs/CBV_GUIDE.md` |
| Response shape | `{success, message, data}` envelope | Lists: `data = {items, meta}` with `page` / `page_size` |
| Default actions | list, create, retrieve, PATCH, delete | `PUT` is opt-in |
| Complex logic | `services/` | Called from view hooks or `@action` methods |

## Email

| Decision | Value | Notes |
| --- | --- | --- |
| Shared HTML shell | `app/base/email_template.py` | Modules build inner HTML only |
| Brand colors | env-overridable | `BRAND_PRIMARY_COLOR`, `BRAND_DARK_COLOR`, `BRAND_ON_PRIMARY_COLOR` |
| Client links | `CLIENT_APP_URL` | Falls back to `APP_BASE_URL` |

## OpenAPI

| Decision | Value | Notes |
| --- | --- | --- |
| Docs surfaces | app + admin | `/docs` and `/docs/admin` when OpenAPI enabled |
| Default mount | app | Admin RBAC under `/docs/admin` |

## Ops

| Decision | Value | Notes |
| --- | --- | --- |
| Container roles | `api` / `worker` / `migrate` | `scripts/ops/docker-entrypoint.sh` |
| Worker cadence | 300s default | `scripts/job_worker.py --interval` |
| E2E token mint | `scripts/e2e_issue_token.py` | Active account + JWTs without email/OTP |
