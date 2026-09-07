import os
from unittest.mock import patch, MagicMock
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import db

client = TestClient(app)


def test_public_registration_forces_user_role():
    db.init()
    email = "test_public_user_01@example.com"
    # Ensure clean state
    db.execute("DELETE FROM users WHERE email = ?", (email,))

    # Attempt to self-assign doctor role
    response = client.post(
        "/api/v1/auth/register/",
        json={
            "email": email,
            "full_name": "Dr Attempt",
            "password": "ValidPassword123!",
            "role": "doctor"
        }
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["user"]["email"] == email
    # Must be forced to "user"
    assert data["user"]["role"] == "user"
    assert "access_token" in data

    # Verify directly in database
    row = db.fetch_one("SELECT role FROM users WHERE email = ?", (email,))
    assert row["role"] == "user"


def test_duplicate_registration_returns_409():
    email = "test_dup_reg@example.com"
    db.execute("DELETE FROM users WHERE email = ?", (email,))

    resp1 = client.post(
        "/api/v1/auth/register/",
        json={
            "email": email,
            "full_name": "First User",
            "password": "ValidPassword123!"
        }
    )
    assert resp1.status_code == 200

    resp2 = client.post(
        "/api/v1/auth/register/",
        json={
            "email": email,
            "full_name": "Duplicate User",
            "password": "ValidPassword123!"
        }
    )
    assert resp2.status_code == 409
    assert "already registered" in resp2.json()["detail"].lower()


def test_registration_short_password_returns_422():
    resp = client.post(
        "/api/v1/auth/register/",
        json={
            "email": "short_pw@example.com",
            "full_name": "Short Pass",
            "password": "short"
        }
    )
    assert resp.status_code == 422


def test_google_config_endpoint():
    with patch.dict(os.environ, {"GOOGLE_CLIENT_ID": "test-client-id-123.apps.googleusercontent.com"}):
        resp = client.get("/api/v1/auth/google/config/")
        assert resp.status_code == 200
        assert resp.json()["client_id"] == "test-client-id-123.apps.googleusercontent.com"


def test_google_auth_without_configuration_returns_503():
    with patch.dict(os.environ, {}, clear=True):
        resp = client.post(
            "/api/v1/auth/google/",
            json={"credential": "mock_google_token_1234567890"}
        )
        assert resp.status_code == 503
        assert "not configured" in resp.json()["detail"]


def test_google_auth_token_audience_mismatch():
    client_id = "configured-client-id.apps.googleusercontent.com"
    with patch.dict(os.environ, {"GOOGLE_CLIENT_ID": client_id}):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "aud": "wrong-client-id.apps.googleusercontent.com",
            "iss": "https://accounts.google.com",
            "email": "user@gmail.com",
            "email_verified": "true",
            "sub": "1234567890"
        }
        with patch("httpx.get", return_value=mock_resp):
            resp = client.post(
                "/api/v1/auth/google/",
                json={"credential": "mock_google_token_1234567890"}
            )
            assert resp.status_code == 401
            assert "audience mismatch" in resp.json()["detail"]


def test_google_auth_new_user_success():
    client_id = "configured-client-id.apps.googleusercontent.com"
    email = "new_google_researcher@gmail.com"
    sub = "google-sub-unique-998877"
    db.execute("DELETE FROM oauth_accounts WHERE provider_subject = ?", (sub,))
    db.execute("DELETE FROM users WHERE email = ?", (email,))

    with patch.dict(os.environ, {"GOOGLE_CLIENT_ID": client_id}):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "aud": client_id,
            "iss": "https://accounts.google.com",
            "email": email,
            "email_verified": "true",
            "name": "Dr Google Researcher",
            "sub": sub
        }
        with patch("httpx.get", return_value=mock_resp):
            resp = client.post(
                "/api/v1/auth/google/",
                json={"credential": "mock_google_token_1234567890"}
            )
            assert resp.status_code == 200, resp.text
            data = resp.json()
            assert data["user"]["email"] == email
            # New google user role must strictly be "user"
            assert data["user"]["role"] == "user"
            assert "access_token" in data

            # Verify oauth_accounts entry
            oauth_entry = db.fetch_one(
                "SELECT * FROM oauth_accounts WHERE provider = 'google' AND provider_subject = ?",
                (sub,)
            )
            assert oauth_entry is not None
            assert oauth_entry["email"] == email


def test_google_auth_existing_password_account_collision_refuses_auto_link():
    """
    CRITICAL SECURITY CHECK:
    If verified Google email matches an existing password account but Google identity is not linked:
    DO NOT auto-link -> return 409 Conflict.
    """
    client_id = "configured-client-id.apps.googleusercontent.com"
    email = "existing_password_user@example.com"
    sub = "google-sub-different-332211"
    
    # Create existing password user
    db.execute("DELETE FROM oauth_accounts WHERE provider_subject = ?", (sub,))
    db.execute("DELETE FROM users WHERE email = ?", (email,))
    client.post(
        "/api/v1/auth/register/",
        json={
            "email": email,
            "full_name": "Password User",
            "password": "SecurePassword123!"
        }
    )

    with patch.dict(os.environ, {"GOOGLE_CLIENT_ID": client_id}):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "aud": client_id,
            "iss": "https://accounts.google.com",
            "email": email,
            "email_verified": "true",
            "name": "Google User",
            "sub": sub
        }
        with patch("httpx.get", return_value=mock_resp):
            resp = client.post(
                "/api/v1/auth/google/",
                json={"credential": "mock_google_token_1234567890"}
            )
            # Must return 409 and not auto-link
            assert resp.status_code == 409
            assert "An account already exists with this email" in resp.json()["detail"]

            # Verify no oauth account was created
            oauth_entry = db.fetch_one(
                "SELECT * FROM oauth_accounts WHERE provider = 'google' AND provider_subject = ?",
                (sub,)
            )
            assert oauth_entry is None
