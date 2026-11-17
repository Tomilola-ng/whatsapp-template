"""Shared HTML email template helpers for transactional mail.

Brand tokens come from settings so forks can re-skin without rewriting helpers.
Module email builders create inner HTML only and pass it to
:func:`base_email_template`.
"""

from __future__ import annotations

import datetime
import html
import ipaddress
from typing import Literal

from app.config.settings import settings

PanelKind = Literal["info", "success", "warning", "error", "neutral"]

# Fallback palette when env brand colors are unset (neutral, not product-locked).
_DEFAULT_PRIMARY = "#2563EB"
_DEFAULT_DARK = "#111827"
_DEFAULT_OFF_WHITE = "#F8FAFC"
_DEFAULT_MUTED = "#6B7280"
_DEFAULT_BORDER = "#E5E7EB"
_DEFAULT_SUCCESS = "#15803D"
_DEFAULT_WARNING = "#B45309"
_DEFAULT_ERROR = "#DC2626"
_DEFAULT_INFO = "#2563EB"

_GOOGLE_FONTS_URL = (
    "https://fonts.googleapis.com/css2?"
    "family=Inter:wght@400;500;600;700&display=swap"
)


def _brand_primary() -> str:
    return (settings.BRAND_PRIMARY_COLOR or _DEFAULT_PRIMARY).strip()


def _brand_dark() -> str:
    return (settings.BRAND_DARK_COLOR or _DEFAULT_DARK).strip()


def _brand_on_primary() -> str:
    return (settings.BRAND_ON_PRIMARY_COLOR or "#FFFFFF").strip()


def email_escape(value: object, *, quote: bool = False) -> str:
    """Escape user- or API-derived strings for safe HTML interpolation."""
    return html.escape(str(value or ""), quote=quote)


def client_app_url(path: str = "") -> str:
    """Build a URL on the client app (CLIENT_APP_URL or APP_BASE_URL)."""
    base = (settings.CLIENT_APP_URL or settings.APP_BASE_URL).rstrip("/")
    cleaned = (path or "").strip()
    if not cleaned:
        return base
    return f"{base}/{cleaned.lstrip('/')}"


def email_button(href: str, label: str, *, secondary: bool = False) -> str:
    """Primary or secondary CTA button (inline styles for client compatibility)."""
    safe_href = email_escape(href, quote=True)
    safe_label = email_escape(label)
    dark = _brand_dark()
    primary = _brand_primary()
    on_primary = _brand_on_primary()
    if secondary:
        style = (
            "display:inline-block;padding:12px 24px;border-radius:8px;"
            f"background-color:#ffffff;color:{dark};"
            f"border:1px solid {_DEFAULT_BORDER};font-weight:700;font-size:15px;"
            "text-decoration:none;line-height:1.2;"
        )
    else:
        style = (
            "display:inline-block;padding:12px 28px;border-radius:8px;"
            f"background-color:{primary};color:{on_primary};"
            "font-weight:700;font-size:15px;text-decoration:none;line-height:1.2;"
        )
    return (
        f'<table role="presentation" cellpadding="0" cellspacing="0" class="mail-btn-wrap">'
        f'<tr><td align="center">'
        f'<a href="{safe_href}" class="mail-btn{" mail-btn-secondary" if secondary else ""}" '
        f'style="{style}">{safe_label}</a>'
        f"</td></tr></table>"
    )


def email_otp_panel(otp: str, valid_minutes: int | str, *, title: str = "Your code") -> str:
    """Highlighted one-time password block."""
    body = (
        f'<p class="mail-otp" style="font-size:32px;font-weight:700;letter-spacing:6px;'
        f'margin:8px 0 12px;font-family:Consolas,Monaco,monospace;">'
        f"{email_escape(otp)}</p>"
        f'<p class="mail-otp-meta mail-text-sm mail-muted">'
        f"Valid for {email_escape(format_valid_minutes(valid_minutes))}.</p>"
    )
    return email_panel("info", title, body)


def email_panel(kind: PanelKind, title: str, body: str) -> str:
    """Branded callout panel."""
    safe_title = email_escape(title)
    return (
        f'<div class="mail-panel mail-panel-{kind}">'
        f'<p class="mail-panel-title">{safe_title}</p>'
        f'<div class="mail-panel-body">{body}</div>'
        f"</div>"
    )


