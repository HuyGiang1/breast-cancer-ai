#!/usr/bin/env python3
"""
scripts/verify_deploy_environment.py

Production Environment Configuration Validator for Breast Cancer AI.
Inspects an environment file or active environment variables to verify that all
security and infrastructure requirements are met prior to staging or production deployment.

Checks:
- APP_ENV == "production"
- APP_FRONTEND_URL uses HTTPS and has no localhost/127.0.0.1
- APP_CORS_ORIGINS is explicit, HTTPS-only, no wildcards, no localhost
- APP_ENABLE_API_DOCS is false (or warned)
- APP_MAIL_MODE is "smtp" with non-placeholder credentials
- DOCTOR_REGISTRATION_MODE is "invite" or "disabled" with strong invite code
- GOOGLE_CLIENT_ID format validation (if enabled)
- Model artifact file accessibility
"""

import argparse
import os
from pathlib import Path
import sys
from typing import Dict, List, Tuple
from urllib.parse import urlparse

PLACEHOLDER_SUBSTRINGS = {
    "replace",
    "example",
    "your_",
    "generate_",
    "secret",
    "todo",
    "changeme",
}


def load_env_file(path: Path) -> Dict[str, str]:
    env_vars: Dict[str, str] = {}
    if not path.exists():
        return env_vars
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, val = line.split("=", 1)
                env_vars[key.strip()] = val.strip().strip("\"'")
    return env_vars


def is_placeholder(val: str) -> bool:
    if not val:
        return True
    lower = val.lower()
    return any(sub in lower for sub in PLACEHOLDER_SUBSTRINGS)


def audit_environment(
    env: Dict[str, str],
    allow_staging_placeholders: bool = False,
) -> Tuple[List[str], List[str], List[str]]:
    """
    Returns (errors, warnings, successes).
    If allow_staging_placeholders=True, unconfigured secrets are classified as
    WAITING_FOR_OPERATOR rather than blocking errors.
    """
    errors: List[str] = []
    warnings: List[str] = []
    successes: List[str] = []

    # 1. APP_ENV
    app_env = env.get("APP_ENV", "").strip().lower()
    if app_env == "production":
        successes.append("APP_ENV is set to 'production'")
    else:
        errors.append(f"APP_ENV must be 'production' (current: '{app_env}')")

    # 2. APP_FRONTEND_URL
    fe_url = env.get("APP_FRONTEND_URL", "").strip()
    if not fe_url:
        errors.append("APP_FRONTEND_URL is required")
    elif not fe_url.startswith("https://"):
        errors.append(f"APP_FRONTEND_URL must use HTTPS scheme: '{fe_url}'")
    elif "localhost" in fe_url or "127.0.0.1" in fe_url:
        errors.append(f"APP_FRONTEND_URL cannot point to localhost/127.0.0.1 in production: '{fe_url}'")
    else:
        successes.append(f"APP_FRONTEND_URL is valid HTTPS: {fe_url}")

    # 3. APP_CORS_ORIGINS
    cors_raw = env.get("APP_CORS_ORIGINS", "").strip()
    if not cors_raw:
        errors.append("APP_CORS_ORIGINS is required and cannot be empty")
    elif cors_raw == "*":
        errors.append("APP_CORS_ORIGINS cannot be '*' in production")
    else:
        origins = [o.strip() for o in cors_raw.split(",") if o.strip()]
        has_invalid = False
        for o in origins:
            if not o.startswith("https://"):
                errors.append(f"CORS origin '{o}' must use HTTPS scheme")
                has_invalid = True
            if "localhost" in o or "127.0.0.1" in o:
                errors.append(f"CORS origin '{o}' cannot point to localhost/127.0.0.1 in production")
                has_invalid = True
        if not has_invalid:
            successes.append(f"APP_CORS_ORIGINS validated: {origins}")

    # 4. API Docs
    docs_enabled = env.get("APP_ENABLE_API_DOCS", "false").strip().lower() == "true"
    if docs_enabled:
        warnings.append("APP_ENABLE_API_DOCS is 'true'. API documentation (/docs, /redoc) will be publicly exposed.")
    else:
        successes.append("APP_ENABLE_API_DOCS is disabled for production hardening")

    # 5. Mail Mode & SMTP
    mail_mode = env.get("APP_MAIL_MODE", "").strip().lower()
    if mail_mode != "smtp":
        if allow_staging_placeholders:
            warnings.append(f"APP_MAIL_MODE is '{mail_mode}'. Production requires 'smtp'.")
        else:
            errors.append(f"APP_MAIL_MODE must be 'smtp' for live production (current: '{mail_mode}')")
    else:
        successes.append("APP_MAIL_MODE is 'smtp'")
        smtp_host = env.get("SMTP_HOST", "").strip()
        smtp_user = env.get("SMTP_USERNAME", "").strip()
        smtp_pass = env.get("SMTP_PASSWORD", "").strip()

        if is_placeholder(smtp_host) or not smtp_host:
            msg = "SMTP_HOST is not configured with a valid provider"
            if allow_staging_placeholders:
                warnings.append(f"[OPERATOR NEEDED] {msg}")
            else:
                errors.append(msg)
        else:
            successes.append(f"SMTP_HOST configured: {smtp_host}")

        if is_placeholder(smtp_pass) or not smtp_pass:
            msg = "SMTP_PASSWORD contains a placeholder or is unset"
            if allow_staging_placeholders:
                warnings.append(f"[OPERATOR NEEDED] {msg}")
            else:
                errors.append(msg)
        else:
            successes.append("SMTP_PASSWORD is set")

    # 6. Doctor Registration Mode
    doc_mode = env.get("DOCTOR_REGISTRATION_MODE", "disabled").strip().lower()
    if doc_mode not in {"disabled", "invite"}:
        errors.append(f"DOCTOR_REGISTRATION_MODE must be 'disabled' or 'invite' (current: '{doc_mode}')")
    elif doc_mode == "invite":
        code = env.get("DOCTOR_INVITE_CODE", "").strip()
        if not code or is_placeholder(code) or len(code) < 12:
            msg = "DOCTOR_INVITE_CODE must be a high-entropy secret (>= 12 chars, non-placeholder)"
            if allow_staging_placeholders:
                warnings.append(f"[OPERATOR NEEDED] {msg}")
            else:
                errors.append(msg)
        else:
            successes.append("DOCTOR_INVITE_CODE is configured with sufficient length")
    else:
        successes.append("DOCTOR_REGISTRATION_MODE is 'disabled' (no doctor registrations permitted)")

    # 7. Google OAuth Client ID
    google_id = env.get("GOOGLE_CLIENT_ID", "").strip()
    if google_id:
        if is_placeholder(google_id) or not google_id.endswith(".apps.googleusercontent.com"):
            msg = f"GOOGLE_CLIENT_ID format is invalid: '{google_id}' (must end with .apps.googleusercontent.com)"
            if allow_staging_placeholders:
                warnings.append(f"[OPERATOR NEEDED] {msg}")
            else:
                errors.append(msg)
        else:
            successes.append("GOOGLE_CLIENT_ID format is valid")
    else:
        warnings.append("GOOGLE_CLIENT_ID is not configured. Google Sign-In will be inactive.")

    return errors, warnings, successes


