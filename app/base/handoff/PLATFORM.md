# Platform Client Guide

## Response Envelope

Success responses use:

```json
{ "success": true, "message": "OK", "data": {} }
```

Errors and rate limits use:

```json
{ "success": false, "message": "Too many requests. Please try again later.", "data": null }
```

Some legacy starter endpoints still return `{ "message": "...", "data": ... }`; client code should prefer the `success` flag when present and continue reading `message` for compatibility.

## Auth

Use `Authorization: Bearer <access_token>` on protected endpoints. `POST /api/v1/auth/login` returns `access`, `refresh`, and `user`. `POST /api/v1/auth/refresh-token` returns a new access token. Logout revokes the current token version, so stale access and refresh tokens should be discarded.

Account responses expose `user_type` (`customer`, `provider`, `admin`), not a coarse `role` field.

## Permissions

Access tokens embed a permission snapshot (`perms`) and `user_type` (`ut`). Many protected routes also require a specific permission codename (for example `notifications.read`, `files.create`). Missing permission returns `403`.

`GET /api/v1/access/me/permissions` returns the current token's `{ user_type, permissions }` after validating session version fields. Staff manage roles and grants through `/api/v1/access/*`; see [`app/access/handoff/CLIENT_HANDOFF.md`](../../access/handoff/CLIENT_HANDOFF.md).

When an admin changes roles or direct grants, existing tokens return `401` until the user logs in again or refreshes.

## Files

`POST /api/v1/base/files` requires active authentication and `files.create`. `GET /api/v1/base/files` is mounted only when `ENVIRONMENT=local` and requires `files.read`. R2 credentials must be configured before uploads succeed.

## Pagination

List endpoints that opt into pagination accept `page` and `page_size` query parameters and return:

```json
{
  "items": [],
  "meta": {
    "page": 1,
    "page_size": 20,
    "total_items": 0,
    "total_pages": 0,
    "has_next": false,
    "has_previous": false,
    "next_page": null,
    "previous_page": null
  }
}
```

## Rate Limits

On 429, retry after the `Retry-After` header. When supported by the active limiter backend, clients may also receive `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `X-RateLimit-Reset`.

## Integration Checklist

- Store access and refresh tokens securely.
- Treat 401 as signed out or token refresh needed.
- Treat 403 as authenticated but not permitted or inactive.
- Call `GET /api/v1/access/me/permissions` after login to cache the user's permission set for UI gating.
- Surface 429 with a wait-and-retry message.
- Never depend on `/api/v1/dev/outbox`; it is local-only test tooling.
