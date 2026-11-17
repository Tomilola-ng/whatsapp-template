# WhatsApp threat model (single-WABA starter)

| Threat | Mitigation in this repo |
| --- | --- |
| Webhook forgery | PyWa `validate_updates` + `WHATSAPP_APP_SECRET`; verify token on challenge |
| Credential leakage | Tokens only in env; status/test routes never return secrets |
| Media SSRF / bombs | Host allowlist, MIME allowlist, `WHATSAPP_MEDIA_MAX_BYTES` |
| Transient Graph failures | Error classification + bounded soft retry (no durable resend queue) |
| Free-form outside 24h window | In-memory service-window helpers; forks should gate template vs free-form |
| Duplicate inbound | Short process-local dedupe on text; PyWa `skip_duplicate_updates` |
| Test endpoint abuse | `test-message` / `test-agent` refused in production |

Out of scope for this starter (product forks may add): multi-tenant IDOR controls, durable outbound attempt queues, usage caps, Embedded Signup credential vaults.

Residual ops risks: live Meta token rotation, public webhook URL exposure, PaaS callback auto-register races (keep auto-register off).
