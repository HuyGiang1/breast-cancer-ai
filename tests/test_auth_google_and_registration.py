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
        assert resp.json()["enabled"] is True

    with patch.dict(os.environ, {}, clear=True):
        resp = client.get("/api/v1/auth/google/config/")
        assert resp.status_code == 200
        assert resp.json()["client_id"] is None
        assert resp.json()["enabled"] is False


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
        mock_payload = {
            "aud": "wrong-client-id.apps.googleusercontent.com",
            "iss": "https://accounts.google.com",
            "email": "user@gmail.com",
            "email_verified": "true",
            "sub": "1234567890"
        }
        with patch("app.api.endpoints.google_id_token.verify_oauth2_token", return_value=mock_payload):
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
        mock_payload = {
            "aud": client_id,
            "iss": "https://accounts.google.com",
            "email": email,
            "email_verified": "true",
            "name": "Dr Google Researcher",
            "sub": sub
        }
        with patch("app.api.endpoints.google_id_token.verify_oauth2_token", return_value=mock_payload):
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
        mock_payload = {
            "aud": client_id,
            "iss": "https://accounts.google.com",
            "email": email,
            "email_verified": "true",
            "name": "Google User",
            "sub": sub
        }
        with patch("app.api.endpoints.google_id_token.verify_oauth2_token", return_value=mock_payload):
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


def test_google_link_requires_auth():
    resp = client.post(
        "/api/v1/auth/google/link/",
        json={"credential": "mock_credential"}
    )
    assert resp.status_code == 401


def test_google_link_and_unlink_flow():
    client_id = "configured-client-id.apps.googleusercontent.com"
    email = "link_flow_user@example.com"
    sub = "google-sub-flow-776655"
    db.execute("DELETE FROM oauth_accounts WHERE provider_subject = ?", (sub,))
    db.execute("DELETE FROM users WHERE email = ?", (email,))

    # Register local user
    reg_resp = client.post(
        "/api/v1/auth/register/",
        json={
            "email": email,
            "full_name": "Link Flow User",
            "password": "ValidPassword123!"
        }
    )
    token = reg_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    with patch.dict(os.environ, {"GOOGLE_CLIENT_ID": client_id}):
        # 1. Attempt link with email mismatch
        mismatch_payload = {
            "aud": client_id,
            "iss": "https://accounts.google.com",
            "email": "different_email@gmail.com",
            "email_verified": "true",
            "sub": sub
        }
        with patch("app.api.endpoints.google_id_token.verify_oauth2_token", return_value=mismatch_payload):
            resp = client.post("/api/v1/auth/google/link/", json={"credential": "mock_google_token_1234567890"}, headers=headers)
            assert resp.status_code == 400
            assert "does not match your account email" in resp.json()["detail"]

        # 2. Successful link with matching email
        matching_payload = {
            "aud": client_id,
            "iss": "https://accounts.google.com",
            "email": email,
            "email_verified": "true",
            "sub": sub
        }
        with patch("app.api.endpoints.google_id_token.verify_oauth2_token", return_value=matching_payload):
            resp = client.post("/api/v1/auth/google/link/", json={"credential": "mock_google_token_1234567890"}, headers=headers)
            assert resp.status_code == 200
            assert resp.json()["connected"] is True
            assert resp.json()["provider"] == "google"

            # 3. Idempotent link
            resp_idem = client.post("/api/v1/auth/google/link/", json={"credential": "mock_google_token_1234567890"}, headers=headers)
            assert resp_idem.status_code == 200
            assert resp_idem.json()["connected"] is True

        # Check me endpoint reflects oauth account
        me_resp = client.get("/api/v1/auth/me/", headers=headers)
        assert me_resp.status_code == 200
        me_data = me_resp.json()
        assert me_data["has_password"] is True
        assert len(me_data["oauth_accounts"]) == 1
        assert me_data["oauth_accounts"][0]["provider"] == "google"

        # 4. Attempt to link this same Google account to another user
        other_email = "other_user_collision@example.com"
        db.execute("DELETE FROM users WHERE email = ?", (other_email,))
        reg2 = client.post(
            "/api/v1/auth/register/",
            json={
                "email": other_email,
                "full_name": "Other User",
                "password": "ValidPassword123!"
            }
        )
        token2 = reg2.json()["access_token"]
        headers2 = {"Authorization": f"Bearer {token2}"}

        matching_payload_other = {
            "aud": client_id,
            "iss": "https://accounts.google.com",
            "email": other_email,
            "email_verified": "true",
            "sub": sub  # same sub already linked to first user
        }
        with patch("app.api.endpoints.google_id_token.verify_oauth2_token", return_value=matching_payload_other):
            resp_coll = client.post("/api/v1/auth/google/link/", json={"credential": "mock_google_token_1234567890"}, headers=headers2)
            assert resp_coll.status_code == 409
            assert "already linked to another user" in resp_coll.json()["detail"]

        # 5. Unlink Google account (since user has password, this should succeed)
        unlink_resp = client.post("/api/v1/auth/google/unlink/", headers=headers)
        assert unlink_resp.status_code == 200
        assert "disconnected" in unlink_resp.json()["message"]

        # Verify me endpoint reflects unlinked state
        me_after = client.get("/api/v1/auth/me/", headers=headers)
        assert len(me_after.json()["oauth_accounts"]) == 0


