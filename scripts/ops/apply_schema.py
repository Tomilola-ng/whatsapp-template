#!/usr/bin/env python3
"""Apply Aerich migrations and sync permissions.

Used as the container pre-start step. PostgreSQL advisory lock so the API and
worker can start together without racing ``aerich upgrade``.

Never generate migrations here. Never run ``aerich init-db`` against a
populated database.
"""

from __future__ import annotations

import asyncio
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

_LOCK_CLASS = 58818
_LOCK_ID = 2465


def _aerich_cmd() -> list[str]:
    local = ROOT / ".venv" / "bin" / "aerich"
    if local.exists():
        return [str(local), "upgrade"]
    return ["uv", "run", "aerich", "upgrade"]


def _run_upgrade() -> None:
    print("Applying Aerich migrations (aerich upgrade)…", flush=True)
    result = subprocess.run(_aerich_cmd(), cwd=ROOT)
    if result.returncode != 0:
        raise SystemExit(result.returncode)
    print("Aerich upgrade complete.", flush=True)


def _sync_permissions() -> None:
    script = ROOT / "scripts" / "sync_permissions.py"
    python = ROOT / ".venv" / "bin" / "python"
    cmd = [str(python) if python.exists() else sys.executable, str(script)]
    print("Syncing permission registry…", flush=True)
    result = subprocess.run(cmd, cwd=ROOT)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


async def _with_pg_lock(dsn: str) -> None:
    import asyncpg

    connect_dsn = dsn.replace("postgres://", "postgresql://", 1)
    conn = await asyncpg.connect(connect_dsn)
    try:
        await conn.execute("SELECT pg_advisory_lock($1, $2)", _LOCK_CLASS, _LOCK_ID)
        try:
            _run_upgrade()
            _sync_permissions()
        finally:
            await conn.execute("SELECT pg_advisory_unlock($1, $2)", _LOCK_CLASS, _LOCK_ID)
    finally:
        await conn.close()


def main() -> int:
    if os.environ.get("SKIP_SCHEMA_APPLY", "").lower() in {"1", "true", "yes"}:
        print("SKIP_SCHEMA_APPLY set; skipping migrations and permission sync.")
        return 0

    from app.config.settings import settings

    url = settings.DATABASE_URL
    if url.startswith("sqlite"):
        _run_upgrade()
        _sync_permissions()
        return 0

    asyncio.run(_with_pg_lock(url))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
