#!/usr/bin/env python3
"""Export app and admin OpenAPI JSON for portal import or CI.

Usage:
    uv run python scripts/export_openapi.py
    uv run python scripts/export_openapi.py --out-dir docs/openapi
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("docs/openapi"),
        help="Directory for app.json and admin.json (default: docs/openapi)",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    from main import app
    from app.base.openapi import attach_dual_openapi

    attach_dual_openapi(app)
    app.state.openapi_app = None
    app.state.openapi_admin = None

    out_dir: Path = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    payloads = {
        "app.json": app.openapi_app(),  # type: ignore[attr-defined]
        "admin.json": app.openapi_admin(),  # type: ignore[attr-defined]
    }
    for name, schema in payloads.items():
        path = out_dir / name
        path.write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {path} ({len(schema.get('paths') or {})} paths)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
