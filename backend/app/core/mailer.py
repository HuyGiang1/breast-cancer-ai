import json
import os
import smtplib
from pathlib import Path
from email.message import EmailMessage

from app.core.database import PROJECT_ROOT, utc_now_iso


MAIL_MODE = os.getenv("APP_MAIL_MODE", "file").strip().lower()
OUTBOX_DIR = PROJECT_ROOT / "backend" / "data" / "outbox"
OUTBOX_DIR.mkdir(parents=True, exist_ok=True)
PASSWORD_RESET_OUTBOX = OUTBOX_DIR / "password_reset.jsonl"
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com").strip()
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "").strip()
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "").strip()
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", SMTP_USERNAME).strip()
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "BreastCare Mint").strip()
FRONTEND_URL = os.getenv("APP_FRONTEND_URL", "http://127.0.0.1:8080").rstrip("/")


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

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as server:
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(msg)


def _write_reset_token_to_file(*, email: str, reset_token: str, expires_at: str) -> None:
    payload = {
        "type": "password_reset",
        "email": email,
        "reset_token": reset_token,
        "expires_at": expires_at,
        "created_at": utc_now_iso(),
    }
    with PASSWORD_RESET_OUTBOX.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")


def send_password_reset_email(*, email: str, reset_token: str, expires_at: str) -> None:
    if MAIL_MODE == "file":
        _write_reset_token_to_file(email=email, reset_token=reset_token, expires_at=expires_at)
        return

    recovery_url = f"{FRONTEND_URL}/#recovery"
    text_body = (
        "Ban da gui yeu cau dat lai mat khau cho BreastCare Mint.\n\n"
        f"Reset token: {reset_token}\n"
        f"Het han luc: {expires_at}\n\n"
        f"Mo trang nay de nhap token va dat lai mat khau: {recovery_url}\n\n"
        "Neu ban khong thuc hien yeu cau nay, hay bo qua email nay."
    )
    html_body = f"""
        <div style="font-family:Arial,sans-serif;line-height:1.6;color:#16332b;">
            <h2 style="margin-bottom:12px;">Dat lai mat khau BreastCare Mint</h2>
            <p>Ban da gui yeu cau dat lai mat khau cho tai khoan nay.</p>
            <p><strong>Reset token:</strong> {reset_token}</p>
            <p><strong>Het han:</strong> {expires_at}</p>
            <p>
                Mo trang
                <a href="{recovery_url}">{recovery_url}</a>
                de nhap token va dat lai mat khau.
            </p>
            <p>Neu ban khong thuc hien yeu cau nay, hay bo qua email nay.</p>
        </div>
    """
    _send_via_smtp(
        to_email=email,
        subject="BreastCare Mint - Dat lai mat khau",
        text_body=text_body,
        html_body=html_body,
    )


def send_welcome_email(*, email: str, full_name: str) -> None:
    if MAIL_MODE == "file":
        return

    login_url = f"{FRONTEND_URL}/#login"
    text_body = (
        f"Xin chao {full_name},\n\n"
        "Tai khoan BreastCare Mint cua ban da duoc tao thanh cong.\n"
        f"Ban co the dang nhap tai: {login_url}\n\n"
        "Cam on ban da su dung he thong."
    )
    html_body = f"""
        <div style="font-family:Arial,sans-serif;line-height:1.6;color:#16332b;">
            <h2 style="margin-bottom:12px;">Chao mung den voi BreastCare Mint</h2>
            <p>Xin chao <strong>{full_name}</strong>,</p>
            <p>Tai khoan cua ban da duoc tao thanh cong.</p>
            <p>
                Dang nhap tai:
                <a href="{login_url}">{login_url}</a>
            </p>
            <p>Cam on ban da su dung he thong.</p>
        </div>
    """
    _send_via_smtp(
        to_email=email,
        subject="BreastCare Mint - Chao mung ban",
        text_body=text_body,
        html_body=html_body,
    )
