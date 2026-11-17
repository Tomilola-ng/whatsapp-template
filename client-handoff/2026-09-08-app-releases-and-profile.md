# Client handoff — App releases, legal URLs, profile username

**Date:** 2026-09-08  
**Audience:** frontend / mobile integrators

## App update policy

`GET /api/v1/app/update-policy?platform=IOS|ANDROID&version=1.2.3&build=42`

| Field | Use |
| --- | --- |
| `update_required` | Block the app until the user updates |
| `update_available` | Optional dismissible prompt |
| `title` / `message` / `store_url` | Dialog copy + store link |
| `check_after_seconds` | Suggested re-poll interval |

Optional live stream: `GET /api/v1/app/events/stream` (SSE event `app_update`).

## Legal URLs

`GET /api/v1/app/legal` → `{ terms_url, privacy_url }` from server env (`TERMS_URL`, `PRIVACY_URL`). Prefer this over hardcoding store review links in the binary.

## Profile fields (additive)

Account payloads (`/auth/me`, `/auth/current-user`, login/OTP user objects) may now include:

| Field | Notes |
| --- | --- |
| `username` | Unique handle, `^[a-z0-9_]{3,32}$` |
| `display_name` | Override when set; otherwise first + last |

`PATCH /api/v1/auth/update-profile` accepts optional `username` and `display_name` **in addition to** existing `first_name`, `last_name`, `phone_number`, `state`.

| Status | Code | Meaning |
| --- | --- | --- |
| 409 | `username_taken` | Handle already used |
| 422 | `invalid_username` / `invalid_display_name` | Validation failed |

## Admin releases

Staff with `app_releases.manage` (default on `content_admin` / `super_admin`):

- `POST /api/v1/admin/app/releases`
- `GET /api/v1/admin/app/releases`
- `PATCH /api/v1/admin/app/releases/{release_id}`
