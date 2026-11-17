"""Account service-layer functions."""

import logging
import secrets
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

from fastapi import BackgroundTasks, HTTPException, Request, Response, UploadFile, status
from pydantic import EmailStr

from app.accounts.auth import (
    PASSWORD_RESET_TOKEN_EXPIRE_HOURS,
    create_access_token,
    create_admin_password_setup_token,
    create_password_reset_token,
    create_refresh_token,
    decode_refresh_token,
    hash_password,
    verify_password,
)
from app.accounts.background import send_activation_email, send_welcome_email
from app.accounts.emails import (
    activate_account_otp,
    admin_invite_email,
    admin_upgrade_email,
    forgot_password_request_otp,
    login_verification_otp,
    password_changed_success,
    password_reset_success,
)
from app.accounts.enums import UserStatus
from app.accounts.models import Account, AccountPreferences
from app.access.services import (
    ensure_default_access_role,
    build_token_auth_payload,
)
from app.accounts.permissions import require_active_account
from app.accounts.schemas import (
    AccountCreatePydantic,
    AccountRead,
    AccountUpdate,
    ChangePasswordSchema,
    EmailVerificationSchema,
    LoginUserSchema,
    NewPasswordSchema,
    ResetPasswordOtpVerifySchema,
    VerifyLoginOtpSchema,
)
from app.accounts.utils import (
    apply_partial_update,
    client_login_location,
    get_user_by_email_or_none,
    get_valid_otp_or_error,
    hash_otp_code,
    hash_setup_code,
    validate_display_name,
    validate_username,
)
from app.base.http_errors import api_error
from app.base.services import upload_file_asset
from app.base.responses import success_response
from app.base.utils import IDPrefix, generate_otp, send_email
from app.config.settings import settings
from app.records.enums import (
    NotificationChannel,
    NotificationType,
    OTPPurpose,
    OTPStatus,
)
from app.records.models import Notification, OTP, PasswordSetupCode

logger = logging.getLogger(__name__)

OTP_VALID_MINUTES = 5
_VERIFICATION_EMAIL_SENT_MESSAGE = (
    "If an account exists for this email, a verification code has been sent."
)
_PASSWORD_RESET_EMAIL_SENT_MESSAGE = (
    "If an account exists for this email, a reset code has been sent."
)
_LOGIN_OTP_SENT_MESSAGE = (
    "If the credentials are correct, a sign-in verification code has been sent."
)


async def _account_read(account: Account) -> AccountRead:
    """Load image FK and return AccountRead (FileOut url populated)."""
    await account.fetch_related("image")
    data = AccountRead.model_validate(account)
    data.display_name = account.display_name or None
    data.username = account.username
    return data


async def register_account(
    data: AccountCreatePydantic,
    background_tasks: BackgroundTasks,
) -> dict:
    """Create a new account and queue its activation email."""
    email = str(data.email).strip().lower()
    if await Account.filter(email=email).exists():
        raise HTTPException(status_code=400, detail="Email already registered.")

    user_data = data.model_dump(exclude_unset=True)
    user_data["email"] = email
    user_data["password"] = hash_password(user_data["password"])
    user = await Account.create(**user_data)
    await ensure_default_access_role(user)

    if user.email:
        background_tasks.add_task(send_activation_email, user.email)

    return {
        "message": "User Created",
        "data": await _account_read(user),
    }


async def _issue_auth_tokens(user: Account) -> dict:
    """Build access/refresh JWTs and serialized profile for an active account."""
    fresh = await Account.get(id=user.id)
    await ensure_default_access_role(fresh)
    token_payload = await build_token_auth_payload(fresh)
    access_token = create_access_token(token_payload)
    refresh_token = create_refresh_token(
        {"sub": token_payload["sub"], "v": token_payload["v"]}
    )
    fresh.last_login_at = datetime.now(timezone.utc)
    await fresh.save(update_fields=["last_login_at", "updated_at"])
    return {
        "access": access_token,
        "refresh": refresh_token,
        "user": await _account_read(fresh),
    }