def email_detail_table(rows: list[tuple[str, str]]) -> str:
    """Key/value rows for structured content (contact details, metadata)."""
    if not rows:
        return ""
    items = []
    for label, value in rows:
        items.append(
            "<tr>"
            f'<td class="mail-detail-label">{email_escape(label)}</td>'
            f'<td class="mail-detail-value">{email_escape(value)}</td>'
            "</tr>"
        )
    return (
        '<table role="presentation" cellpadding="0" cellspacing="0" '
        'class="mail-detail-table" width="100%">'
        f"{''.join(items)}</table>"
    )


def email_list(items: list[str], *, ordered: bool = False) -> str:
    """Simple bullet or numbered list."""
    tag = "ol" if ordered else "ul"
    lis = "".join(f"<li>{email_escape(item)}</li>" for item in items if item)
    if not lis:
        return ""
    return f'<{tag} class="mail-list">{lis}</{tag}>'


def email_divider() -> str:
    return '<hr class="mail-divider" />'


def email_muted(text: str) -> str:
    return f'<p class="mail-text mail-muted">{email_escape(text)}</p>'


def format_expiry_hours(hours: int | float | str) -> str:
    """Human-readable expiry duration: hours below 24, days at or above."""
    total = int(float(hours))
    if total >= 24:
        days = total // 24 if total % 24 == 0 else max(1, round(total / 24))
        return f"{days} day" if days == 1 else f"{days} days"
    return f"{total} hour" if total == 1 else f"{total} hours"


def email_link_expires_text(hours: int | float | str) -> str:
    """Standard copy for expiring action links."""
    return f"This link expires in {format_expiry_hours(hours)}."


def is_probable_ip_address(value: object) -> bool:
    """Return True when value looks like an IP address rather than a place name."""
    text = str(value or "").strip()
    if not text:
        return False
    try:
        ipaddress.ip_address(text)
        return True
    except ValueError:
        return False


def email_location_panel(title: str, location: object) -> str:
    """Render a location callout only for human-readable place strings (not IPs)."""
    text = str(location or "").strip()
    if not text or is_probable_ip_address(text):
        return ""
    return email_panel(
        "neutral",
        title,
        f'<p class="mail-text mail-mb-0">Approximate location: {email_escape(text)}</p>',
    )


def format_valid_minutes(minutes: int | float | str) -> str:
    """Human-readable OTP validity (minutes only — OTP windows stay short)."""
    total = int(float(minutes))
    return f"{total} minute" if total == 1 else f"{total} minutes"