def test_google_unlink_refused_without_password():
    client_id = "configured-client-id.apps.googleusercontent.com"
    email = "google_only_user@gmail.com"
    sub = "google-sub-only-112233"
    db.execute("DELETE FROM oauth_accounts WHERE provider_subject = ?", (sub,))
    db.execute("DELETE FROM users WHERE email = ?", (email,))

    with patch.dict(os.environ, {"GOOGLE_CLIENT_ID": client_id}):
        mock_payload = {
            "aud": client_id,
            "iss": "https://accounts.google.com",
            "email": email,
            "email_verified": "true",
            "name": "Google Only User",
            "sub": sub
        }
        with patch("app.api.endpoints.google_id_token.verify_oauth2_token", return_value=mock_payload):
            auth_resp = client.post(
                "/api/v1/auth/google/",
                json={"credential": "mock_google_token_1234567890"}
            )
            assert auth_resp.status_code == 200
            token = auth_resp.json()["access_token"]

        headers = {"Authorization": f"Bearer {token}"}
        # Check has_password is False
        me_resp = client.get("/api/v1/auth/me/", headers=headers)
        assert me_resp.json()["has_password"] is False

        # Unlink should fail to prevent lockout
        unlink_resp = client.post("/api/v1/auth/google/unlink/", headers=headers)
        assert unlink_resp.status_code == 400
        assert "Cannot disconnect Google account without a password set" in unlink_resp.json()["detail"]


def test_forgot_and_reset_password_flow():
    email = "forgot_test_user@example.com"
    original_pw = "OriginalSecret123!"
    new_pw = "NewSecretPassword456!"

    db.execute("DELETE FROM users WHERE email = ?", (email,))
    client.post(
        "/api/v1/auth/register/",
        json={
            "email": email,
            "full_name": "Forgot Tester",
            "password": original_pw
        }
    )

    # 1. Non-existent email returns generic message (no enumeration)
    non_exist_resp = client.post(
        "/api/v1/auth/forgot-password/",
        json={"email": "non_existent_account@example.com"}
    )
    assert non_exist_resp.status_code == 200
    assert "If an account exists" in non_exist_resp.json()["message"]
    assert non_exist_resp.json().get("reset_token") is None

    # 2. Existing email returns same generic message, plus reset_token in file mode
    with patch.dict(os.environ, {"APP_MAIL_MODE": "file", "APP_FRONTEND_URL": "http://localhost"}):
        forgot_resp = client.post(
            "/api/v1/auth/forgot-password/",
            json={"email": email}
        )
        assert forgot_resp.status_code == 200
        assert "If an account exists" in forgot_resp.json()["message"]
        reset_token = forgot_resp.json().get("reset_token")
        assert reset_token is not None

        # Verify token in DB
        db_token = db.fetch_one("SELECT * FROM password_reset_tokens WHERE token = ?", (reset_token,))
        assert db_token is not None

        # 3. Reset password with valid token
        reset_resp = client.post(
            "/api/v1/auth/reset-password/",
            json={"token": reset_token, "new_password": new_pw}
        )
        assert reset_resp.status_code == 200
        assert "Password updated successfully" in reset_resp.json()["message"]

        # 4. Old password must fail
        login_old = client.post(
            "/api/v1/auth/login/",
            json={"email": email, "password": original_pw}
        )
        assert login_old.status_code == 401

        # 5. New password must succeed
        login_new = client.post(
            "/api/v1/auth/login/",
            json={"email": email, "password": new_pw}
        )
        assert login_new.status_code == 200
        assert "access_token" in login_new.json()

        # 6. Reusing used token must fail
        reuse_resp = client.post(
            "/api/v1/auth/reset-password/",
            json={"token": reset_token, "new_password": "AnotherPassword789!"}
        )
        assert reuse_resp.status_code == 400
        assert "Invalid reset token" in reuse_resp.json()["detail"]