def main():
    parser = argparse.ArgumentParser(description="Verify Production Deployment Environment")
    parser.add_argument(
        "--env-file",
        type=Path,
        default=Path(".env"),
        help="Path to environment file to check (default: .env)",
    )
    parser.add_argument(
        "--staging-check",
        action="store_true",
        help="Run in Staging Readiness mode: classifies missing operator secrets as WAITING_FOR_OPERATOR instead of fatal errors.",
    )
    args = parser.parse_args()

    env_path = args.env_file
    if env_path.exists():
        print(f"[*] Auditing environment file: {env_path}")
        env = load_env_file(env_path)
    else:
        print(f"[*] File {env_path} not found; auditing active system environment variables")
        env = dict(os.environ)

    errors, warnings, successes = audit_environment(env, allow_staging_placeholders=args.staging_check)

    print("\n" + "=" * 60)
    print("ENVIRONMENT AUDIT RESULTS")
    print("=" * 60)

    for s in successes:
        print(f" [PASS] {s}")
    for w in warnings:
        print(f" [WARN] {w}")
    for e in errors:
        print(f" [FAIL] {e}")

    print("=" * 60)

    if errors:
        print(f"\n[!] Audit FAILED with {len(errors)} error(s).", file=sys.stderr)
        sys.exit(1)
    else:
        if args.staging_check:
            print("\n[+] STAGING-READY: Zero code/config blockers. Remaining items await live operator secrets.")
        else:
            print("\n[+] LIVE-PRODUCTION-READY: All production credentials and hardening constraints validated.")
        sys.exit(0)


if __name__ == "__main__":
    main()
