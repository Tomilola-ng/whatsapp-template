#!/usr/bin/env python3
"""Verify live FastAPI routes vs ENDPOINTS_CHECKLIST.md.

Exits 0 when every checklist path/method pair is registered and every live
product route is documented; exits 1 and prints gaps otherwise.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

_e2e_env = ROOT / ".env.e2e"
if _e2e_env.exists():
    for line in _e2e_env.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)

CHECKLIST = ROOT / "app/base/handoff/ENDPOINTS_CHECKLIST.md"
CHECKLIST_LINE = re.compile(
    r"^-\s+\[x\]\s+`(GET|POST|PUT|PATCH|DELETE)\s+(/api/v1/[^`]+)`",
    re.IGNORECASE,
)

# Intentionally registered but outside the starter checklist.
DOCUMENTED_EXTRAS: set[tuple[str, str]] = {
    ("GET", "/api/v1/dev/outbox"),
    ("GET", "/api/v1/auth/preferences"),
    ("PATCH", "/api/v1/auth/preferences"),
    ("DELETE", "/api/v1/auth/account"),
    ("GET", "/api/v1/admin/audit-logs"),
    ("POST", "/api/v1/admin/notifications/broadcast"),
    ("GET", "/api/v1/client-errors"),
    ("POST", "/api/v1/client-errors"),
    ("GET", "/api/v1/notifications/staff"),
    ("GET", "/api/v1/notifications/stream"),
    ("GET", "/api/v1/notifications/unread-count"),
    ("POST", "/api/v1/notifications/mark-all-read"),
}


def normalize_path(path: str) -> str:
    """Collapse {param} segments for set comparison."""
    return re.sub(r"\{[^}]+\}", "{id}", path.rstrip("/") or "/")


def load_checklist() -> set[tuple[str, str]]:
    if not CHECKLIST.exists():
        raise SystemExit(f"Missing checklist: {CHECKLIST}")
    pairs: set[tuple[str, str]] = set()
    for line in CHECKLIST.read_text().splitlines():
        match = CHECKLIST_LINE.match(line.strip())
        if match:
            method, path = match.group(1).upper(), match.group(2)
            pairs.add((method, normalize_path(path)))
    return pairs


def load_live_routes() -> set[tuple[str, str]]:
    from main import app

    prefix = "/api/v1"
    live: set[tuple[str, str]] = set()
    for route in app.routes:
        methods = getattr(route, "methods", None) or set()
        path = getattr(route, "path", None)
        if not path or not methods:
            continue
        if not path.startswith(prefix):
            continue
        for method in methods:
            if method in {"HEAD", "OPTIONS"}:
                continue
            live.add((method.upper(), normalize_path(path)))
    return live


def main() -> int:
    checklist = load_checklist()
    documented = checklist | DOCUMENTED_EXTRAS
    live = load_live_routes()

    missing = sorted(checklist - live)
    undocumented = sorted(live - documented)

    print(f"Checklist entries: {len(checklist)}")
    print(f"Live /api/v1 routes: {len(live)}")

    if missing:
        print("\nChecklist paths not found on live app:")
        for method, path in missing:
            print(f"  - {method} {path}")

    if undocumented:
        print("\nLive routes missing from checklist/extras:")
        for method, path in undocumented:
            print(f"  - {method} {path}")

    if missing or undocumented:
        return 1
    print("\nAPI consistency check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