def _email_styles() -> str:
    dark = _brand_dark()
    primary = _brand_primary()
    muted = _DEFAULT_MUTED
    border = _DEFAULT_BORDER
    off_white = _DEFAULT_OFF_WHITE
    return f"""
        body, table, td, a, p {{
          margin: 0;
          padding: 0;
          font-family: "Inter", Arial, Helvetica, sans-serif;
        }}
        h1, h2, h3, h4, h5, h6 {{
          margin: 0;
          padding: 0;
          font-family: "Inter", Arial, Helvetica, sans-serif;
        }}
        body {{
          width: 100% !important;
          background-color: #EEF2F7;
          color: {dark};
          -webkit-text-size-adjust: 100%;
          -ms-text-size-adjust: 100%;
        }}
        img {{
          border: 0;
          outline: none;
          text-decoration: none;
          max-width: 100%;
          height: auto;
        }}
        a {{
          color: {primary};
          text-decoration: underline;
        }}
        .mail-outer {{
          width: 100%;
          background-color: #EEF2F7;
          padding: 32px 16px;
        }}
        .mail-container {{
          width: 100%;
          max-width: 600px;
          margin: 0 auto;
        }}
        .mail-card {{
          background-color: #ffffff;
          border-radius: 16px;
          overflow: hidden;
          border: 1px solid {border};
          box-shadow: 0 8px 24px rgba(17, 24, 39, 0.06);
        }}
        .mail-header {{
          background-color: {dark};
          padding: 28px 32px 24px;
          text-align: center;
        }}
        .mail-brand-lockup {{
          display: inline-block;
          text-decoration: none;
        }}
        .mail-brand-logo {{
          display: block;
          max-height: 40px;
          width: auto;
          border-radius: 8px;
        }}
        .mail-brand-wordmark {{
          font-family: "Inter", Arial, sans-serif;
          font-size: 22px;
          line-height: 1.2;
          letter-spacing: 0.02em;
          font-weight: 700;
          color: #ffffff;
          vertical-align: middle;
        }}
        .mail-content {{
          padding: 32px;
        }}
        .mail-title {{
          color: {dark};
          font-size: 26px;
          line-height: 1.2;
          font-weight: 700;
          margin: 0 0 16px;
        }}
        .mail-lead {{
          color: {dark};
          font-size: 17px;
          line-height: 1.6;
          margin: 0 0 20px;
        }}
        .mail-text {{
          color: {dark};
          font-size: 16px;
          line-height: 1.6;
          margin: 0 0 16px;
        }}
        .mail-text-sm {{ font-size: 14px; line-height: 1.55; }}
        .mail-text-xs {{ font-size: 12px; line-height: 1.5; }}
        .mail-muted {{ color: {muted}; }}
        .mail-mb-0 {{ margin-bottom: 0 !important; }}
        .mail-panel {{
          border-radius: 12px;
          padding: 18px 20px;
          margin: 0 0 20px;
          border: 1px solid {border};
        }}
        .mail-panel-title {{
          font-size: 13px;
          font-weight: 700;
          letter-spacing: 0.06em;
          text-transform: uppercase;
          margin: 0 0 10px;
        }}
        .mail-panel-body p:last-child,
        .mail-panel-body ul:last-child,
        .mail-panel-body ol:last-child {{
          margin-bottom: 0;
        }}
        .mail-panel-info {{ background-color: #EFF6FF; border-color: #BFDBFE; }}
        .mail-panel-info .mail-panel-title {{ color: {_DEFAULT_INFO}; }}
        .mail-panel-success {{ background-color: #ECFDF3; border-color: #BBF7D0; }}
        .mail-panel-success .mail-panel-title {{ color: {_DEFAULT_SUCCESS}; }}
        .mail-panel-warning {{ background-color: #FFFBEB; border-color: #FDE68A; }}
        .mail-panel-warning .mail-panel-title {{ color: {_DEFAULT_WARNING}; }}
        .mail-panel-error {{ background-color: #FEF2F2; border-color: #FECACA; }}
        .mail-panel-error .mail-panel-title {{ color: {_DEFAULT_ERROR}; }}
        .mail-panel-neutral {{ background-color: {off_white}; }}
        .mail-panel-neutral .mail-panel-title {{ color: {muted}; }}
        .mail-otp {{ color: {dark}; }}
        .mail-btn-wrap {{ margin: 8px 0 20px; }}
        .mail-divider {{
          border: 0;
          border-top: 1px solid {border};
          margin: 24px 0;
        }}
        .mail-detail-table td {{
          padding: 8px 0;
          font-size: 15px;
          line-height: 1.5;
          vertical-align: top;
        }}
        .mail-detail-label {{
          color: {muted};
          width: 34%;
          padding-right: 12px !important;
          font-weight: 600;
        }}
        .mail-detail-value {{
          color: {dark};
          word-break: break-word;
        }}
        .mail-list {{
          margin: 0 0 16px 20px;
          padding: 0;
          color: {dark};
          font-size: 15px;
          line-height: 1.6;
        }}
        .mail-list li {{ margin-bottom: 6px; }}
        .mail-support {{ margin-top: 8px; }}
        .mail-footer {{
          background-color: {off_white};
          padding: 24px 32px;
          text-align: center;
          border-top: 1px solid {border};
        }}
        .mail-footer p {{
          color: {muted};
          font-size: 12px;
          line-height: 1.6;
          margin: 0 0 8px;
        }}
        .mail-footer a {{
          color: {dark};
          font-weight: 600;
          text-decoration: none;
        }}
        /* Legacy class aliases for older markup */
        .muted {{ color: {muted}; font-size: 14px; }}
        .notification, .success, .warning, .error {{
          border-radius: 12px;
          padding: 18px 20px;
          margin: 0 0 20px;
          border: 1px solid {border};
        }}
        .notification {{ background-color: #EFF6FF; border-color: #BFDBFE; }}
        .success {{ background-color: #ECFDF3; border-color: #BBF7D0; }}
        .warning {{ background-color: #FFFBEB; border-color: #FDE68A; }}
        .error {{ background-color: #FEF2F2; border-color: #FECACA; }}
        h1, h2, h3 {{
          color: {dark};
          margin: 0 0 12px;
          line-height: 1.2;
          font-weight: 700;
        }}
        h1 {{ font-size: 26px; margin-bottom: 16px; }}
        h2 {{ font-size: 20px; }}
        h3 {{ font-size: 14px; letter-spacing: 0.04em; text-transform: uppercase; }}
        p {{
          color: {dark};
          font-size: 16px;
          line-height: 1.6;
          margin: 0 0 16px;
        }}
        @media only screen and (max-width: 620px) {{
          .mail-outer {{ padding: 16px 8px !important; }}
          .mail-content, .mail-footer {{
            padding-left: 20px !important;
            padding-right: 20px !important;
          }}
          .mail-title, h1 {{ font-size: 22px !important; }}
          .mail-otp {{ font-size: 28px !important; letter-spacing: 4px !important; }}
        }}
    """


