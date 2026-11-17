# Client Error Logging Handoff

Clients may send `POST /api/v1/client-errors/` with `message` plus optional
`flow`, `screen`, `email`, `platform`, `app_version`, `client_timestamp`,
`stack`, and JSON `metadata`. An optional bearer token links the current account.

Keep payloads free of secrets and unnecessary personal data. The server performs
deep redaction as a second line of defense. Local and staging list access is open
for development; production `GET /api/v1/client-errors/` requires
`client_errors.read`.
