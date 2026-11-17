"""Unit tests for username / display-name helpers."""

from __future__ import annotations

import unittest

from app.accounts.utils import validate_display_name, validate_username


class ProfileValidationTests(unittest.TestCase):
    def test_username_ok(self) -> None:
        self.assertEqual(validate_username("Ada_42"), "ada_42")

    def test_username_rejects_bad_chars(self) -> None:
        with self.assertRaises(ValueError):
            validate_username("Ada-42")

    def test_display_name_collapses_whitespace(self) -> None:
        self.assertEqual(validate_display_name("  Ada   Lovelace  "), "Ada Lovelace")


if __name__ == "__main__":
    unittest.main()
