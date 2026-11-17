# WhatsApp FastAPI 2026 Template

Lean FastAPI starter for **WhatsApp bots and AI assistants**:

- PyWa webhook pipeline (`app/whatsapp`) with stub brain you replace per product
- email/OTP auth and in-app notifications (SSE)
- Tortoise ORM plus Aerich migrations
- reusable service-layer structure
- dual OpenAPI docs (app + admin)
- in-app notifications and contact endpoint
- audit/client-error logging
- optional Cloudflare R2, Resend, Paystack, Prembly
- local shell/curl E2E smoke tests

## What Is Included

- `app/whatsapp`: Cloud API attach, inbound handlers, entry → brain → replies, flows/callbacks, status + local test routes
- `app/accounts`: registration, login, OTP, password reset, profile
- `app/access`: permissions, access roles, JWT guards
- `app/base`: health, files, shared helpers
- `app/records`: in-app notifications and OTPs
- `app/contact`: public contact form
- `app/config`: settings, DB, routers
- `startapp.py`: module scaffolder

See [docs/WHATSAPP_INTEGRATION.md](docs/WHATSAPP_INTEGRATION.md) for webhook setup.

## Quick Start

1. Install Python `3.13+` and `uv`.
2. `cp .env.sample .env` then `uv run python scripts/generate_secrets.py --write .env`
3. `uv sync`
4. `uv run aerich upgrade`
5. `uv run fastapi dev main.py`
6. Smoke: `GET http://localhost:8000/api/v1/health`

Leave `WHATSAPP_ENABLED=false` until Meta credentials are ready. First boot must stay green without WhatsApp.

## WhatsApp smoke (when enabled)

```text
GET  /api/v1/whatsapp/status
POST /api/v1/whatsapp/test-agent   # local/staging — runs entry_point without Meta
POST /api/v1/whatsapp/test-message # local/staging — outbound Cloud API send
```

Webhook path (configure in Meta): `/api/v1/webhooks/whatsapp`

## Customize the bot

Edit `app/whatsapp/brain.py` (`process_message`). That is the intentional product extension point.

## Shell E2E Smoke

```bash
cp .env.e2e.example .env.e2e
docker compose up -d
uv run aerich upgrade
bash app/base/tests/run_all.sh .env.e2e
```

## Ops

- Generate secrets: `uv run python scripts/generate_secrets.py --write .env`
- Create admin: `uv run python scripts/create_admin.py --email admin@example.com`
- Sync permissions after adding codenames: `uv run python scripts/sync_permissions.py`

## Docs

- [docs/WHATSAPP_INTEGRATION.md](docs/WHATSAPP_INTEGRATION.md)
- [docs/WHATSAPP_THREAT_MODEL.md](docs/WHATSAPP_THREAT_MODEL.md)
- [docs/CBV_GUIDE.md](docs/CBV_GUIDE.md)
- [docs/SETUP_GUIDE.md](docs/SETUP_GUIDE.md)
- [docs/API_KEYS_GUIDE.md](docs/API_KEYS_GUIDE.md)
- [AGENTS.md](AGENTS.md)
