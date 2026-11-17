#!/usr/bin/env python
import argparse
import asyncio
import importlib
import sys
from pathlib import Path

from tortoise import Tortoise

# Ensure project root is on sys.path (same pattern as other scripts)
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config.settings import settings  # noqa: E402


def import_model(path: str):
    """
    Import a model class from a fully qualified path, e.g. 'app.questions.models.Question'.
    """
    module_path, class_name = path.rsplit(".", 1)
    module = importlib.import_module(module_path)
    return getattr(module, class_name)


async def run(model_path: str) -> None:
    """
    Delete all rows for a given model, e.g. "app.questions.models.Question".
    """
    await Tortoise.init(config=settings.TORTOISE_CONFIG)
    try:
        the_model = import_model(model_path)
        count = await the_model.all().count()
        await the_model.all().delete()
        print(f"Deleted {count} rows from {model_path}")
    finally:
        await Tortoise.close_connections()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Delete all rows for a given Tortoise model."
    )
    parser.add_argument(
        "model",
        help='Fully-qualified model, e.g. "app.questions.models.Question"',
    )
    args = parser.parse_args()
    asyncio.run(run(args.model))


if __name__ == "__main__":
    main()
