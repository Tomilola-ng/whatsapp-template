"""Accounts Routes"""

from typing import Annotated

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Request,
    Response,
    UploadFile,
    status,
)
from fastapi.security import HTTPBearer

from app.accounts import services as account_services
from app.accounts.auth import get_current_user, get_user_from_password_reset_token
from app.accounts.models import Account
from app.accounts.permissions import get_current_active_user
from app.accounts.schemas import (
    AccountCreatePydantic,
    AccountDeleteRequest,
    AccountPreferencesUpdate,
    AccountUpdate,
    ChangePasswordSchema,
    EmailVerificationSchema,
    ExchangeSetupCodeSchema,
    ForgetPasswordSchema,
    LoginUserSchema,
    NewPasswordSchema,
    RefreshTokenRequest,
    ResetPasswordOtpVerifySchema,
    VerifyLoginOtpSchema,
)
from app.base.rate_limit import limiter
from app.config.settings import settings
from app.records.enums import OTPPurpose


router = APIRouter(prefix="/auth", tags=["Accounts"])
security = HTTPBearer()


@router.post("/login", status_code=status.HTTP_200_OK)
@limiter.limit(settings.RATE_LIMIT_LOGIN)
async def login_user(
    request: Request,
    data: LoginUserSchema,
    background_tasks: BackgroundTasks,
):
    """Login user; return tokens, or login_pending when email MFA is enabled."""
    return await account_services.authenticate_user(data, background_tasks)


@router.post("/verify-login-otp", status_code=status.HTTP_200_OK)
@limiter.limit(settings.RATE_LIMIT_OTP_VERIFY)
async def verify_login_otp(request: Request, data: VerifyLoginOtpSchema):
    """Complete optional email MFA after password login."""
    return await account_services.verify_login_otp(data)


@router.post("/logout", status_code=status.HTTP_200_OK, dependencies=[Depends(security)])
async def logout_user(
    response: Response,
    current_user: Annotated[Account, Depends(get_current_user)],
):
    """Logout user; revoke JWTs for this account and clear cookies."""
    return await account_services.logout_user(response, current_user)


@router.post("/register", status_code=status.HTTP_201_CREATED)
@limiter.limit(settings.RATE_LIMIT_REGISTER)
async def register_user(
    request: Request,
    data: AccountCreatePydantic,
    background_tasks: BackgroundTasks,
):
    """Register new user; send activation email if email provided."""
    return await account_services.register_account(data, background_tasks)


@router.get("/current-user", status_code=status.HTTP_200_OK, dependencies=[Depends(security)])
async def get_current_user_data(
    current_user: Annotated[Account, Depends(get_current_active_user)],
):
    """Get authenticated user's profile."""
    return await account_services.get_current_user_profile(current_user)


@router.get("/me", status_code=status.HTTP_200_OK, dependencies=[Depends(security)])
async def get_current_user_alias(
    current_user: Annotated[Account, Depends(get_current_active_user)],
):
    """Canonical alias for the authenticated active account."""
    return await account_services.get_current_user_profile(current_user)


@router.patch("/update-user-image", status_code=status.HTTP_200_OK, dependencies=[Depends(security)])
async def update_user_image(
    file: Annotated[UploadFile, File(...)],
    current_user: Annotated[Account, Depends(get_current_active_user)],
):
    """Partially update authenticated user image."""
    return await account_services.update_user_image(file, current_user)


@router.patch("/update-profile", status_code=status.HTTP_200_OK, dependencies=[Depends(security)])
async def update_user_profile(
    data: AccountUpdate,
    current_user: Annotated[Account, Depends(get_current_active_user)],
):
    """Update authenticated user's profile."""
    return await account_services.update_user_profile(data, current_user)


@router.post("/send-otp")
@limiter.limit(settings.RATE_LIMIT_OTP_SEND)
async def send_email_verification(
    request: Request,
    data: EmailVerificationSchema,
    background_tasks: BackgroundTasks,
):
    """Resend activation email."""
    return await account_services.request_otp(
        data.email,
        OTPPurpose.ACCOUNT_VERIFICATION,
        background_tasks,
    )


@router.post("/verify-otp", status_code=status.HTTP_200_OK)
@limiter.limit(settings.RATE_LIMIT_OTP_VERIFY)
async def verify_otp(
    request: Request,
    data: EmailVerificationSchema,
    background_tasks: BackgroundTasks,
):
    """Verify OTP and activate account."""
    return await account_services.verify_account_otp(data, background_tasks)


@router.post("/change-password", status_code=status.HTTP_200_OK, dependencies=[Depends(security)])
async def change_password(
    data: ChangePasswordSchema,
    request: Request,
    background_tasks: BackgroundTasks,
    current_user: Annotated[Account, Depends(get_current_active_user)],
):
    """Change password for authenticated user."""
    return await account_services.change_password(
        data, current_user, request, background_tasks
    )


@router.post("/forgot-password", status_code=status.HTTP_200_OK)
@limiter.limit(settings.RATE_LIMIT_OTP_SEND)
async def forgot_password(
    request: Request,
    data: ForgetPasswordSchema,
    background_tasks: BackgroundTasks,
):
    """Send password reset OTP."""
    return await account_services.request_otp(
        data.email,
        OTPPurpose.PASSWORD_RESET,
        background_tasks,
    )


@router.post("/verify-reset-otp", status_code=status.HTTP_200_OK)
@limiter.limit(settings.RATE_LIMIT_OTP_VERIFY)
async def verify_reset_password_otp(
    request: Request,
    data: ResetPasswordOtpVerifySchema,
):
    """Validate password reset OTP and return a short-lived reset token."""
    return await account_services.verify_reset_password_otp(data, request)


@router.post("/reset-password")
async def reset_password(
    data: NewPasswordSchema,
    request: Request,
    background_tasks: BackgroundTasks,
    user: Annotated[Account, Depends(get_user_from_password_reset_token)],
):
    """Set new password using the reset token from verify-reset-otp or exchange-setup-code."""
    return await account_services.reset_password(
        data, user, request, background_tasks
    )


@router.post("/exchange-setup-code", status_code=status.HTTP_200_OK)
@limiter.limit(settings.RATE_LIMIT_OTP_VERIFY)
async def exchange_setup_code(
    request: Request,
    data: ExchangeSetupCodeSchema,
):
    """Exchange an opaque admin setup code for a short-lived password-setup JWT."""
    return await account_services.exchange_setup_code(
        data.code,
        str(data.email),
        request,
    )


@router.post("/refresh-token", status_code=status.HTTP_200_OK)
@limiter.limit(settings.RATE_LIMIT_REFRESH)
async def refresh_access_token(request: Request, data: RefreshTokenRequest):
    """Refresh access token using a valid refresh token."""
    return await account_services.refresh_access_token(data.refresh_token)


@router.get("/preferences", dependencies=[Depends(security)])
async def get_preferences(
    current_user: Annotated[Account, Depends(get_current_active_user)],
):
    return await account_services.get_account_preferences(current_user)


@router.patch("/preferences", dependencies=[Depends(security)])
async def patch_preferences(
    data: AccountPreferencesUpdate,
    current_user: Annotated[Account, Depends(get_current_active_user)],
):
    return await account_services.update_account_preferences(current_user, data)


@router.delete("/account", dependencies=[Depends(security)])
async def delete_own_account(
    data: AccountDeleteRequest,
    current_user: Annotated[Account, Depends(get_current_active_user)],
):
    return await account_services.delete_account(current_user, data)
