"""Unit checks for audit metadata redaction and registry wiring."""

from __future__ import annotations

import unittest

from app.audit.utils import redact_audit_metadata
from app.base.utils import IDPrefix, generate_prefixed_id, make_id_default
from app.config.settings import settings


class TestAuditRedaction(unittest.TestCase):
    def test_redacts_sensitive_keys_nested(self) -> None:
        payload = {
            "reason": "manual adjust",
            "otp": "123456",
            "nested": {
                "authorization": "Bearer secret",
                "amount": 5,
                "api_key": "abc",
            },
            "prompt": "full user prompt",
            "safe_list": [{"token": "x"}, {"label": "ok"}],
        }
        cleaned = redact_audit_metadata(payload)
        assert cleaned is not None
        self.assertEqual(cleaned["reason"], "manual adjust")
        self.assertEqual(cleaned["otp"], "[REDACTED]")
        self.assertEqual(cleaned["prompt"], "[REDACTED]")
        self.assertEqual(cleaned["nested"]["amount"], 5)
        self.assertEqual(cleaned["nested"]["authorization"], "[REDACTED]")
        self.assertEqual(cleaned["nested"]["api_key"], "[REDACTED]")
        self.assertEqual(cleaned["safe_list"][0]["token"], "[REDACTED]")
        self.assertEqual(cleaned["safe_list"][1]["label"], "ok")
        # Original untouched
        self.assertEqual(payload["otp"], "123456")

    def test_none_metadata(self) -> None:
        self.assertIsNone(redact_audit_metadata(None))

    def test_rejects_non_object_metadata(self) -> None:
        with self.assertRaises(TypeError):
            redact_audit_metadata(["not", "a", "dict"])  # type: ignore[arg-type]


class TestAuditWiring(unittest.TestCase):
    def test_audit_model_registered(self) -> None:
        self.assertIn("app.audit.models", settings.tortoise_models)

    def test_audit_id_prefix(self) -> None:
        self.assertEqual(IDPrefix.AUDIT_LOG, "AUD")
        sample = generate_prefixed_id(IDPrefix.AUDIT_LOG)
        self.assertTrue(sample.startswith("AUD_"))
        default_fn = make_id_default(IDPrefix.AUDIT_LOG)
        self.assertEqual(default_fn.__name__, "id_default_aud")


if __name__ == "__main__":
    unittest.main()
