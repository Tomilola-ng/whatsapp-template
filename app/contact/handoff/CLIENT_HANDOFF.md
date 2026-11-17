# Contact Client Handoff

Base path: `/api/v1/contact`

`POST /`

Public contact form endpoint. Body:

```json
{
  "full_name": "Ada Lovelace",
  "email": "ada@example.com",
  "description": "I need help with my account."
}
```

Returns `200` with a message when accepted. This route may be rate-limited; clients should handle 429 using `Retry-After`.
