#!/usr/bin/env python3
"""
scripts/render_nginx_config.py

Renders production, staging, or bootstrap Nginx configuration from templates.
Guarantees:
1. Replaces domain name and SSL certificate paths.
2. Applies strict mode-based HSTS policies:
   - bootstrap: HTTP-only challenge responder (no TLS/HSTS).
   - staging: HSTS omitted (safe, zero-risk, no preload).
   - production: max-age=31536000 without includeSubDomains or preload.
3. Fails closed with exit code 1 if any unexpanded ${...} placeholders remain.
"""

import argparse
import os
from pathlib import Path
import re
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROD_TEMPLATE = PROJECT_ROOT / "deploy" / "nginx.production.conf.template"
DEFAULT_BOOTSTRAP_TEMPLATE = PROJECT_ROOT / "deploy" / "nginx.bootstrap.conf.template"
DEFAULT_OUTPUT = PROJECT_ROOT / "deploy" / "nginx.production.conf"


def check_unexpanded_vars(content: str) -> list[str]:
    """Returns a list of unexpanded ${...} placeholders found in content."""
    return [f"${{{m}}}" for m in sorted(set(re.findall(r"\$\{([A-Za-z0-9_]+)\}", content)))]


def render_nginx_config(
    server_name: str,
    ssl_cert_path: str | None = None,
    ssl_key_path: str | None = None,
    mode: str = "staging",
    template_path: Path | None = None,
    output_path: Path = DEFAULT_OUTPUT,
) -> str:
    mode = mode.lower().strip()
    if mode not in {"staging", "production", "bootstrap"}:
        raise ValueError(f"Invalid mode '{mode}'. Must be 'staging', 'production', or 'bootstrap'.")

    # Select default template if not explicitly specified
    if template_path is None:
        template_path = DEFAULT_BOOTSTRAP_TEMPLATE if mode == "bootstrap" else DEFAULT_PROD_TEMPLATE

    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")

    # Default SSL cert paths if not provided
    if not ssl_cert_path:
        ssl_cert_path = f"/etc/letsencrypt/live/{server_name}/fullchain.pem"
    if not ssl_key_path:
        ssl_key_path = f"/etc/letsencrypt/live/{server_name}/privkey.pem"

    # Define mode-based HSTS header
    if mode == "staging":
        # Staging policy: Do NOT send HSTS header; omit HSTS to prevent domain pinning
        hsts_directive = "# HSTS omitted for staging deployment"
    elif mode == "production":
        # Production initial policy: max-age 1 year, NO includeSubDomains, NO preload until post-cutover verification
        hsts_directive = 'add_header Strict-Transport-Security "max-age=31536000" always;'
    else:
        hsts_directive = ""

    template_content = template_path.read_text(encoding="utf-8")

    # Substitute variables
    rendered = template_content
    rendered = rendered.replace("${SERVER_NAME}", server_name)
    rendered = rendered.replace("${SSL_CERT_PATH}", ssl_cert_path)
    rendered = rendered.replace("${SSL_KEY_PATH}", ssl_key_path)
    rendered = rendered.replace("${HSTS_DIRECTIVE}", hsts_directive)

    # Fail closed if any unresolved placeholders remain
    unresolved = check_unexpanded_vars(rendered)
    if unresolved:
        raise ValueError(
            f"Unresolved placeholders remain in rendered Nginx config: {unresolved}"
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered, encoding="utf-8")
    return rendered


def main():
    parser = argparse.ArgumentParser(description="Render Nginx Configuration from Template")
    parser.add_argument(
        "--server-name",
        type=str,
        default=os.getenv("SERVER_NAME", "bcai.example.com"),
        help="Server FQDN (default: env SERVER_NAME or bcai.example.com)",
    )
    parser.add_argument(
        "--ssl-cert",
        type=str,
        default=os.getenv("SSL_CERT_PATH", None),
        help="Full path to TLS fullchain certificate",
    )
    parser.add_argument(
        "--ssl-key",
        type=str,
        default=os.getenv("SSL_KEY_PATH", None),
        help="Full path to TLS private key",
    )
    parser.add_argument(
        "--mode",
        choices=["staging", "production", "bootstrap"],
        default=os.getenv("DEPLOYMENT_MODE", "staging"),
        help="Deployment mode (default: staging)",
    )
    parser.add_argument(
        "--template",
        type=Path,
        default=None,
        help="Explicit template file path (optional)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Output configuration path (default: deploy/nginx.production.conf)",
    )

    args = parser.parse_args()

    try:
        render_nginx_config(
            server_name=args.server_name,
            ssl_cert_path=args.ssl_cert,
            ssl_key_path=args.ssl_key,
            mode=args.mode,
            template_path=args.template,
            output_path=args.output,
        )
        print(f"[+] Successfully rendered Nginx config ({args.mode} mode) -> {args.output}")
    except Exception as exc:
        print(f"[!] Rendering failed: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
