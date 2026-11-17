"""Contact Routes"""

from fastapi import APIRouter, Request, status

from app.base.rate_limit import limiter
from app.config.settings import settings
from app.contact.schemas import ContactForm
from app.contact.services import submit_contact_form

router = APIRouter(prefix="/contact", tags=["Contact"])


@router.post("/", status_code=status.HTTP_200_OK)
@limiter.limit(settings.RATE_LIMIT_CONTACT)
async def contact_us(request: Request, data: ContactForm):
    """
    Public endpoint for contact form submissions.
    Sends an email to the configured project inbox.
    """
    return await submit_contact_form(data)
