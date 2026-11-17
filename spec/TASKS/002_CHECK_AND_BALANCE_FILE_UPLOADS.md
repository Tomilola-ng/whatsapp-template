# Task 002 - Check And Balance File Uploads

## Purpose

Verify file upload, ownership, and listing behavior matches the starter contract. Ensure uploads cannot attach to other users' assets.

## Source Of Truth

`spec/API.md` files section; `docs/TEMPLATE_SCHEMA.dbml` (`fileasset`); live `app/base` code.

## Depends On

001.

## Scope

- Audit `POST /api/v1/base/files` authentication and owner assignment.
- Audit local-only `GET /api/v1/base/files` pagination and owner scoping.
- Confirm allowed MIME types and size limits are enforced in services.
- Ensure profile image upload reuses ownership rules.

## Out Of Scope

CDN configuration, virus scanning, or product-specific media pipelines.

## Database Tables

`fileasset`.

## Backend Files To Review

`app/base/routes.py`, `services/`, `models.py`, `schemas.py`; `app/accounts/services/` (`update_user_image`).

## Business Rules

- Only the authenticated active owner may upload and list their files.
- Presigned URLs do not grant mutation rights.
- Local global listing must never expose other users' assets.

## Completion Checklist

- [ ] Upload requires active authentication.
- [ ] New rows record owner when the starter supports owner-aware uploads.
- [ ] Listing is owner-scoped and local-only where documented.

## Schema Gap

Owner column on `fileasset` — align model, DBML, and migrations via task 006 if changed.