def _brand_header_html() -> str:
    brand_name = email_escape(settings.display_brand_name)
    app_url = email_escape(client_app_url(), quote=True)
    logo_url = (settings.BRAND_LOGO_URL or "").strip()
    if logo_url:
        safe_logo = email_escape(logo_url, quote=True)
        brand_inner = (
            f'<img src="{safe_logo}" alt="{brand_name}" class="mail-brand-logo" '
            f'style="display:block;max-height:40px;width:auto;border-radius:8px;">'
        )
    else:
        brand_inner = f'<span class="mail-brand-wordmark">{brand_name}</span>'
    return (
        f'<a href="{app_url}" class="mail-brand-lockup" style="text-decoration:none;">'
        f"{brand_inner}</a>"
    )


def base_email_template(title: str, body: str, *, preheader: str | None = None) -> str:
    """Wrap inner email HTML in the shared brand shell."""
    year = datetime.datetime.now().year
    brand_name = email_escape(settings.display_brand_name)
    support_email = email_escape(settings.support_email)
    escaped_title = email_escape(title)
    app_url = email_escape(client_app_url(), quote=True)
    dark = _brand_dark()
    off_white = _DEFAULT_OFF_WHITE
    border = _DEFAULT_BORDER
    preheader_html = ""
    if preheader:
        preheader_html = (
            f'<div style="display:none;max-height:0;overflow:hidden;opacity:0;">'
            f"{email_escape(preheader)}"
            f"</div>"
        )
    return f"""\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta http-equiv="X-UA-Compatible" content="IE=edge">
  <title>{escaped_title} | {brand_name}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="{email_escape(_GOOGLE_FONTS_URL, quote=True)}" rel="stylesheet">
  <style>{_email_styles()}</style>
</head>
<body>
  {preheader_html}
  <table role="presentation" cellpadding="0" cellspacing="0" width="100%" class="mail-outer">
    <tr>
      <td align="center">
        <table role="presentation" cellpadding="0" cellspacing="0" width="100%" class="mail-container">
          <tr>
            <td>
              <table role="presentation" cellpadding="0" cellspacing="0" width="100%" class="mail-card">
                <tr>
                  <td class="mail-header" style="background-color:{dark};padding:28px 32px 24px;text-align:center;">
                    {_brand_header_html()}
                  </td>
                </tr>
                <tr>
                  <td class="mail-content" style="padding:32px;">
                    {body}
                    <p class="mail-text mail-text-sm mail-muted mail-support">
                      Questions? Reply to this email or contact
                      <a href="mailto:{support_email}">{support_email}</a>.
                    </p>
                  </td>
                </tr>
                <tr>
                  <td class="mail-footer" style="background-color:{off_white};padding:24px 32px;text-align:center;border-top:1px solid {border};">
                    <p>&copy; {year} {brand_name}. All rights reserved.</p>
                    <p class="mail-text-xs">
                      <a href="{app_url}">{email_escape(client_app_url())}</a>
                    </p>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""
