"""Contact Services"""

import asyncio

from app.config.settings import settings
from app.base.utils import send_email
from app.contact.emails import new_contact_submission_email
from app.contact.schemas import ContactForm


async def submit_contact_form(data: ContactForm):
    """
    Process contact form submission and send notification email to admin
    """
    context = {
        "full_name": data.full_name,
        "email": data.email,
        "description": data.description
    }

    # Generate email body
    email_body = new_contact_submission_email(context)

    # Send email to the configured inbox for this project.
    await asyncio.to_thread(
        send_email,
        subject="New Contact Form Submission",
        address=settings.CONTACT_RECIPIENT_EMAIL,
        body=email_body,
    )

    return {"message": "Message sent successfully"}
