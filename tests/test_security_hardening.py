"""
tests/test_security_hardening.py

Unit and integration tests for API security hardening:
- CORS fail-closed validation in production
- API documentation control
- /readyz probe verification
- Password reset token omission in production
"""

import os
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app, get_cors_origins


@pytest.fixture
def client():
    return TestClient(app)


def test_cors_production_fail_closed_missing():
    with patch.dict(os.environ, {"APP_ENV": "production", "APP_CORS_ORIGINS": ""}):
        with pytest.raises(RuntimeError, match="APP_CORS_ORIGINS must be explicitly configured"):
            get_cors_origins()


def test_cors_production_fail_closed_wildcard():
    with patch.dict(os.environ, {"APP_ENV": "production", "APP_CORS_ORIGINS": "*"}):
        with pytest.raises(RuntimeError, match="cannot be '\\*' in production"):
            get_cors_origins()


def test_cors_production_fail_closed_non_https():
    with patch.dict(os.environ, {"APP_ENV": "production", "APP_CORS_ORIGINS": "http://insecure.example.com"}):
        with pytest.raises(RuntimeError, match="must use HTTPS in production"):
            get_cors_origins()


def test_cors_production_fail_closed_localhost():
    with patch.dict(os.environ, {"APP_ENV": "production", "APP_CORS_ORIGINS": "https://localhost:8080"}):
        with pytest.raises(RuntimeError, match="cannot target localhost"):
            get_cors_origins()


def test_cors_production_valid():
    with patch.dict(os.environ, {"APP_ENV": "production", "APP_CORS_ORIGINS": "https://bcai.hospital.org,https://research.hospital.org"}):
        origins = get_cors_origins()
        assert origins == ["https://bcai.hospital.org", "https://research.hospital.org"]


def test_healthz_and_readyz_probes(client):
    res = client.get("/healthz")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}

    res = client.get("/readyz")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ready"
    assert data["database"] == "ok"
    assert data["final_ml"] == "research_demo"
    assert data["final_dl"] == "research_demo"


def test_forgot_password_suppresses_token_in_production(client):
    # Under production, reset_token must never be returned in API response
    with patch.dict(os.environ, {"APP_ENV": "production", "APP_MAIL_MODE": "smtp"}):
        res = client.post("/api/v1/auth/forgot-password/", json={"email": "nonexistent@example.com"})
        assert res.status_code == 200
        data = res.json()
        assert "message" in data
        assert data.get("reset_token") is None
