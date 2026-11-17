"""Contact Schemas"""

from pydantic import BaseModel, EmailStr


class ContactForm(BaseModel):
    """
    Schema for contact form submission
    """
    full_name: str
    email: EmailStr
    description: str
