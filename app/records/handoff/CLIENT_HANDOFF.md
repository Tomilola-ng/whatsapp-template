# Records Client Handoff

Base path: `/api/v1/notifications`

All routes require an active bearer token and the permission codename noted below. Missing permission returns `403`. After an admin changes roles, existing tokens return `401` until the user logs in again or refreshes.

## List Notifications

`GET /`

Requires `notifications.read`. Supports `page` and `page_size`. Returns the authenticated user's notifications ordered newest first.

## Mark Read

`PATCH /{notification_id}/read`

Requires `notifications.read`. Returns `404` when the notification does not exist and `403` when it belongs to another account.

`GET /unread-count`, `POST /mark-all-read`, and `GET /stream` provide badge,
bulk-read, and SSE update flows.
