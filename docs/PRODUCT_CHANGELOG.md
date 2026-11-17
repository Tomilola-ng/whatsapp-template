# Product change log

Append-only ledger of **intentional product/API behaviour changes**. Unlike
[`docs/BUGFIX_LOG.md`](BUGFIX_LOG.md) (symptom → bugfix commit), this log tracks
**expected flow changes**, new endpoints, and client-facing contract updates.

Agents and humans should read this before assuming “E2E green = client done”,
and append here whenever product behaviour shifts.

## How to use

1. **Before changing client flows** — search this file and module
   `CHANGELOG_*.md` handoff digests.
2. **After a product/API behaviour change** — add a new entry at the **top** of
   Entries (newest first), and add/update a file under
   [`client-handoff/`](../client-handoff/).
3. Update the relevant module `app/*/handoff/CLIENT_HANDOFF.md` when the
   long-term reference changes.
4. Record architectural reconciliation in `spec/CHANGES.md` when the choice is
   structural — do not duplicate long prose here.

## Entry template

```markdown
### YYYY-MM-DD — Short title

- **Status**: shipped | partial | planned
- **Area**: module or flow
- **Client impact**: what app/mobile/API integrators must do differently
- **API / env changes**: new/changed routes, fields, env vars (brief)
- **Commit(s)**: `sha` — subject (or `pending`)
- **Handoff**: link to module CLIENT_HANDOFF / client-handoff delta
- **Notes**: optional follow-ups
```

## Entries

### 2026-11-10 — Class-based views; admin release list contract

- **Status**: shipped
- **Area**: base (`app/base/views.py`) / app_releases admin endpoints
- **Client impact**: `GET /admin/app/releases` now uses `page` / `page_size` and returns `data: {items, meta}` (was `limit` / `offset` with `{items, total, limit, offset}`); the `published` filter is now `published_at__isnull` (inverted meaning); `GET /admin/app/releases/{id}` added; path param renamed `release_id` → `id`.
- **API / env changes**: none beyond the above; no env changes.
- **Commit(s)**: pending
- **Handoff**: [`client-handoff/2026-11-10-cbv-admin-releases.md`](../client-handoff/2026-11-10-cbv-admin-releases.md), `app/app_releases/handoff/CLIENT_HANDOFF.md`, [`docs/CBV_GUIDE.md`](CBV_GUIDE.md)
- **Notes**: Establishes the CBV pattern for all future CRUD modules. WhatsApp HTTP routes unchanged; new env allowlists are server-side only (see `.env.sample`).

### 2026-09-08 — App releases, legal URLs, profile username

- **Status**: shipped
- **Area**: app_releases / accounts profile / ops docs
- **Client impact**: Poll `GET /app/update-policy` for soft/force updates; read legal links from `GET /app/legal`; profile responses may include `username` and `display_name`; `PATCH /auth/update-profile` accepts those fields in addition to first/last/phone/state.
- **API / env changes**: `/app/*`, `/admin/app/releases`; `TERMS_URL`, `PRIVACY_URL`, `RATE_LIMIT_UPDATE_POLICY`; account `username` / `display_name_override`
- **Commit(s)**: `7bc960b` — feat: port app-release and profile fields into the FastAPI template
- **Handoff**: [`client-handoff/2026-09-08-app-releases-and-profile.md`](../client-handoff/2026-09-08-app-releases-and-profile.md), `app/app_releases/handoff/CLIENT_HANDOFF.md`
- **Notes**: Thin public surface is documented in `AGENTS.md` / `DECISIONS.md` (omit routers; do not delete modules).

### 2026-08-29 — Optional email MFA + dual OpenAPI + email kit

- **Status**: shipped
- **Area**: accounts / docs / email / ops
- **Client impact**: `POST /auth/verify-otp` still returns tokens (auto-login after register). Login stays password→tokens by default. When `email_login_mfa_enabled` is true on preferences, `POST /auth/login` returns `login_pending` and clients must call `POST /auth/verify-login-otp`. Use `/docs` (app) and `/docs/admin` separately.
- **API / env changes**: `email_login_mfa_enabled` on preferences; `POST /auth/verify-login-otp`; `CLIENT_APP_URL`, brand color env vars; dual OpenAPI export
- **Commit(s)**: pending
- **Handoff**: [`client-handoff/2026-08-29-optional-email-mfa-and-docs.md`](../client-handoff/2026-08-29-optional-email-mfa-and-docs.md), `app/accounts/handoff/CLIENT_HANDOFF.md`
- **Notes**: Preview emails with `uv run python scripts/preview_emails.py`
