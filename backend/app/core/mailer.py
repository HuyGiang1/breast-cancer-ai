import json
import logging
import os
import smtplib
import urllib.parse
from email.message import EmailMessage
from pathlib import Path

from app.core.database import PROJECT_ROOT, utc_now_iso

logger = logging.getLogger("mailer")

MAIL_MODE = os.getenv("APP_MAIL_MODE", "file").strip().lower()
OUTBOX_DIR = PROJECT_ROOT / "backend" / "data" / "outbox"
OUTBOX_DIR.mkdir(parents=True, exist_ok=True)
PASSWORD_RESET_OUTBOX = OUTBOX_DIR / "password_reset.jsonl"
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com").strip()
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "").strip()
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "").strip()
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", SMTP_USERNAME).strip()
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "Breast Health Studio").strip()
FRONTEND_URL = os.getenv("APP_FRONTEND_URL", "http://localhost").rstrip("/")


def _send_via_smtp(*, to_email: str, subject: str, text_body: str, html_body: str | None = None) -> None:
    if not SMTP_USERNAME or not SMTP_PASSWORD or not SMTP_FROM_EMAIL:
        raise RuntimeError("SMTP is not configured. Please set SMTP_USERNAME, SMTP_PASSWORD, and SMTP_FROM_EMAIL.")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = f"{SMTP_FROM_NAME} <{SMTP_FROM_EMAIL}>"
    msg["To"] = to_email
    msg.set_content(text_body)
    if html_body:
        msg.add_alternative(html_body, subtype="html")

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
    except Exception as exc:
        # Log controlled server-side error without exposing passwords or sensitive tokens
        logger.error("SMTP delivery failed for recipient '%s' via %s:%s: %s", to_email, SMTP_HOST, SMTP_PORT, exc)
        raise RuntimeError(f"Email delivery failed: {exc}") from None


def _write_reset_token_to_file(*, email: str, reset_token: str, expires_at: str, reset_url: str) -> None:
    payload = {
        "type": "password_reset",
        "email": email,
        "reset_token": reset_token,
        "reset_url": reset_url,
        "expires_at": expires_at,
        "created_at": utc_now_iso(),
    }
    with PASSWORD_RESET_OUTBOX.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")


def send_password_reset_email(*, email: str, reset_token: str, expires_at: str) -> None:
    encoded_token = urllib.parse.quote(reset_token)
    recovery_url = f"{FRONTEND_URL}/reset-password.html?token={encoded_token}&v=auth-v3"

    if MAIL_MODE == "file":
        _write_reset_token_to_file(
            email=email,
            reset_token=reset_token,
            expires_at=expires_at,
            reset_url=recovery_url,
        )
        return

    subject = "Reset your Breast Health Studio password"
    text_body = (
        "Hello,\n\n"
        "We received a request to reset your password for your Breast Health Studio account.\n\n"
        f"You can reset your password using the following link (expires at {expires_at}):\n"
        f"{recovery_url}\n\n"
        "If you did not request this password reset, please ignore this email.\n"
        "This is an automated message from the Breast Health Studio research platform."
    )
    html_body = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 24px; }}
    .card {{ max-width: 560px; margin: 0 auto; background: #1e293b; border-radius: 12px; padding: 32px; border: 1px solid #334155; }}
    .brand {{ font-size: 18px; font-weight: 700; color: #14b8a6; margin-bottom: 24px; display: inline-block; }}
    h1 {{ font-size: 22px; color: #ffffff; margin-top: 0; margin-bottom: 16px; }}
    p {{ font-size: 15px; line-height: 1.6; color: #cbd5e1; margin: 0 0 16px; }}
    .btn {{ display: inline-block; background: #0d9488; color: #ffffff !important; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: 600; margin: 20px 0; }}
    .link-alt {{ font-size: 13px; color: #94a3b8; word-break: break-all; margin-top: 20px; }}
    .footer {{ margin-top: 32px; padding-top: 16px; border-top: 1px solid #334155; font-size: 12px; color: #64748b; }}
  </style>
</head>
<body>
  <div class="card">
    <span class="brand">BC Breast Health Studio</span>
    <h1>Password Reset Request</h1>
    <p>A password reset was requested for your Breast Health Studio research account (<strong>{email}</strong>).</p>
    <p>Click the button below to set a new password. This link is valid until <strong>{expires_at}</strong>.</p>
    <p style="text-align: center;">
      <a href="{recovery_url}" class="btn">Reset Password</a>
    </p>
    <p class="link-alt">If the button does not work, copy and paste this link into your browser:<br><a href="{recovery_url}" style="color: #2dd4bf;">{recovery_url}</a></p>
    <div class="footer">
      If you did not request a password reset, you can safely ignore this email.<br>
      Research &amp; Educational Platform. Not for autonomous clinical diagnosis.
    </div>
  </div>
</body>
</html>"""

    _send_via_smtp(
        to_email=email,
        subject=subject,
        text_body=text_body,
        html_body=html_body,
    )


def send_welcome_email(*, email: str, full_name: str) -> None:
    if MAIL_MODE == "file":
        return

    login_url = f"{FRONTEND_URL}/login.html?v=auth-v3"
    subject = "Welcome to Breast Health Studio"
    text_body = (
        f"Hello {full_name},\n\n"
        "Your research account on Breast Health Studio has been created successfully.\n\n"
        f"You can sign in at: {login_url}\n\n"
        "Breast Health Studio Research Platform"
    )
    html_body = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 24px; }}
    .card {{ max-width: 560px; margin: 0 auto; background: #1e293b; border-radius: 12px; padding: 32px; border: 1px solid #334155; }}
    .brand {{ font-size: 18px; font-weight: 700; color: #14b8a6; margin-bottom: 24px; display: inline-block; }}
    h1 {{ font-size: 22px; color: #ffffff; margin-top: 0; margin-bottom: 16px; }}
    p {{ font-size: 15px; line-height: 1.6; color: #cbd5e1; margin: 0 0 16px; }}
    .btn {{ display: inline-block; background: #0d9488; color: #ffffff !important; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: 600; margin: 20px 0; }}
    .footer {{ margin-top: 32px; padding-top: 16px; border-top: 1px solid #334155; font-size: 12px; color: #64748b; }}
  </style>
</head>
<body>
  <div class="card">
    <span class="brand">BC Breast Health Studio</span>
    <h1>Welcome to Breast Health Studio</h1>
    <p>Hello <strong>{full_name}</strong>,</p>
    <p>Your research workspace account has been created successfully.</p>
    <p style="text-align: center;">
      <a href="{login_url}" class="btn">Sign In to Studio</a>
    </p>
    <div class="footer">
      Research &amp; Educational Platform. Not for autonomous clinical diagnosis.
    </div>
  </div>
</body>
</html>"""

    _send_via_smtp(
        to_email=email,
        subject=subject,
        text_body=text_body,
        html_body=html_body,
    )