def test_reset_password_expired_token():
    email = "expired_token_user@example.com"
    db.execute("DELETE FROM users WHERE email = ?", (email,))
    reg = client.post(
        "/api/v1/auth/register/",
        json={"email": email, "full_name": "Expired Tester", "password": "Password123!"}
    )
    user_id = reg.json()["user"]["id"]

    # Insert an already-expired token directly
    token = "expired_token_abc123"
    db.execute(
        """
        INSERT INTO password_reset_tokens (user_id, token, expires_at, created_at)
        VALUES (?, ?, ?, ?)
        """,
        (user_id, token, "2020-01-01T00:00:00+00:00", "2020-01-01T00:00:00+00:00")
    )

    resp = client.post(
        "/api/v1/auth/reset-password/",
        json={"token": token, "new_password": "NewValidPass999!"}
    )
    assert resp.status_code == 400
    assert "Reset token expired" in resp.json()["detail"]


def test_registration_strict_account_type_validation():
    """Verify that invalid account_type values are strictly rejected with HTTP 422."""
    db.init()
    # 1. account_type='admin' must be rejected with 422
    resp_admin = client.post(
        "/api/v1/auth/register/",
        json={
            "email": "admin_attempt@example.com",
            "full_name": "Admin Attempt",
            "password": "ValidPassword123!",
            "account_type": "admin"
        }
    )
    assert resp_admin.status_code == 422

    # 2. account_type='banana' must be rejected with 422
    resp_banana = client.post(
        "/api/v1/auth/register/",
        json={
            "email": "banana_attempt@example.com",
            "full_name": "Banana Attempt",
            "password": "ValidPassword123!",
            "account_type": "banana"
        }
    )
    assert resp_banana.status_code == 422

    # 3. account_type='personal' succeeds as role='user'
    email_pers = "strict_personal@example.com"
    db.execute("DELETE FROM users WHERE email = ?", (email_pers,))
    resp_pers = client.post(
        "/api/v1/auth/register/",
        json={
            "email": email_pers,
            "full_name": "Personal User",
            "password": "ValidPassword123!",
            "account_type": "personal"
        }
    )
    assert resp_pers.status_code == 200
    assert resp_pers.json()["user"]["role"] == "user"

    # 4. Attempting to inject role='doctor' or role='admin' with personal account cannot elevate
    email_inj = "injection_attempt@example.com"
    db.execute("DELETE FROM users WHERE email = ?", (email_inj,))
    resp_inj = client.post(
        "/api/v1/auth/register/",
        json={
            "email": email_inj,
            "full_name": "Injection Attempt",
            "password": "ValidPassword123!",
            "account_type": "personal",
            "role": "doctor"
        }
    )
    assert resp_inj.status_code == 200
    assert resp_inj.json()["user"]["role"] == "user"
