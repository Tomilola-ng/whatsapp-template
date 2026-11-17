# Admin app releases — CBV list/retrieve contract

## What changed

Admin release CRUD now uses the shared class-based view envelope.

| Before | After |
| --- | --- |
| `GET /admin/app/releases?limit=&offset=&published=` | `GET /admin/app/releases?page=&page_size=&published_at__isnull=&ordering=` |
| List `data`: `{items, total, limit, offset}` | List `data`: `{items, meta}` with pagination meta |
| Path param `{release_id}` | Path param `{id}` |
| No retrieve | `GET /admin/app/releases/{id}` |

Public `/app/update-policy`, `/app/legal`, and `/app/events/stream` are unchanged.

Auth still requires an active account with `app_releases.manage`.
