"""
tests/test_nginx_rendering.py

Unit tests for Nginx configuration template rendering and container contract validation:
- Staging mode: HSTS header deliberately omitted to prevent domain pinning prior to production.
- Production mode: HSTS max-age=31536000 only, strictly without includeSubDomains or preload.
- Bootstrap mode: HTTP-only port 80 ACME webroot challenge for Let's Encrypt issuance.
- Strict fail-closed validation if unexpanded variables remain.
- Backend Dockerfile non-root application user contract.
"""

import re
from pathlib import Path
import pytest
from scripts.render_nginx_config import render_nginx_config, check_unexpanded_vars


ROOT_DIR = Path(__file__).resolve().parent.parent


def test_render_nginx_config_staging(tmp_path):
    out_file = tmp_path / "nginx.staging.conf"
    rendered = render_nginx_config(
        mode="staging",
        server_name="staging.breasthealth.org",
        ssl_cert_path="/etc/letsencrypt/live/staging.breasthealth.org/fullchain.pem",
        ssl_key_path="/etc/letsencrypt/live/staging.breasthealth.org/privkey.pem",
        output_path=out_file,
    )

    assert out_file.exists()
    assert "server_name staging.breasthealth.org;" in rendered
    assert "ssl_certificate /etc/letsencrypt/live/staging.breasthealth.org/fullchain.pem;" in rendered
    assert "ssl_certificate_key /etc/letsencrypt/live/staging.breasthealth.org/privkey.pem;" in rendered
    # Staging must NOT include HSTS header (and definitely no preload or includeSubDomains)
    assert "Strict-Transport-Security" not in rendered
    assert "preload" not in rendered
    assert "includeSubDomains" not in rendered
    # Obsolete header X-XSS-Protection must not be present
    assert "X-XSS-Protection" not in rendered
    # No unexpanded ${...} variables
    assert check_unexpanded_vars(rendered) == []


def test_render_nginx_config_production(tmp_path):
    out_file = tmp_path / "nginx.prod.conf"
    rendered = render_nginx_config(
        mode="production",
        server_name="app.breasthealth.org",
        ssl_cert_path="/etc/letsencrypt/live/app.breasthealth.org/fullchain.pem",
        ssl_key_path="/etc/letsencrypt/live/app.breasthealth.org/privkey.pem",
        output_path=out_file,
    )

    assert out_file.exists()
    assert "server_name app.breasthealth.org;" in rendered
    assert "Strict-Transport-Security" in rendered
    assert 'max-age=31536000" always;' in rendered
    # Must NOT include includeSubDomains or preload
    assert "preload" not in rendered
    assert "includeSubDomains" not in rendered
    assert check_unexpanded_vars(rendered) == []


def test_render_nginx_config_bootstrap(tmp_path):
    out_file = tmp_path / "nginx.boot.conf"
    rendered = render_nginx_config(
        mode="bootstrap",
        server_name="staging.breasthealth.org",
        output_path=out_file,
    )

    assert out_file.exists()
    assert "server_name staging.breasthealth.org;" in rendered
    assert "location /.well-known/acme-challenge/ {" in rendered
    assert "root /var/www/certbot;" in rendered
    # Must be HTTP-only; no ssl directives
    assert "listen 443" not in rendered
    assert "Strict-Transport-Security" not in rendered
    assert check_unexpanded_vars(rendered) == []


def test_render_nginx_config_fails_on_invalid_mode():
    with pytest.raises(ValueError, match="Invalid mode 'unknown'"):
        render_nginx_config(
            mode="unknown",
            server_name="staging.breasthealth.org",
        )


def test_unexpanded_variables_detection():
    sample_with_vars = "server_name ${SERVER_NAME}; proxy_pass http://${BACKEND_UPSTREAM};"
    unexpanded = check_unexpanded_vars(sample_with_vars)
    assert set(unexpanded) == {"${SERVER_NAME}", "${BACKEND_UPSTREAM}"}


def test_backend_dockerfile_non_root_contract():
    dockerfile_path = ROOT_DIR / "backend" / "Dockerfile"
    assert dockerfile_path.exists(), "backend/Dockerfile must exist"
    content = dockerfile_path.read_text(encoding="utf-8")

    # Contract 1: Must create unprivileged user/group
    assert re.search(r"useradd\s+.*appuser", content), "Dockerfile must create appuser"
    # Contract 2: Must explicitly switch to USER appuser before CMD
    assert "USER appuser" in content, "Dockerfile must set USER appuser"
    # Contract 3: Ensure runtime dirs chowned to appuser
    assert "chown -R appuser:appgroup" in content, "Dockerfile must chown runtime directories to appuser:appgroup"
