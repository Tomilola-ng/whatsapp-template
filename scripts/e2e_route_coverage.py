#!/usr/bin/env python3
"""Compare live /api/v1 routes against the last shell E2E request log.

Report-only by default (exit 0). Use --fail-under N to require a minimum
covered-operation count after run_all.sh.

Usage:
  bash app/base/tests/run_all.sh .env.e2e
  uv run python scripts/e2e_route_coverage.py
  uv run python scripts/e2e_route_coverage.py --markdown
  uv run python scripts/e2e_route_coverage.py --fail-under 100
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DEFAULT_LOG = ROOT / "app/base/tests/api-test.log"
METHOD_PATH_RE = re.compile(
    r"\b(GET|POST|PUT|PATCH|DELETE)\s+(/[^\s?(]+)",
    re.IGNORECASE,
)


def _load_e2e_env() -> None:
    env_file = ROOT / ".env.e2e"
    if not env_file.exists():
        return
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def load_registered_ops() -> set[tuple[str, str]]:
    from main import app

    ops: set[tuple[str, str]] = set()
    for route in app.routes:
        methods = getattr(route, "methods", None) or set()
        path = getattr(route, "path", None)
        if not path or not methods or not path.startswith("/api/"):
            continue
        for method in methods:
            if method in {"HEAD", "OPTIONS"}:
                continue
            ops.add((method.upper(), path))
    return ops


def parse_log_hits(log_path: Path) -> set[tuple[str, str]]:
    if not log_path.exists():
        raise SystemExit(
            f"Missing E2E log: {log_path}\n"
            "Run `bash app/base/tests/run_all.sh .env.e2e` first."
        )
    hits: set[tuple[str, str]] = set()
    for line in log_path.read_text(errors="ignore").splitlines():
        match = METHOD_PATH_RE.search(line)
        if not match:
            continue
        method = match.group(1).upper()
        raw = match.group(2).split("?", 1)[0]
        if raw.startswith("http"):
            continue
        hits.add((method, raw))
    return hits


def template_regex(template: str) -> re.Pattern[str]:
    parts: list[str] = []
    i = 0
    while i < len(template):
        if template[i] == "{":
            j = template.find("}", i)
            if j < 0:
                parts.append(re.escape(template[i]))
                i += 1
                continue
            parts.append(r"[^/]+")
            i = j + 1
        else:
            parts.append(re.escape(template[i]))
            i += 1
    return re.compile("^" + "".join(parts) + "$")


def match_hit(
    method: str, concrete: str, registered: set[tuple[str, str]]
) -> tuple[str, str] | None:
    candidates = [concrete]
    if not concrete.startswith("/api/"):
        prefix = concrete if concrete.startswith("/") else f"/{concrete}"
        candidates.append(f"/api/v1{prefix}")
    for tmpl_method, tmpl_path in registered:
        if tmpl_method != method:
            continue
        rx = template_regex(tmpl_path)
        for candidate in candidates:
            if rx.match(candidate):
                return tmpl_method, tmpl_path
    return None


def area_for(path: str) -> str:
    segs = [s for s in path.split("/") if s and not s.startswith("{")]
    if len(segs) >= 3 and segs[0] == "api" and segs[1].startswith("v"):
        return segs[2]
    return segs[0] if segs else "(root)"


def compute_coverage(
    registered: set[tuple[str, str]], hits: set[tuple[str, str]]
) -> tuple[set[tuple[str, str]], set[tuple[str, str]], list[tuple[str, str]]]:
    covered: set[tuple[str, str]] = set()
    unmatched: list[tuple[str, str]] = []
    for method, path in sorted(hits):
        matched = match_hit(method, path, registered)
        if matched:
            covered.add(matched)
        else:
            unmatched.append((method, path))
    uncovered = registered - covered
    return covered, uncovered, unmatched


def print_report(
    registered: set[tuple[str, str]],
    covered: set[tuple[str, str]],
    uncovered: set[tuple[str, str]],
    unmatched: list[tuple[str, str]],
    log_path: Path,
) -> None:
    print(f"E2E log: {log_path}")
    print(f"registered_ops={len(registered)}")
    print(f"covered_ops={len(covered)}")
    print(f"uncovered_ops={len(uncovered)}")
    if registered:
        pct = 100.0 * len(covered) / len(registered)
        print(f"coverage_pct={pct:.1f}")

    by_area = Counter(area_for(path) for _, path in uncovered)
    print("\nUncovered by area:")
    for area, count in by_area.most_common():
        print(f"  {area}: {count}")

    print("\nUncovered operations:")
    for method, path in sorted(uncovered):
        print(f"  {method:6} {path}")

    if unmatched:
        print(f"\nLog hits not matched to a registered /api route ({len(unmatched)}):")
        for method, path in unmatched[:20]:
            print(f"  {method:6} {path}")
        if len(unmatched) > 20:
            print(f"  ... +{len(unmatched) - 20} more")


def markdown_backlog(
    covered: set[tuple[str, str]],
    uncovered: set[tuple[str, str]],
) -> str:
    """Emit a markdown table fragment for docs/E2E_COVERAGE.md."""
    covered_by = defaultdict(set)
    uncovered_by = defaultdict(set)
    for method, path in covered:
        covered_by[area_for(path)].add((method, path))
    for method, path in uncovered:
        uncovered_by[area_for(path)].add((method, path))

    areas = sorted(set(covered_by) | set(uncovered_by))
    lines = [
        "| Area | Covered | Uncovered | Status |",
        "| --- | ---: | ---: | --- |",
    ]
    for area in areas:
        c = len(covered_by[area])
        u = len(uncovered_by[area])
        if u == 0:
            status = "covered"
        elif c == 0:
            status = "untested"
        else:
            status = "partial"
        lines.append(f"| `{area}` | {c} | {u} | {status} |")

    lines.append("")
    lines.append("### Uncovered operations (refresh via script)")
    lines.append("")
    lines.append("```")
    for method, path in sorted(uncovered):
        lines.append(f"{method:6} {path}")
    lines.append("```")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--log",
        type=Path,
        default=DEFAULT_LOG,
        help=f"Path to api-test.log (default: {DEFAULT_LOG})",
    )
    parser.add_argument(
        "--markdown",
        action="store_true",
        help="Print markdown backlog table instead of the text report",
    )
    parser.add_argument(
        "--fail-under",
        type=int,
        default=None,
        help="Exit 1 if covered_ops is below this count (optional CI gate)",
    )
    args = parser.parse_args()

    _load_e2e_env()
    registered = load_registered_ops()
    hits = parse_log_hits(args.log)
    covered, uncovered, unmatched = compute_coverage(registered, hits)

    if args.markdown:
        print(
            f"_Snapshot after last E2E log: "
            f"**{len(covered)}/{len(registered)}** operations covered "
            f"(`{args.log.name}`)._"
        )
        print()
        print(markdown_backlog(covered, uncovered))
    else:
        print_report(registered, covered, uncovered, unmatched, args.log)

    if args.fail_under is not None and len(covered) < args.fail_under:
        print(
            f"\nFAIL: covered_ops={len(covered)} < --fail-under {args.fail_under}",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
