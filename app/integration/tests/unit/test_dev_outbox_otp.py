"""Dev outbox OTP extraction (FRM-039 E2E harness fix)."""

from __future__ import annotations

import unittest

from app.integration.dev_outbox import extract_otp_from_body


class TestDevOutboxOtpExtraction(unittest.TestCase):
    def test_ignores_css_hex_and_reads_strong_otp(self) -> None:
        body = """
        <style>body { color: #222222; }</style>
        <h3>Your OTP Code</h3>
        <p><strong>847291</strong></p>
        """
        self.assertEqual(extract_otp_from_body(body), "847291")

    def test_skips_hash_prefixed_digits_without_strong(self) -> None:
        body = "theme #222222 then code 998877 ends"
        self.assertEqual(extract_otp_from_body(body), "998877")


if __name__ == "__main__":
    unittest.main()
