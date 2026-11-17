# Client Handoff Hub

This folder collects frontend and mobile integration notes for the generic starter.

- `PLATFORM.md` covers auth, envelopes, pagination, permissions, rate limits, and integration checklist items.
- `ENDPOINTS_CHECKLIST.md` tracks exposed starter endpoints and auth requirements.
- Module docs live under `app/<module>/handoff/CLIENT_HANDOFF.md` (including [`app/access/handoff/CLIENT_HANDOFF.md`](../../access/handoff/CLIENT_HANDOFF.md)).

Useful commands:

```bash
cp .env.e2e.example .env.e2e
bash app/base/tests/run_all.sh .env.e2e
bash app/accounts/tests/run.sh .env.e2e
bash app/access/tests/run.sh .env.e2e
```
