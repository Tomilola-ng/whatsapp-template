## Prompt: WhatsApp API boilerplate (orchestrated, domain-agnostic)

**Goal:** Scaffold a **production-style WhatsApp Business webhook integration** similar in architecture to an existing FastAPI + `pywa_async` app, but **without any product-specific domain** (no jobs, payments, onboarding to a particular product, etc.). Everything should be generic placeholders and clear extension points.

**Tech choices:**

- Python 3.11+
- **FastAPI** as the HTTP server
- **`pywa_async.WhatsApp`** attached to the FastAPI app for webhooks (verify token, callback URL, phone_id, token, app_id, app_secret, business_account_id as needed)
- **Pydantic v2** for request/response and flow payloads
- Optional: a thin **settings** module (e.g. `pydantic-settings`) for `WA_*`, `LLM_PROVIDER`, API keys

**Directory layout (required):** a package directory named **`whatsapp/`** containing exactly these modules (names matter):

| File | Responsibility |
|------|----------------|
| **`entry.py`** | **Message orchestration entrypoint.** Single async function, e.g. `entry_point(text: str, msisdn: str, *, context: dict \| None) -> WhatsAppLogicResponse`. This is where inbound **normalized text** lands after audio/image handling. It should call a **stub** “brain” (e.g. echo, or a placeholder async `process_message`)—no real business rules. Must return a **`WhatsAppLogicResponse`** (see `schemas.py`). |
| **`replies.py`** | **Outbound orchestration.** Functions that take `WhatsAppLogicResponse` + `WhatsApp` client + `msisdn` and perform the right `pywa` calls: plain text, buttons, **flow buttons** (`FlowButton`), etc. Keep this the **only** place that knows how to map structured logic output to WhatsApp API sends. |
| **`callbacks.py`** | **`@wa.on_callback_button()`** handlers (and similar if needed). Parse `callback_data`, route to small handler functions. **No** giant inline logic—delegate to named functions. Use prefix constants and safe parsing; unknown callbacks → polite fallback message. |
| **`flows.py`** | **Flow completion orchestration.** `async def handle_flow_completion(wa_client, completion) -> WhatsAppLogicResponse` (or equivalent signature matching `pywa`). Maintain a **registry**: detect which flow was completed (e.g. by screen field signatures or `flow_token`), dispatch to a handler, return a response for `replies.py` to send. Include **one example** generic flow handler (e.g. “contact form” with fake fields) and a TODO for real persistence. |
| **`shared.py`** | **Shared utilities:** optional singleton WhatsApp sender client for non-webhook code paths, `format_whatsapp_message` (markdown/escapes → WhatsApp-friendly text), msisdn normalization helpers, logging helpers—**no** domain models. If chat persistence exists in the real app, expose a **optional** hook interface here (protocol/callback) so the boilerplate stays generic. |
| **`schemas.py`** | Pydantic models: `WhatsAppLogicResponse` (`reply`, optional `flow` enum or string id, optional `flow_buttons`, etc.), test API models, flow payload models for the example flow. **Enum** for flow ids should be minimal (`GENERIC_CONTACT = "generic_contact"`). |
| **`routes.py`** | FastAPI `APIRouter` for dev/testing: e.g. `POST /whatsapp/test-message` that uses `shared.send_user_message` (or equivalent). |
| **`llm_client.py`** | Abstract `LLMClient` + stub / optional **Gemini** placeholder for **`describe_image`** and **`transcribe_audio`**. Factory `get_llm_client()` driven by config (`GEMINI_ENABLED`). |
| **`describe_image.py`** | `async def describe_image(wa_client, image_id, caption=None) -> str`: download media via `wa_client`, base64, delegate to `llm_client`. |
| **`transcribe_audio.py`** | `async def transcribe_audio(wa_client, audio_id) -> str`: temp file, delegate to `llm_client`. |
| **`__init__.py`** | Re-export public symbols (`router`, `entry_point`, `handle_flow_completion`, etc.). |

**Application wiring (orchestration requirements):**

1. **`main.py` (or app factory)** must:
   - Create FastAPI app and `WhatsApp(server=app, ...)`.
   - Register **`whatsapp.routes.router`** under a prefix (e.g. `/api/v1`).
   - Implement **one** `@wa.on_message()` handler that acts as the **pipeline**:
     - Resolve `msisdn` / wa_id.
     - Branch by `MessageType`: **text** → pass body to `entry_point`; **audio** → `transcribe_audio` then `entry_point`; **image** → `describe_image` then optionally prepend caption and pass to `entry_point` (document the chosen behavior).
     - Pass the `WhatsAppLogicResponse` to **`replies.send_reply`** (or similarly named) from `replies.py`.
   - Register **`@wa.on_callback_button()`** in **`callbacks.py`** via a function `register_callback_handlers(wa: WhatsApp)` **or** import side-effects clearly documented—prefer explicit registration.
   - Register **`@wa.on_flow_completion()`** (or the library’s equivalent) to call **`flows.handle_flow_completion`** then **`replies`**.

2. **Error handling:** At pipeline boundaries, catch exceptions, log stack traces, return a **generic user-facing** error string from `entry`/`flows`, never raw exceptions.

3. **Configuration:** All secrets and flow IDs via env/settings; **comment** which Meta / WhatsApp Flow JSON fields must align with `flows.py` detection keys.

4. **Dependencies:** `pyproject.toml` with `fastapi`, `uvicorn`, `pywa`, `pydantic-settings`, `httpx`, etc. Optional LLM SDKs only when you wire a real media client.

**Explicit non-goals:**

- No real database models unless a **single optional** `TODO` interface is shown.
- No third-party payment, CRM, or vertical-specific copy.
- No hardcoded brand name; use “Assistant” or “Bot” in strings.

**Deliverable:** The full **`whatsapp/`** package with the files above, minimal **`main.py`** demonstrating registration, a **README** section (short) describing the webhook URL, env vars, and the message → entry → replies flow diagram in text—plus how to add a new flow handler in `flows.py`.