async def _send_login_verification_otp(
    user: Account,
    background_tasks: BackgroundTasks,
) -> None:
    """Create and email a pending login verification OTP."""
    cooldown_start = datetime.now(timezone.utc) - timedelta(
        seconds=settings.OTP_RESEND_COOLDOWN_SECONDS
    )
    recent_pending = await OTP.filter(
        account=user,
        purpose=OTPPurpose.LOGIN_VERIFICATION,
        status=OTPStatus.PENDING,
        created_at__gte=cooldown_start,
    ).exists()
    if recent_pending:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Please wait before requesting another code.",
            headers={"Retry-After": str(settings.OTP_RESEND_COOLDOWN_SECONDS)},
        )

    await OTP.filter(
        account=user,
        purpose=OTPPurpose.LOGIN_VERIFICATION,
        status=OTPStatus.PENDING,
    ).delete()

    otp_code = generate_otp()
    await OTP.create(
        account=user,
        code=None,
        code_hash=hash_otp_code(otp_code),
        purpose=OTPPurpose.LOGIN_VERIFICATION,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=OTP_VALID_MINUTES),
    )
    context = {
        "first_name": user.first_name,
        "otp": otp_code,
        "valid_minutes": OTP_VALID_MINUTES,
    }
    background_tasks.add_task(
        send_email,
        "Your Login Verification Code",
        str(user.email),
        login_verification_otp(context),
    )


async def authenticate_user(
    data: LoginUserSchema,
    background_tasks: BackgroundTasks,
) -> dict:
    """Validate credentials; optionally defer tokens behind email MFA."""
    email = str(data.email).strip().lower()
    user = await Account.filter(email=email).first()
    if not user or not verify_password(data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    require_active_account(user)

    prefs, _ = await AccountPreferences.get_or_create(account=user)
    if prefs.email_login_mfa_enabled:
        await _send_login_verification_otp(user, background_tasks)
        return {
            "message": _LOGIN_OTP_SENT_MESSAGE,
            "data": {
                "login_pending": True,
                "email": email,
            },
        }

    return {
        "message": "Login Successful",
        "data": await _issue_auth_tokens(user),
    }


async def verify_login_otp(data: VerifyLoginOtpSchema) -> dict:
    """Validate login OTP and return auth tokens (optional email MFA step 2)."""
    user = await get_user_by_email_or_none(data.email)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired code.")
    require_active_account(user)
    otp = await get_valid_otp_or_error(
        user,
        data.otp_code,
        purpose=OTPPurpose.LOGIN_VERIFICATION,
    )
    otp.status = OTPStatus.USED
    otp.verified_at = datetime.now(timezone.utc)
    await otp.save()
    return {
        "message": "Login Successful",
        "data": await _issue_auth_tokens(user),
    }


async def logout_user(response: Response, current_user: Account) -> dict:
    """Invalidate current JWTs by bumping session version; clear auth cookies if used."""
    current_user.auth_token_version = int(current_user.auth_token_version or 0) + 1
    await current_user.save()
    cookie_path = getattr(settings, "AUTH_COOKIE_PATH", "/")
    response.delete_cookie(key="access", path=cookie_path)
    response.delete_cookie(key="refresh", path=cookie_path)
    return {"message": "Logout successful"}


async def request_otp(
    email: EmailStr,
    purpose: OTPPurpose,
    background_tasks: BackgroundTasks,
) -> dict:
    """Create and send an OTP for account verification or password reset."""
    user = await get_user_by_email_or_none(email)
    if purpose == OTPPurpose.ACCOUNT_VERIFICATION:
        success_message = _VERIFICATION_EMAIL_SENT_MESSAGE
    elif purpose == OTPPurpose.PASSWORD_RESET:
        success_message = _PASSWORD_RESET_EMAIL_SENT_MESSAGE
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported OTP purpose.",
        )

    if not user:
        logger.info("OTP request for unknown email (not disclosed to client).")
        return {"message": success_message}

    cooldown_start = datetime.now(timezone.utc) - timedelta(
        seconds=settings.OTP_RESEND_COOLDOWN_SECONDS
    )
    recent_pending = await OTP.filter(
        account=user,
        purpose=purpose,
        status=OTPStatus.PENDING,
        created_at__gte=cooldown_start,
    ).exists()
    if recent_pending:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Please wait before requesting another code.",
            headers={"Retry-After": str(settings.OTP_RESEND_COOLDOWN_SECONDS)},
        )

    await OTP.filter(
        account=user,
        purpose=purpose,
        status=OTPStatus.PENDING,
    ).delete()

    otp_code = generate_otp()
    await OTP.create(
        account=user,
        code=None,
        code_hash=hash_otp_code(otp_code),
        purpose=purpose,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=OTP_VALID_MINUTES),
    )

    context = {
        "first_name": user.first_name,
        "otp": otp_code,
        "valid_minutes": OTP_VALID_MINUTES,
    }
    if purpose == OTPPurpose.ACCOUNT_VERIFICATION:
        background_tasks.add_task(
            send_email,
            "Your Verification OTP",
            str(email),
            activate_account_otp(context),
        )
        return {"message": success_message}

    background_tasks.add_task(
        send_email,
        "Reset Your Password",
        str(email),
        forgot_password_request_otp(context),
    )
    return {"message": success_message}


