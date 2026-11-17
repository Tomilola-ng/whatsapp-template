# Accounts Client Change Digest - 2026-07

- Logout and password changes revoke prior token versions.
- OTP-based E2E tests can fetch codes through the local-only dev outbox.
- Auth routes have per-route rate-limit settings.
- Account responses expose `user_type` instead of a coarse `role` field; see access handoff for permissions.
