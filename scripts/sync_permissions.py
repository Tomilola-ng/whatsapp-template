#!/usr/bin/env python
"""Sync code-first permission registry rows into the database."""

import asyncio
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from tortoise import Tortoise

from app.access.permission_registry import sync_permissions
from app.access.services import seed_default_access_roles
from app.config.settings import settings


async def _run() -> None:
    await Tortoise.init(config=settings.TORTOISE_CONFIG)
    try:
        created = await sync_permissions()
        await seed_default_access_roles()
        print(f"Synced permissions ({created} newly created). Seeded default access roles.")
    finally:
        await Tortoise.close_connections()


def main() -> None:
    asyncio.run(_run())


if __name__ == "__main__":
    main()
