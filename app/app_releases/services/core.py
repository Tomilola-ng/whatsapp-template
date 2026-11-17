from __future__ import annotations

import re
from datetime import datetime, timezone

from app.app_releases.enums import AppPlatform
from app.app_releases.models import AppRelease
from app.base.http_errors import api_error

SEMVER = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$"
)


def parse_platform(raw: str) -> AppPlatform:
    try:
        return AppPlatform(raw.upper())
    except ValueError as exc:
        raise api_error(
            422, "unsupported_app_platform", "App platform is not supported."
        ) from exc


def validate_version(value: str) -> str:
    if not SEMVER.fullmatch(value):
        raise api_error(
            422, "invalid_app_version", "Version must be valid semantic versioning."
        )
    return value


async def latest_release(platform: AppPlatform) -> AppRelease | None:
    now = datetime.now(timezone.utc)
    return (
        await AppRelease.filter(
            platform=platform,
            is_active=True,
            published_at__isnull=False,
            published_at__lte=now,
        )
        .order_by("-build_number", "-published_at", "-id")
        .first()
    )


async def update_policy(platform_raw: str, version: str, build: int) -> dict:
    platform = parse_platform(platform_raw)
    validate_version(version)
    if build <= 0:
        raise api_error(422, "invalid_build_number", "Build number must be positive.")
    release = await latest_release(platform)
    if not release:
        return {
            "platform": platform.value,
            "current_version": version,
            "current_build": build,
            "latest_version": version,
            "latest_build": build,
            "minimum_supported_version": version,
            "minimum_supported_build": build,
            "update_available": False,
            "update_required": False,
            "title": None,
            "message": None,
            "store_url": None,
            "published_at": None,
            "check_after_seconds": 86400,
        }
    available = build < release.build_number
    required = available and (
        build < release.minimum_supported_build_number or release.force_update
    )
    return {
        "platform": platform.value,
        "current_version": version,
        "current_build": build,
        "latest_version": release.version_name,
        "latest_build": release.build_number,
        "minimum_supported_version": release.minimum_supported_version_name,
        "minimum_supported_build": release.minimum_supported_build_number,
        "update_available": available,
        "update_required": required,
        "title": release.update_title,
        "message": release.update_message,
        "store_url": release.store_url,
        "published_at": release.published_at,
        "check_after_seconds": 86400,
    }


def validate_release_values(values: dict) -> None:
    validate_version(values["version_name"])
    validate_version(values["minimum_supported_version_name"])
    if values["minimum_supported_build_number"] > values["build_number"]:
        raise api_error(
            422,
            "invalid_release",
            "Minimum supported build cannot exceed release build.",
        )
    if not str(values["store_url"]).startswith("https://"):
        raise api_error(422, "invalid_release", "Store URL must use HTTPS.")
