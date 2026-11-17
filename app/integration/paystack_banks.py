"""Load Paystack bank list from bundled JSON (no live List Banks API calls)."""

import json
from functools import lru_cache
from pathlib import Path

from app.config.settings import settings


def _default_banks_json_path() -> Path:
    return (
        Path(__file__).resolve().parent.parent.parent
        / "data"
        / "paystack-banks-response-april-2nd-2026.json"
    )


def _banks_path_str() -> str:
    if settings.PAYSTACK_BANKS_JSON_PATH:
        return settings.PAYSTACK_BANKS_JSON_PATH
    return str(_default_banks_json_path())


@lru_cache(maxsize=8)
def _load_banks_raw(cache_key: str) -> list[dict]:
    with open(cache_key, encoding="utf-8") as fh:
        payload = json.load(fh)
    data = payload.get("data")
    if not isinstance(data, list):
        return []
    return data


def paystack_banks_raw() -> list[dict]:
    """Return the ``data`` array from the Paystack-style banks JSON file."""
    return _load_banks_raw(_banks_path_str())


def list_banks_for_picker() -> list[dict[str, object]]:
    """Active Nigerian banks for dropdowns, sorted by name."""
    rows: list[dict[str, object]] = []
    for item in paystack_banks_raw():
        if not isinstance(item, dict):
            continue
        if not item.get("active"):
            continue
        if item.get("is_deleted"):
            continue
        if item.get("country") != "Nigeria":
            continue
        bank_id = item.get("id")
        name = item.get("name")
        code = item.get("code")
        if bank_id is None or not name or not code:
            continue
        rows.append(
            {
                "id": int(bank_id),
                "name": str(name),
                "code": str(code),
                "slug": item.get("slug") if item.get("slug") else None,
            }
        )
    rows.sort(key=lambda r: str(r["name"]).lower())
    return rows


@lru_cache(maxsize=1)
def _bank_code_to_display_name() -> dict[str, str]:
    return {str(r["code"]): str(r["name"]) for r in list_banks_for_picker()}


def get_bank_name_for_code(code: str) -> str | None:
    """Resolve bank display name from bundled Paystack bank list, if present."""
    if not code or not str(code).strip():
        return None
    return _bank_code_to_display_name().get(str(code).strip())
