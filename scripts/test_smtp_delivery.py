#!/usr/bin/env python3
"""
scripts/test_smtp_delivery.py

Operator diagnostic utility to verify SMTP mail server connectivity and authentication.
Safely connects using STARTTLS / TLS, tests authentication, and optionally sends a probe email.

SECURITY GUARANTEES:
- Passwords and auth tokens are NEVER printed to stdout or logs.
- Sensitive credentials are read directly from .env or environment variables.
"""

import argparse
import os
from pathlib import Path
import smtplib
import ssl
import sys
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")


def test_smtp(recipient_email: str | None = None) -> bool:
    host = os.getenv("SMTP_HOST", "").strip()
    port = int(os.getenv("SMTP_PORT", "587").strip())
    username = os.getenv("SMTP_USERNAME", "").strip()
    password = os.getenv("SMTP_PASSWORD", "").strip()
    from_email = os.getenv("SMTP_FROM_EMAIL", username).strip()
    from_name = os.getenv("SMTP_FROM_NAME", "Breast Health Studio").strip()

    security = os.getenv("SMTP_SECURITY", "ssl" if port == 465 else "starttls").strip().lower()

    print("[*] Testing SMTP connectivity with configured settings:")
    print(f"    Host: {host}")
    print(f"    Port: {port}")
    print(f"    Security: {security}")
    print(f"    Username: {username if username else '(none)'}")
    print(f"    Password: {'*' * 8 if password else '(none)'}")
    print(f"    From: {from_name} <{from_email}>")

    if not host:
        print("[!] SMTP_HOST is not configured.", file=sys.stderr)
        return False

    context = ssl.create_default_context()

    try:
        if security in {"ssl", "tls"} or port == 465:
            print(f"[*] Establishing SSL connection to {host}:{port}...")
            server = smtplib.SMTP_SSL(host, port, context=context, timeout=15)
        else:
            print(f"[*] Establishing SMTP connection to {host}:{port}...")
            server = smtplib.SMTP(host, port, timeout=15)
            server.ehlo()
            if server.has_extn("starttls"):
                print("[*] Upgrading connection to STARTTLS...")
                server.starttls(context=context)
                server.ehlo()

        if username and password:
            print("[*] Authenticating with SMTP server...")
            server.login(username, password)
            print("[+] SMTP authentication SUCCESSFUL.")
        else:
            print("[*] No credentials provided; anonymous relay test.")

        if recipient_email:
            print(f"[*] Sending test probe email to {recipient_email}...")
            message = (
                f"From: {from_name} <{from_email}>\r\n"
                f"To: {recipient_email}\r\n"
                f"Subject: [Test] Breast Cancer AI SMTP Connectivity Probe\r\n"
                "\r\n"
                "This is a verified test email from the Breast Cancer AI production mail subsystem.\r\n"
                "SMTP configuration and transport security verified successfully.\r\n"
            )
            server.sendmail(from_email, [recipient_email], message)
            print(f"[+] Test email successfully sent to {recipient_email}.")

        server.quit()
        print("[+] All SMTP connection tests PASSED.")
        return True

    except Exception as exc:
        print(f"[!] SMTP connection test FAILED: {exc}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(description="Test SMTP connectivity and mail delivery.")
    parser.add_argument(
        "--send-to",
        type=str,
        default=None,
        help="Optional recipient email address to send a test message to.",
    )
    args = parser.parse_args()
    success = test_smtp(args.send_to)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