async def verify_account_otp(
    data: EmailVerificationSchema,
    background_tasks: BackgroundTasks,
) -> dict:
    """Activate an account and return login tokens."""
    if not data.otp_code:
        raise HTTPException(status_code=422, detail="OTP code is required.")
    user = await get_user_by_email_or_none(data.email)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired code.")
    otp = await get_valid_otp_or_error(user, data.otp_code)

    user.status = UserStatus.ACTIVE
    await user.save()
    otp.status = OTPStatus.USED
    otp.verified_at = datetime.now(timezone.utc)
    await otp.save()

    if user.email:
        background_tasks.add_task(send_welcome_email, user.email)
    await ensure_default_access_role(user)
    token_payload = await build_token_auth_payload(user)
    access_token = create_access_token(token_payload)
    refresh_token = create_refresh_token(
        {"sub": token_payload["sub"], "v": token_payload["v"]}
    )
    user.last_login_at = datetime.now(timezone.utc)
    await user.save(update_fields=["last_login_at", "updated_at"])
    return {
        "message": "OTP verified successfully.",
        "data": {
            "access": access_token,
            "refresh": refresh_token,
            "user": await _account_read(user),
            "created": True,
        },
    }


async def verify_reset_password_otp(
    data: ResetPasswordOtpVerifySchema,
    request: Request,
) -> dict:
    """Validate the password-reset OTP, consume it, bump session version, and return a 6h JWT."""
    user = await get_user_by_email_or_none(data.email)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired code.")
    otp = await get_valid_otp_or_error(
        user,
        data.otp_code,
        purpose=OTPPurpose.PASSWORD_RESET,
    )
    otp.status = OTPStatus.USED
    otp.verified_at = datetime.now(timezone.utc)
    await otp.save()
    user.auth_token_version = int(user.auth_token_version) + 1
    await user.save()
    reset_token = create_password_reset_token(
        {"sub": str(user.id), "v": int(user.auth_token_version)}
    )
    current_login = client_login_location(request)

    return {
        "message": "OTP verified. Use Authorization: Bearer <reset_token> on POST /auth/reset-password with your new password.",
        "data": {
            "reset_token": reset_token,
            "token_type": "Bearer",
            "expires_in_hours": PASSWORD_RESET_TOKEN_EXPIRE_HOURS,
            "current_login": current_login,
        },
    }


async def reset_password(
    data: NewPasswordSchema,
    user: Account,
    request: Request,
    background_tasks: BackgroundTasks,
) -> dict:
    """Set a new password using the 6h password-reset JWT."""
    if data.new_password != data.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match.")

    user.password = hash_password(data.new_password)
    user.status = UserStatus.ACTIVE
    user.auth_token_version = int(user.auth_token_version) + 1
    await user.save()
    current_login = client_login_location(request)

    await _record_password_reset_success(user, current_login, background_tasks)

    return {
        "message": "Password reset successfully.",
        "data": {
            "current_login": current_login,
        },
    }


async def change_password(
    data: ChangePasswordSchema,
    current_user: Account,
    request: Request,
    background_tasks: BackgroundTasks,
) -> dict:
    """Change the authenticated user's password."""
    if not verify_password(data.old_password, current_user.password):
        raise HTTPException(status_code=400, detail="Old password is incorrect.")
    if data.new_password != data.confirm_password:
        raise HTTPException(status_code=400, detail="New passwords do not match.")

    current_user.auth_token_version = int(current_user.auth_token_version) + 1
    current_user.password = hash_password(data.new_password)
    await current_user.save()
    current_login = client_login_location(request)
    await _record_password_changed_success(
        current_user, current_login, background_tasks
    )
    return {
        "message": "Password changed successfully. Sign in again on this device.",
        "data": {
            "current_login": current_login,
        },
    }


