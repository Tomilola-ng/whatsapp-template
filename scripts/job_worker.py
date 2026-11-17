#!/usr/bin/env python3
"""Simple background worker loop for starter maintenance jobs.

Usage:
    uv run python scripts/job_worker.py
    uv run python scripts/job_worker.py --once
    uv run python scripts/job_worker.py --interval 300
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("job_worker")


async def _run_once() -> dict:
    from tortoise import Tortoise

    from app.config.settings import settings
    from app.schedules.jobs.maintenance import run_maintenance

    await Tortoise.init(config=settings.TORTOISE_CONFIG)
    try:
        result = await run_maintenance()
        logger.info("maintenance complete: %s", result)
        return result
    finally:
        await Tortoise.close_connections()


async def _loop(interval_seconds: int) -> None:
    while True:
        try:
            await _run_once()
        except Exception:
            logger.exception("maintenance cycle failed")
        await asyncio.sleep(interval_seconds)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run one maintenance cycle and exit.",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=300,
        help="Seconds between cycles when looping (default: 300).",
    )
    args = parser.parse_args()
    if args.once:
        asyncio.run(_run_once())
    else:
        asyncio.run(_loop(max(30, args.interval)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
