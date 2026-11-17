# WhatsApp Integration

Domain-agnostic WhatsApp Cloud API wiring via **PyWa** (`pywa_async`). Single business number (single-WABA) starter — not multi-tenant middleware.

## Flow

```text
Meta webhook → PyWa handlers → entry_point → brain.process_message → replies.send_reply
```

| Module | Role |
|--------|------|
| `app/whatsapp/client.py` | Attach PyWa to FastAPI; Dokploy-safe callback origin; auto-register off by default |
| `app/whatsapp/services/handlers.py` | Inbound text / audio / image pipeline |
| `app/whatsapp/services/entry.py` | MSISDN normalize, service-window note, call the brain |
| `app/whatsapp/brain.py` | **Replace this** with your product logic / agent |
| `app/whatsapp/services/replies.py` | Only place that calls PyWa text send APIs (soft transient retry) |
| `app/whatsapp/services/templates.py` | Thin approved-template send helper |
| `app/whatsapp/services/media.py` | Allowlisted media download + describe/transcribe |
| `app/whatsapp/services/error_classify.py` | Meta error → retryable classification |
| `app/whatsapp/services/service_window.py` | In-memory 24h customer-service window helpers |
| `app/whatsapp/services/callbacks.py` | Button callbacks (`help:` sample) |
| `app/whatsapp/services/flows.py` | Flow completion registry (generic contact sample) |
| `app/whatsapp/routes.py` | `GET /whatsapp/status`, local `test-message` / `test-agent` |

Root shims (`handlers.py`, `entry.py`, …) re-export the service package for older imports.

## Enable

1. Set env from `.env.sample` (`WHATSAPP_ENABLED=true` + required secrets).
2. Point Meta webhook to `{APP_BASE_URL or WHATSAPP_CALLBACK_URL}{WHATSAPP_WEBHOOK_ENDPOINT}` (default `/api/v1/webhooks/whatsapp`).
3. Subscribe the `messages` field; add a tester number.
4. Keep `WHATSAPP_AUTO_REGISTER_CALLBACK=false` on PaaS (Traefik race). Configure the callback once in Meta UI.
5. Smoke: `GET /api/v1/whatsapp/status`, then `POST /api/v1/whatsapp/test-agent` (local/staging).

## Hardening defaults

- PyWa `validate_updates=True` + `WHATSAPP_APP_SECRET` for webhook signatures.
- Inbound media: host allowlist (`WHATSAPP_MEDIA_FETCH_ALLOWLIST_HOSTS`), MIME allowlist, size cap (`WHATSAPP_MEDIA_MAX_BYTES`).
- Outbound text/template: soft in-process retry on transient Meta codes (`WHATSAPP_OUTBOUND_MAX_ATTEMPTS`).
- Service window: `WHATSAPP_SERVICE_WINDOW_HOURS` (default 24); recorded in-memory from inbound timestamps — forks may persist later.

See [WHATSAPP_THREAT_MODEL.md](WHATSAPP_THREAT_MODEL.md).

## Extend

- Swap `brain.process_message` for your agent / business rules.
- Register new flow handlers in `services/flows.py`.
- Add callback prefixes in `services/callbacks.py`.
- Use `send_template_message(...)` for approved templates outside the free-form window.
- Wire real Gemini (or other) media describe/transcribe in `llm_client.py` when `GEMINI_ENABLED=true`.

This starter intentionally has **no** product domain (tasks, CRM, billing), **no** multi-tenant Embedded Signup / usage metering, and **no** mobile push / Apple / Google / RevenueCat.
