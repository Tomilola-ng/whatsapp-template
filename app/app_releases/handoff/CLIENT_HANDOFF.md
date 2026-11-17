# Client handoff — App updates + legal URLs

**Audience:** frontend / mobile integrators

## Update policy (poll)

`GET /api/v1/app/update-policy?platform=IOS|ANDROID&version=1.2.3&build=42`

Unauthenticated. Rate limited.

Response `data` fields clients should branch on:

| Field | Type | Meaning |
| --- | --- | --- |
| `update_available` | bool | A newer published build exists |
| `update_required` | bool | Soft/force gate — block usage until updated |
| `latest_version` / `latest_build` | string / int | Newest published release |
| `minimum_supported_version` / `minimum_supported_build` | string / int | Floor for soft-required updates |
| `title` / `message` | string \| null | Copy for the update dialog |
| `store_url` | string \| null | App Store / Play Store URL |
| `check_after_seconds` | int | Suggested poll interval (default 86400) |

**Client branch:** if `update_required`, show blocking UI; else if `update_available`, show dismissible prompt.

## Live updates (optional SSE)

`GET /api/v1/app/events/stream?platform=IOS&version=1.2.3&build=42`

- Event name: `app_update`
- Payload: same policy shape as above (without `current_*` / `check_after_seconds`)
- Keep-alive comments every ~25s

Prefer polling for most apps; use SSE when you want in-session prompts.

## Legal URLs

`GET /api/v1/app/legal`

```json
{
  "success": true,
  "message": "Legal URLs retrieved",
  "data": {
    "terms_url": "https://example.com/terms",
    "privacy_url": "https://example.com/privacy"
  }
}
```

Backed by `TERMS_URL` and `PRIVACY_URL` env vars — change URLs without shipping a new binary.

## Admin (staff JWT + `app_releases.manage`)

| Method | Path |
| --- | --- |
| `POST` | `/api/v1/admin/app/releases` |
| `GET` | `/api/v1/admin/app/releases` |
| `GET` | `/api/v1/admin/app/releases/{id}` |
| `PATCH` | `/api/v1/admin/app/releases/{id}` |

Create/list/retrieve/patch releases per platform. `store_url` must be HTTPS. Publish with `published_at` set and `is_active=true`.

All responses use `{"success": true, "message": "...", "data": ...}`. The list is paginated:
`GET ...?page=1&page_size=20&platform=IOS&is_active=true&published_at__isnull=false&ordering=-build_number`
returns `data: {"items": [...], "meta": {"page", "page_size", "total_items", "total_pages", "has_next", "has_previous", "next_page", "previous_page"}}`.
A duplicate `(platform, build_number)` returns `409` with `detail.code = "release_build_exists"`; an unknown id returns `404`.
