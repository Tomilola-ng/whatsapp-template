# Bugfix Log

Agents must read this log before patching a user-facing bug and add an entry after
the fix is verified. The purpose is symptom → root cause → fix → commit
traceability across starter forks.

## Entry template

### YYYY-MM-DD — Short title

- **Area**: module or flow
- **Symptom**: user-visible failure and relevant status/error code
- **Root cause**: why the failure happened
- **Fix**: implementation and regression coverage
- **Commit(s)**: commit hash and subject, or `pending`
- **Verification**: exact command or HTTP reproduction
- **Notes**: rollout or compatibility details

## Entries

### 2026-07-29 — Optional integration import broke application startup

- **Area**: optional third-party integrations
- **Symptom**: application import or startup failed even when an optional integration was not configured.
- **Root cause**: optional client libraries were imported eagerly from a startup-loaded module.
- **Fix**: load optional integrations lazily inside the call path; missing configuration fails only when that feature is invoked.
- **Commit(s)**: retained as a generic production lesson for this starter.
- **Verification**: import the app with optional integration env vars unset; first boot and `/api/v1/health` succeed.
- **Notes**: optional integrations must be import-safe and fail only when used.
