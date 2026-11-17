# Client Change Digest - 2026-07

- Added local-only dev outbox endpoints for OTP-based E2E tests.
- Added standard envelope helpers and a 429 rate-limit envelope.
- Added shell/curl E2E test harness and module runner pattern.
- Added internal maintenance job trigger protected by `X-Internal-Token` outside local development.
- Added RBAC: `user_type` persona field, JWT permission snapshots, and `/access/*` management routes.
- File upload/list and notification routes now require documented permission codenames.
