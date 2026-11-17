# Access Control Client Handoff

Base path: `/api/v1/access`

## My Permissions

`GET /access/me/permissions`

Requires bearer token. Returns:

```json
{
  "user_type": "customer",
  "permissions": ["notifications.read", "notifications.manage"]
}
```

Permissions come from the access JWT. The endpoint validates the token against live session state (active status and version fields). After an admin changes roles, existing tokens return `401` until the user logs in again or refreshes.

## Assignment rules (staff)

- Users cannot modify their own roles or direct permissions (`403`).
- `role_slugs` on replace must include at least one role (`400` if empty).
- Only holders of `*` can assign the `super_admin` role.
- Assigners can only grant roles whose permissions they already hold.
- System roles (`is_system: true`) cannot be renamed or have permissions changed.

## Management (staff)

| Method | Path | Permission |
| ------ | ---- | ---------- |
| GET | `/access/permissions` | `access.read` |
| GET | `/access/roles` | `access.read` |
| POST | `/access/roles` | `access.manage` |
| PATCH | `/access/roles/{role_id}` | `access.manage` |
| DELETE | `/access/roles/{role_id}` | `access.manage` |
| GET | `/access/accounts/{account_id}/roles` | `accounts.read` |
| PUT | `/access/accounts/{account_id}/roles` | `accounts.assign_roles` |
| PUT | `/access/accounts/{account_id}/permissions` | `accounts.assign_roles` |

Missing permission returns `403` with `"You do not have permission to perform this action."`

Role assignment changes invalidate existing tokens; clients must re-authenticate.
