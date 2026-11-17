# E2E coverage honesty

Shell E2E (`app/base/tests/run_all.sh`) proves **scenarios**, not “every
route or every client screen works.” The pass counter is assertion count, not
unique route coverage.

Read this before telling humans or agents that E2E green means frontend-safe.

## What green means

| Claim | True? |
| --- | --- |
| Core auth / OTP / password / contact smoke paths work | Usually yes |
| Every `/api/v1` operation was called | **No** — refresh with the coverage script |
| Optional integrations (R2, Resend) | Only if configured and covered |
| Production provider money paths | **No** unless your fork adds them |
| Mobile SSO / store billing / device push (Apple, Google, RevenueCat, Expo) | **No** — intentionally removed from this WhatsApp starter |
| WhatsApp webhook and test routes | Only when `WHATSAPP_ENABLED=true` and covered by your fork's tests |

## Refresh coverage

```bash
bash app/base/tests/run_all.sh .env.e2e
uv run python scripts/e2e_route_coverage.py
uv run python scripts/e2e_route_coverage.py --markdown
```

Optional CI gate:

```bash
uv run python scripts/e2e_route_coverage.py --fail-under 20
```

Also keep the endpoint checklist honest:

```bash
uv run python scripts/check_api_consistency.py
```

## Auth matrix (starter)

| Principal | Typical headers |
| --- | --- |
| App user | `Authorization: Bearer <access>` |
| Platform admin | Admin JWT + RBAC permission |
| Public | No auth (`/health`, `/auth/register`, `/contact`) |
| Internal jobs | `X-Internal-Token` (outside local when configured) |

## Docs surfaces

When `OPENAPI_ENABLED=true` (or `ENVIRONMENT=local`):

| Surface | URL |
| --- | --- |
| App | `/docs` or `/docs/app` · `/openapi/app.json` |
| Admin | `/docs/admin` · `/openapi/admin.json` |

Export: `uv run python scripts/export_openapi.py`
