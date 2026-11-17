#!/usr/bin/env python3
"""Render all transactional email templates to static HTML for browser preview.

No API server or database required. Outputs files under ./email-preview/ and
optionally opens the index page in your default browser.

Usage:
    uv run python scripts/preview_emails.py
    uv run python scripts/preview_emails.py --no-open
"""

from __future__ import annotations

import argparse
import html
import sys
import webbrowser
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.accounts import emails as account_emails
from app.config.settings import settings
from app.contact import emails as contact_emails

OUTPUT_DIR = REPO_ROOT / "email-preview"


def _sample_contexts() -> list[tuple[str, str, callable]]:
    """Return (slug, label, builder) for every transactional template."""
    base = (settings.CLIENT_APP_URL or settings.APP_BASE_URL).rstrip("/")
    return [
        (
            "accounts-activate-otp",
            "Activate account (OTP)",
            lambda: account_emails.activate_account_otp(
                {"first_name": "Ada", "otp": "482916", "valid_minutes": 10}
            ),
        ),
        (
            "accounts-login-otp",
            "Sign-in verification (OTP)",
            lambda: account_emails.login_verification_otp(
                {"first_name": "Ada", "otp": "739204", "valid_minutes": 10}
            ),
        ),
        (
            "accounts-forgot-password-otp",
            "Forgot password (OTP)",
            lambda: account_emails.forgot_password_request_otp(
                {"first_name": "Ada", "otp": "105837", "valid_minutes": 15}
            ),
        ),
        (
            "accounts-password-reset-success",
            "Password reset successful",
            lambda: account_emails.password_reset_success(
                {"first_name": "Ada", "location": "Lagos, NG"}
            ),
        ),
        (
            "accounts-password-changed",
            "Password changed",
            lambda: account_emails.password_changed_success(
                {"first_name": "Ada", "location": "Lagos, NG"}
            ),
        ),
        (
            "accounts-welcome",
            "Welcome",
            lambda: account_emails.welcome_email(
                {"first_name": "Ada", "full_name": "Ada Okonkwo"}
            ),
        ),
        (
            "accounts-admin-invite",
            "Admin invite",
            lambda: account_emails.admin_invite_email(
                {
                    "first_name": "George",
                    "setup_link": f"{base}/set-password?code=preview-admin-invite",
                    "expires_in_hours": 2,
                }
            ),
        ),
        (
            "accounts-admin-upgrade",
            "Admin upgrade",
            lambda: account_emails.admin_upgrade_email(
                {
                    "first_name": "George",
                    "setup_link": f"{base}/set-password?code=preview-admin-upgrade",
                    "expires_in_hours": 2,
                }
            ),
        ),
        (
            "contact-new-submission",
            "Contact form submission",
            lambda: contact_emails.new_contact_submission_email(
                {
                    "full_name": "Jane Merchant",
                    "email": "jane@example.com",
                    "description": "I would like to learn more about your product.",
                }
            ),
        ),
    ]


def _index_html(entries: list[tuple[str, str]]) -> str:
    rows = "\n".join(
        f'      <li><a href="{html.escape(slug)}.html">{html.escape(label)}</a></li>'
        for slug, label in entries
    )
    brand = html.escape(settings.display_brand_name)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{brand} — Email previews</title>
  <style>
    body {{
      font-family: Inter, system-ui, sans-serif;
      background: #eef2f7;
      color: #111827;
      margin: 0;
      padding: 32px 20px;
    }}
    main {{
      max-width: 640px;
      margin: 0 auto;
      background: #fff;
      border: 1px solid #e5e7eb;
      border-radius: 16px;
      padding: 28px 32px;
      box-shadow: 0 8px 24px rgba(17, 24, 39, 0.06);
    }}
    h1 {{ font-size: 1.5rem; margin: 0 0 8px; }}
    p {{ color: #6b7280; margin: 0 0 20px; line-height: 1.5; }}
    ul {{ margin: 0; padding-left: 1.25rem; line-height: 1.8; }}
    a {{ color: #111827; font-weight: 600; }}
    code {{
      background: #f8fafc;
      padding: 2px 6px;
      border-radius: 4px;
      font-size: 0.9em;
    }}
  </style>
</head>
<body>
  <main>
    <h1>{brand} email previews</h1>
    <p>
      Static renders from <code>scripts/preview_emails.py</code>.
      Regenerate anytime — no API calls required.
    </p>
    <ul>
{rows}
    </ul>
  </main>
</body>
</html>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Render email templates to HTML files.")
    parser.add_argument(
        "--no-open",
        action="store_true",
        help="Write files only; do not open the index in a browser.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT_DIR,
        help=f"Output directory (default: {OUTPUT_DIR})",
    )
    args = parser.parse_args()
    out_dir = args.output.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    index_entries: list[tuple[str, str]] = []
    for slug, label, builder in _sample_contexts():
        path = out_dir / f"{slug}.html"
        path.write_text(builder(), encoding="utf-8")
        index_entries.append((slug, label))
        print(f"  wrote {path.relative_to(REPO_ROOT)}")

    index_path = out_dir / "index.html"
    index_path.write_text(_index_html(index_entries), encoding="utf-8")
    print(f"  wrote {index_path.relative_to(REPO_ROOT)}")
    print(f"\nOpen: file://{index_path}")

    if not args.no_open:
        webbrowser.open(index_path.as_uri())

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
