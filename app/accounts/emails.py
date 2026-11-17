"""Account email templates."""

from typing import Dict

from app.base.email_template import (
    base_email_template as base_template,
    client_app_url,
    email_button,
    email_escape,
    email_link_expires_text,
    email_list,
    email_location_panel,
    email_muted,
    email_otp_panel,
    email_panel,
)
from app.config.settings import settings


def activate_account_otp(context: Dict) -> str:
    """Generate the account-activation OTP email."""
    content = f"""
        <h1 class="mail-title">Activate your account</h1>
        <p class="mail-text">Hello {email_escape(context['first_name'])},</p>
        <p class="mail-lead">
            Use the one-time password below to verify your email and activate your
            {email_escape(settings.display_brand_name)} account.
        </p>
        {email_otp_panel(context["otp"], context["valid_minutes"], title="Verification code")}
        {email_muted("If you did not create an account, you can safely ignore this email.")}
        """
    return base_template(
        "Activate Your Account",
        content,
        preheader=f"Your verification code is {context.get('otp', '')}",
    )


def login_verification_otp(context: Dict) -> str:
    """Generate the optional email MFA login OTP email."""
    content = f"""
        <h1 class="mail-title">Sign-in verification</h1>
        <p class="mail-text">Hello {email_escape(context['first_name'])},</p>
        <p class="mail-lead">Enter this code to complete your sign-in:</p>
        {email_otp_panel(context["otp"], context["valid_minutes"], title="Sign-in code")}
        {email_muted("If you did not attempt to sign in, you can safely ignore this email.")}
        """
    return base_template(
        "Your Login Verification Code",
        content,
        preheader=f"Your sign-in code is {context.get('otp', '')}",
    )


def forgot_password_request_otp(context: Dict) -> str:
    """Generate the forgot-password OTP email."""
    content = f"""
        <h1 class="mail-title">Reset your password</h1>
        <p class="mail-text">Hello {email_escape(context['first_name'])},</p>
        <p class="mail-lead">Use this code to continue resetting your password:</p>
        {email_otp_panel(context["otp"], context["valid_minutes"], title="Reset code")}
        {email_muted("If you did not request a password reset, you can safely ignore this email.")}
        """
    return base_template(
        "Reset Your Password",
        content,
        preheader=f"Your password reset code is {context.get('otp', '')}",
    )


def password_reset_success(context: Dict) -> str:
    """Generate the successful password-reset email."""
    location_note = email_location_panel(
        "Sign-in details",
        context.get("location") or context.get("ip"),
    )
    brand = email_escape(settings.display_brand_name)
    content = f"""
        <h1 class="mail-title">Password reset successful</h1>
        <p class="mail-text">Hello {email_escape(context['first_name'])},</p>
        <p class="mail-lead">Your password has been updated successfully.</p>
        {location_note}
        {email_panel(
            "success",
            "You are all set",
            f'<p class="mail-text mail-mb-0">Sign in to {brand} with your new password.</p>',
        )}
        {email_button(client_app_url("/login"), "Sign in")}
        {email_muted("Keep your password confidential. Change it immediately if you suspect compromise.")}
        """
    return base_template("Password Reset Successful", content)


def password_changed_success(context: Dict) -> str:
    """Generate the password-changed email for authenticated updates."""
    location_note = email_location_panel(
        "Change details",
        context.get("location") or context.get("ip"),
    )
    content = f"""
        <h1 class="mail-title">Password changed</h1>
        <p class="mail-text">Hello {email_escape(context['first_name'])},</p>
        <p class="mail-lead">
            Your account password was changed and all other sessions were signed out.
        </p>
        {location_note}
        {email_panel(
            "warning",
            "Did not make this change?",
            '<p class="mail-text mail-mb-0">Contact support immediately so we can help secure your account.</p>',
        )}
        {email_button(client_app_url("/login"), "Sign in")}
        """
    return base_template("Your Password Was Changed", content)


def welcome_email(context: Dict) -> str:
    """Generate the welcome email for new users."""
    greeting_name = email_escape(context.get("full_name") or context["first_name"])
    brand = email_escape(settings.display_brand_name)
    content = f"""
        <h1 class="mail-title">Welcome to {brand}</h1>
        <p class="mail-text">Hey {greeting_name},</p>
        <p class="mail-lead">Your account is active and ready to use.</p>
        {email_panel(
            "success",
            "Next steps",
            email_list(
                [
                    "Complete your profile.",
                    "Explore the available endpoints and flows.",
                    "Review settings before going to production.",
                ]
            ),
        )}
        {email_button(client_app_url(), "Open app")}
        <p class="mail-text mail-mb-0">Cheers,<br>The {brand} team</p>
        """
    return base_template(f"Welcome to {settings.display_brand_name}!", content)


def admin_invite_email(context: Dict) -> str:
    """Generate the initial admin invite email."""
    content = f"""
        <h1 class="mail-title">Admin access invitation</h1>
        <p class="mail-text">Hello {email_escape(context['first_name'])},</p>
        <p class="mail-lead">
            An administrator account has been created for you in
            {email_escape(settings.display_brand_name)}.
        </p>
        {email_panel(
            "info",
            "Set your password",
            f'<p class="mail-text">Create your password using the secure link below.</p>'
            f'<p class="mail-text mail-mb-0">{email_escape(email_link_expires_text(context["expires_in_hours"]))}</p>',
        )}
        {email_button(str(context["setup_link"]), "Set your password")}
        {email_muted("After setting your password, sign in with your email address and new password.")}
        """
    return base_template("Admin Access Invitation", content)


def admin_upgrade_email(context: Dict) -> str:
    """Generate the admin-upgrade email for an existing account."""
    content = f"""
        <h1 class="mail-title">Account upgraded to admin</h1>
        <p class="mail-text">Hello {email_escape(context['first_name'])},</p>
        <p class="mail-lead">
            Your existing {email_escape(settings.display_brand_name)} account now has
            admin access.
        </p>
        {email_panel(
            "info",
            "Complete admin access",
            f'<p class="mail-text">Use the secure link below if you need to set or reset your password.</p>'
            f'<p class="mail-text mail-mb-0">{email_escape(email_link_expires_text(context["expires_in_hours"]))}</p>',
        )}
        {email_button(client_app_url("/login"), "Sign in")}
        {email_button(str(context["setup_link"]), "Set password", secondary=True)}
        """
    return base_template("Admin Access Upgrade", content)
