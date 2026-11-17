"""Contact email templates."""

from typing import Dict

from app.base.email_template import (
    base_email_template as base_template,
    email_detail_table,
    email_escape,
    email_panel,
)


def new_contact_submission_email(context: Dict) -> str:
    """Generate HTML email for a new contact form submission."""
    content = f"""
        <h1 class="mail-title">New contact form submission</h1>
        <p class="mail-lead">You have received a new message from the contact form.</p>
        {email_panel(
            "info",
            "Contact details",
            email_detail_table(
                [
                    ("Name", str(context.get("full_name") or "")),
                    ("Email", str(context.get("email") or "")),
                ]
            ),
        )}
        {email_panel(
            "neutral",
            "Message",
            f'<p class="mail-text mail-mb-0">{email_escape(context.get("description"))}</p>',
        )}
        """
    return base_template("New Contact Form Submission", content)
