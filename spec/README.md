# Spec-Driven Development

This folder is the **agent reconciliation layer** for the FastAPI starter. Human-readable project specs live in `docs/`.

## Start Here (Humans)

| Doc | Purpose |
| --- | ------- |
| [`docs/PROJECT_SPEC.md`](../docs/PROJECT_SPEC.md) | What the project is, roles, scope, fork guidance |
| [`docs/FEATURES.md`](../docs/FEATURES.md) | Feature inventory with status |
| [`docs/API_CONTRACT.md`](../docs/API_CONTRACT.md) | HTTP contract for registered routes |
| [`docs/DATABASE_SPEC.md`](../docs/DATABASE_SPEC.md) | Schema, tables, Aerich rules |
| [`docs/IMPLEMENTATION_PLAN.md`](../docs/IMPLEMENTATION_PLAN.md) | Phased build and fork milestones |

## Agent Layer (This Folder)

| File | Purpose |
| ---- | ------- |
| `API.md` | Endpoint contract mirror — keep aligned with `docs/API_CONTRACT.md` |
| `AUTH_AND_PERMISSIONS.md` | Auth, RBAC, JWT claims, route guards |
| `DATABASE.md` | Schema mirror — keep aligned with `docs/DATABASE_SPEC.md` |
| `CHANGES.md` | Reconciliation ledger when spec and code diverge |
| `TASKS/` | Ordered check-and-balance task files (001–008) |

## How To Use It

1. Read `docs/PROJECT_SPEC.md` and `docs/IMPLEMENTATION_PLAN.md` before starting work.
2. Open the relevant task under `spec/TASKS/` for granular scope and checklists.
3. Update `docs/API_CONTRACT.md` and `docs/DATABASE_SPEC.md` when contracts change.
4. Mirror the same changes in `spec/API.md` / `spec/DATABASE.md` if agents rely on them.
5. Record intentional differences in `spec/CHANGES.md`.

## Principles

- Prefer the smallest change that satisfies the spec.
- Do not hand-edit files under `migrations/models/`; use Aerich only (see `docs/DATABASE_SPEC.md`).
- Keep the template generic — no product-specific domains in starter docs unless you are building a product fork.
- Mark feature status honestly in `docs/FEATURES.md` (`existing`, `planned`, `stubbed`).
