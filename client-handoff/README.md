# Client handoff (sendable deltas)

This folder holds **standalone integration updates** for frontend and mobile
teams. Each file is meant to be copied or shared as-is when behaviour changes —
you do not need to diff module `CLIENT_HANDOFF.md` files to see what shipped.

**OpenAPI:**

- **App** (`/docs`, `/docs/app`, `docs/openapi/app.json`) — product JWT
- **Admin** (`/docs/admin`, `docs/openapi/admin.json`) — platform admin RBAC

| File | Covers | Product changelog |
| --- | --- | --- |
| [`2026-11-10-cbv-admin-releases.md`](2026-11-10-cbv-admin-releases.md) | Admin app-releases CBV pagination and detail | CBV admin releases (2026-11-10) |
| [`2026-09-08-app-releases-and-profile.md`](2026-09-08-app-releases-and-profile.md) | Update policy, legal URLs, username/display_name | App releases + profile (2026-09-08) |
| [`2026-08-29-optional-email-mfa-and-docs.md`](2026-08-29-optional-email-mfa-and-docs.md) | Optional email MFA, dual OpenAPI, verify-otp auto-login reminder | Optional email MFA + dual OpenAPI (2026-08-29) |


Ongoing API reference stays under `app/*/handoff/CLIENT_HANDOFF.md`.