async def _record_password_reset_success(
    user: Account,
    current_login: dict,
    background_tasks: BackgroundTasks,
) -> None:
    """In-app notification + success email (async via background)."""
    ip_part = current_login.get("ip") or "an unknown address"

    await Notification.create(
        account=user,
        type=NotificationType.SUCCESS,
        channel=NotificationChannel.PUSH,
        title="Password reset successful",
        message=(
            f"Your password was reset (approx. from {ip_part}). If this was not you, contact support."
        ),
        sent_at=datetime.now(timezone.utc),
    )
    if user.email:
        context = {
            "first_name": user.first_name,
            "ip": current_login.get("ip"),
            "user_agent": current_login.get("user_agent"),
        }
        background_tasks.add_task(
            send_email,
            "Password reset successful",
            str(user.email),
            password_reset_success(context),
        )


async def _record_password_changed_success(
    user: Account,
    current_login: dict,
    background_tasks: BackgroundTasks,
) -> None:
    """In-app notification + email when password is changed from an authenticated session."""
    ip_part = current_login.get("ip") or "an unknown address"
    await Notification.create(
        account=user,
        type=NotificationType.WARNING,
        channel=NotificationChannel.PUSH,
        title="Password changed",
        message=(
            f"Your password was changed (approx. from {ip_part}). "
            "All other devices were signed out. If this was not you, contact support."
        ),
        sent_at=datetime.now(timezone.utc),
    )
    if user.email:
        context = {
            "first_name": user.first_name,
            "ip": current_login.get("ip"),
            "user_agent": current_login.get("user_agent"),
        }
        background_tasks.add_task(
            send_email,
            "Your password was changed",
            str(user.email),
            password_changed_success(context),
        )


async def refresh_access_token(refresh_token: str) -> dict:
    """Issue a new access token from a valid refresh token."""
    payload = decode_refresh_token(refresh_token)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing user ID in token",
        )
    if not str(user_id).startswith(f"{IDPrefix.ACCOUNT}_"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID format",
        )
    user = await Account.filter(id=user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    require_active_account(user)
    await ensure_default_access_role(user)
    if "v" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token version",
        )
    token_v = int(payload["v"])
    if token_v != int(user.auth_token_version):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or revoked",
        )
    token_payload = await build_token_auth_payload(user)
    return {
        "message": "Token refreshed successfully.",
        "data": {
            "access": create_access_token(token_payload),
        },
    }


async def get_current_user_profile(current_user: Account) -> dict:
    """Return the authenticated user's profile."""
    return {
        "message": "User Retrieved",
        "data": await _account_read(current_user),
    }


async def update_user_profile(data: AccountUpdate, current_user: Account) -> dict:
    """Patch editable profile fields for the authenticated user."""
    update_data = data.model_dump(exclude_unset=True)
    display_name = update_data.pop("display_name", None)
    username = update_data.pop("username", None)

    if display_name is not None:
        try:
            update_data["display_name_override"] = validate_display_name(display_name)
        except ValueError as exc:
            raise api_error(
                422, "invalid_display_name", "Display name is invalid."
            ) from exc

    if username is not None:
        try:
            normalized = validate_username(username)
        except ValueError as exc:
            raise api_error(
                422,
                "invalid_username",
                "Username must be 3-32 lowercase letters, digits, or underscores.",
            ) from exc
        taken = (
            await Account.filter(username=normalized)
            .exclude(id=current_user.id)
            .exists()
        )
        if taken:
            raise api_error(409, "username_taken", "Username is already taken.")
        update_data["username"] = normalized

    apply_partial_update(current_user, update_data)
    await current_user.save()

    return {
        "message": "Profile updated successfully",
        "data": await _account_read(current_user),
    }


