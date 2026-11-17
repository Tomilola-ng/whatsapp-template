"""Accounts schemas"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from app.base.schemas import FileOut
from app.config.pagination import PaginatedResponse


# Account Schemas
class AccountCreatePydantic(BaseModel):
    """Email/password registration."""

    first_name: str = Field(min_length=1, max_length=255)
    last_name: str = Field(min_length=1, max_length=255)
    phone_number: Optional[str] = Field(None, max_length=20)
    email: EmailStr
    password: str = Field(min_length=1, max_length=255)
    state: Optional[str] = Field(None, max_length=255)


class AccountRead(BaseModel):
    """Account read schema (includes image when loaded)."""
    id: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    display_name: Optional[str] = None
    username: Optional[str] = None
    user_type: str
    email: Optional[str] = None
    status: str
    created_at: datetime
    state: Optional[str] = None
    phone_number: Optional[str] = None
    image: Optional[FileOut] = None

    class Config:
        """Pydantic model configuration"""
        from_attributes = True


class AccountAdminDetail(AccountRead):
    """Admin detailed account view (same shape as AccountRead until admin-only fields exist)."""


class AccountListResponse(PaginatedResponse[AccountRead]):
    """Schema for list response"""


class LoginUserSchema(BaseModel):
    """User login credentials."""
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    """Login token response payload."""
    access: str
    refresh: str
    user: AccountRead


class RefreshTokenRequest(BaseModel):
    """Refresh token request payload."""
    refresh_token: str


class RefreshTokenResponse(BaseModel):
    """Refresh token response payload."""
    access: str


class EmailVerificationSchema(BaseModel):
    """Email + OTP for verification."""
    email: EmailStr
    otp_code: Optional[str] = Field(None, max_length=6)


class ForgetPasswordSchema(BaseModel):
    """Email to request password reset."""
    email: EmailStr


class ValidatePasswordSchema(BaseModel):
    """Single password field for validation."""
    password: str


class NewPasswordSchema(BaseModel):
    """Complete password reset using the 6h reset token (Bearer) from verify-reset-otp."""
    new_password: str
    confirm_password: str


class ResetPasswordOtpVerifySchema(BaseModel):
    """Email and OTP for `/auth/verify-reset-otp` before receiving the short-lived reset JWT."""
    email: EmailStr
    otp_code: str = Field(..., min_length=1, max_length=6)


class ChangePasswordSchema(BaseModel):
    """Change password with Old Password."""
    old_password: str
    new_password: str
    confirm_password: str


class ExchangeSetupCodeSchema(BaseModel):
    """Opaque admin setup code exchanged for a short-lived password-setup JWT."""

    code: str = Field(..., min_length=8, max_length=256)
    email: EmailStr


class AccountUpdate(BaseModel):
    """Schema for updating user profile."""
    first_name: Optional[str] = Field(None, min_length=1, max_length=255)
    last_name: Optional[str] = Field(None, min_length=1, max_length=255)
    phone_number: Optional[str] = Field(None, min_length=1, max_length=255)
    state: Optional[str] = Field(None, min_length=1, max_length=255)
    display_name: Optional[str] = Field(None, min_length=1, max_length=80)
    username: Optional[str] = Field(None, min_length=3, max_length=32)


class AccountPreferencesUpdate(BaseModel):
    push_enabled: Optional[bool] = None
    email_notifications_enabled: Optional[bool] = None
    marketing_email_enabled: Optional[bool] = None
    email_login_mfa_enabled: Optional[bool] = None


class AccountPreferencesRead(BaseModel):
    id: str
    account_id: str
    push_enabled: bool
    email_notifications_enabled: bool
    marketing_email_enabled: bool
    email_login_mfa_enabled: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class VerifyLoginOtpSchema(BaseModel):
    """Email and OTP for `/auth/verify-login-otp` after password sign-in with MFA."""

    email: EmailStr
    otp_code: str = Field(..., min_length=1, max_length=6)


class AccountDeleteRequest(BaseModel):
    confirm: bool = False
    confirmation_phrase: Optional[str] = None
    reason: Optional[str] = Field(None, max_length=500)
