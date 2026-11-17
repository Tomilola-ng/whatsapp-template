# Task 006 - Migrations And Schema Baseline

## Purpose

Establish a checked-in Aerich migration history for the starter schema and enforce migration discipline for all future schema changes.

## Source Of Truth

`spec/DATABASE.md`; `docs/TEMPLATE_SCHEMA.dbml`; `pyproject.toml` `[tool.aerich]`; `migrations/` directory.

## Depends On

001–005 (models must reflect auth, OTP hashing, and setup codes before baselining).

## Scope

- Ensure Aerich is configured with `app.config.database.TORTOISE_ORM`.
- Generate and check in starter migration history for supported starter tables (`accounts`, `otps`, `password_setup_codes`, `fileasset`, `notifications`, access-control joins, platform tables). Legacy migrations may still mention removed mobile tables until a fork generates a cleanup migration.
- Document the operator workflow in `spec/DATABASE.md` and `AGENTS.md`.
- Add `scripts/migrate.py` wrapper with clear warnings.

## Critical Rules

1. Use **`uv run aerich migrate`** and **`uv run aerich upgrade`** ONLY.
2. **NEVER** manually create or edit files under `migrations/models/`.
3. Check in generated Aerich history for the starter schema.
4. Review generated SQL before applying to PostgreSQL staging/production.

## Commands

```powershell
# Fresh database
uv run aerich init -t app.config.database.TORTOISE_ORM
uv run aerich init-db

# Existing checkout
uv run aerich upgrade

# After model changes
uv run aerich migrate --name your_change_description
uv run aerich upgrade
```

Or:

```powershell
uv run python scripts/migrate.py
```

## Out Of Scope

Data backfill scripts for product-specific domains, fake migration baselines on populated DBs.

## Completion Checklist

- [ ] `migrations/models/` contains only Aerich-generated files.
- [ ] Fresh `aerich upgrade` succeeds against SQLite and is rehearsed on PostgreSQL.
- [ ] `docs/TEMPLATE_SCHEMA.dbml` matches registered Tortoise models.
- [ ] `AGENTS.md` and `spec/DATABASE.md` state the never-hand-edit rule prominently.

## Schema Gap

Any drift between DBML and models must be resolved by changing models and running `aerich migrate` — not by editing migration files.