async def update_user_image(file: UploadFile, current_user: Account) -> dict:
    """Upload and attach a new profile image."""
    image_asset = await upload_file_asset(
        file=file,
        folder="user_images",
        alt_text=f"{current_user.first_name} Image",
    )
    current_user.image = image_asset
    await current_user.save()

    return {
        "message": "User Updated Successfully",
        "data": await _account_read(current_user),
    }


async def _build_password_setup_link(account: Account) -> str:
    """Create a frontend-friendly password setup link with an opaque one-time code."""
    await PasswordSetupCode.filter(account=account, used_at__isnull=True).delete()
    code = secrets.token_urlsafe(32)
    await PasswordSetupCode.create(
        account=account,
        code_hash=hash_setup_code(code),
        expires_at=datetime.now(timezone.utc)
        + timedelta(hours=settings.ADMIN_PASSWORD_SETUP_CODE_EXPIRE_HOURS),
    )
    query = urlencode({"code": code})
    return f"{settings.PASSWORD_SETUP_URL}?{query}"


async def exchange_setup_code(code: str, email: str, request: Request) -> dict:
    """Exchange an opaque admin setup code for a short-lived password-setup JWT."""
    user = await get_user_by_email_or_none(email)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired setup code.")

    setup_code = await PasswordSetupCode.filter(
        account=user,
        code_hash=hash_setup_code(code),
        used_at__isnull=True,
    ).order_by("-created_at").first()
    now = datetime.now(timezone.utc)
    expires_at = setup_code.expires_at if setup_code else None
    if expires_at is not None and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if not setup_code or not expires_at or expires_at <= now:
        raise HTTPException(status_code=400, detail="Invalid or expired setup code.")

    setup_code.used_at = now
    await setup_code.save()
    user.auth_token_version = int(user.auth_token_version) + 1
    await user.save()
    reset_token = create_admin_password_setup_token(
        {"sub": str(user.id), "v": int(user.auth_token_version)},
        expires_delta=timedelta(hours=PASSWORD_RESET_TOKEN_EXPIRE_HOURS),
    )
    current_login = client_login_location(request)
    return {
        "message": (
            "Setup code accepted. Use Authorization: Bearer <reset_token> on "
            "POST /auth/reset-password with your new password."
        ),
        "data": {
            "reset_token": reset_token,
            "token_type": "Bearer",
            "expires_in_hours": PASSWORD_RESET_TOKEN_EXPIRE_HOURS,
            "current_login": current_login,
        },
    }


async def _send_invite_email(account: Account) -> None:
    """Send the new-admin invite email."""
    if not account.email:
        return
    context = {
        "first_name": account.first_name,
        "setup_link": await _build_password_setup_link(account),
        "expires_in_hours": settings.ADMIN_PASSWORD_SETUP_CODE_EXPIRE_HOURS,
    }
    send_email(
        f"Admin access for {settings.PROJECT_NAME}",
        str(account.email),
        admin_invite_email(context),
    )


async def _send_admin_upgrade_email(account: Account) -> None:
    """Send the admin-upgrade email for an existing account."""
    if not account.email:
        return
    context = {
        "first_name": account.first_name,
        "setup_link": await _build_password_setup_link(account),
        "expires_in_hours": settings.ADMIN_PASSWORD_SETUP_CODE_EXPIRE_HOURS,
    }
    send_email(
        f"Your {settings.PROJECT_NAME} account now has admin access",
        str(account.email),
        admin_upgrade_email(context),
    )


def _preferences_payload(prefs: AccountPreferences) -> dict:
    return {
        "id": prefs.id,
        "account_id": prefs.account_id,
        "push_enabled": prefs.push_enabled,
        "email_notifications_enabled": prefs.email_notifications_enabled,
        "marketing_email_enabled": prefs.marketing_email_enabled,
        "email_login_mfa_enabled": prefs.email_login_mfa_enabled,
        "created_at": prefs.created_at,
        "updated_at": prefs.updated_at,
    }


async def get_account_preferences(account: Account) -> dict:
    prefs, _ = await AccountPreferences.get_or_create(account=account)
    return success_response(data=_preferences_payload(prefs), message="Preferences")


async def update_account_preferences(account: Account, data) -> dict:
    prefs, _ = await AccountPreferences.get_or_create(account=account)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(prefs, field, value)
    await prefs.save()
    return success_response(data=_preferences_payload(prefs), message="Preferences updated")
