# Task 003 - Check And Balance Notifications

## Purpose

Verify notification listing, read state, SSE/unread helpers, and the public contact endpoint behave as documented.

## Source Of Truth

`spec/API.md` notifications and contact sections; `docs/TEMPLATE_SCHEMA.dbml`; live `app/records` and `app/contact` code.

## Depends On

001.

## Scope

- Audit notification list pagination and `unread_only` filtering.
- Confirm mark-read is owner-scoped.
- Confirm unread-count, mark-all-read, and SSE stream are owner-scoped.
- Audit contact form delivery and abuse controls (rate limit in task 004).

## Out Of Scope

WhatsApp outbound delivery, mobile device push providers, cross-worker SSE fan-out.

## Database Tables

`notifications` only (no `push_device_tokens` in this starter).

## Backend Files To Review

`app/records/routes.py`, `services/`, `models.py`; `app/contact/routes.py`, `services/`.

## Business Rules

- Users may only read and update their own notifications.
- Notification rows belong to the recipient account only.
- Contact submissions email the configured inbox without exposing internal errors.

## Completion Checklist

- [ ] Notification REST contract matches `spec/API.md`.
- [ ] Unread-count, mark-all-read, and SSE stream are owner-scoped.
- [ ] Contact endpoint documented and smoke-tested.

## Schema Gap

None for starter notification shape unless adding sequence IDs in a product fork.
