"""Unit tests for app release policy helpers."""

from __future__ import annotations

import unittest
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException

from app.app_releases.enums import AppPlatform
from app.app_releases.services.core import parse_platform, update_policy, validate_version


class AppReleaseHelperTests(unittest.IsolatedAsyncioTestCase):
    def test_parse_platform(self) -> None:
        self.assertEqual(parse_platform("ios"), AppPlatform.IOS)

    def test_invalid_version(self) -> None:
        with self.assertRaises(HTTPException) as ctx:
            validate_version("1.2")
        self.assertEqual(ctx.exception.status_code, 422)

    async def test_update_policy_without_release(self) -> None:
        with patch(
            "app.app_releases.services.core.latest_release",
            new=AsyncMock(return_value=None),
        ):
            policy = await update_policy("ANDROID", "1.0.0", 10)
        self.assertFalse(policy["update_available"])
        self.assertFalse(policy["update_required"])
        self.assertEqual(policy["latest_build"], 10)


if __name__ == "__main__":
    unittest.main()
