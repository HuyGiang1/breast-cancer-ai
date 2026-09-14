import os
from unittest.mock import patch, MagicMock
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import db

client = TestClient(app)


def test_password_registration_self_selected_roles():
    db.init()
    user_email = "test_pw_reg_user@example.com"
    doc_email = "test_pw_reg_doctor@example.com"
    admin_email = "test_pw_reg_admin@example.com"
    db.execute("DELETE FROM users WHERE email IN (?, ?, ?)", (user_email, doc_email, admin_email))

    # 1. Register as regular user
    resp_user = client.post(
        "/api/v1/auth/register/",
        json={
            "email": user_email,
            "full_name": "Standard User",
            "password": "ValidPassword123!",
            "role": "user",
        },
    )
    assert resp_user.status_code == 200, resp_user.text
    assert resp_user.json()["user"]["role"] == "user"
    row_user = db.fetch_one("SELECT role FROM users WHERE email = ?", (user_email,))
    assert row_user["role"] == "user"

    # 2. Register as doctor (self-declared)
    resp_doc = client.post(
        "/api/v1/auth/register/",
        json={
            "email": doc_email,
            "full_name": "Dr Self Declared",
            "password": "ValidPassword123!",
            "role": "doctor",
        },
    )
    assert resp_doc.status_code == 200, resp_doc.text
    assert resp_doc.json()["user"]["role"] == "doctor"
    row_doc = db.fetch_one("SELECT role FROM users WHERE email = ?", (doc_email,))
    assert row_doc["role"] == "doctor"

    # 3. Reject disallowed roles (admin, manager, superuser, staff)
    for bad_role in ("admin", "manager", "superuser", "staff"):
        resp_bad = client.post(
            "/api/v1/auth/register/",
            json={
                "email": f"{bad_role}_{admin_email}",
                "full_name": "Attacker",
                "password": "ValidPassword123!",
                "role": bad_role,
            },
        )
        assert resp_bad.status_code == 400, f"Expected 400 for role '{bad_role}'"
        assert "Invalid role" in resp_bad.json()["detail"]


def test_password_login_preserves_stored_role():
    user_email = "test_login_user@example.com"
    doc_email = "test_login_doc@example.com"
    db.execute("DELETE FROM users WHERE email IN (?, ?)", (user_email, doc_email))

    client.post("/api/v1/auth/register/", json={"email": user_email, "full_name": "U", "password": "Password123!", "role": "user"})
    client.post("/api/v1/auth/register/", json={"email": doc_email, "full_name": "D", "password": "Password123!", "role": "doctor"})

    # Standard user login
    resp1 = client.post("/api/v1/auth/login/", json={"email": user_email, "password": "Password123!"})
    assert resp1.status_code == 200
    assert resp1.json()["user"]["role"] == "user"

    # Doctor login
    resp2 = client.post("/api/v1/auth/login/", json={"email": doc_email, "password": "Password123!"})
    assert resp2.status_code == 200
    assert resp2.json()["user"]["role"] == "doctor"

    # Client payload attempting role elevation during login must be ignored
    resp3 = client.post("/api/v1/auth/login/", json={"email": user_email, "password": "Password123!", "role": "doctor"})
    assert resp3.status_code == 200
    assert resp3.json()["user"]["role"] == "user"
    row = db.fetch_one("SELECT role FROM users WHERE email = ?", (user_email,))
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


def test_first_time_google_auth_requires_role_selection():
    client_id = "configured-client-id.apps.googleusercontent.com"
    email = "new_google_prompt_role@gmail.com"
    sub = "google-sub-unique-prompt-role-111"
    db.execute("DELETE FROM oauth_accounts WHERE provider_subject = ?", (sub,))
    db.execute("DELETE FROM users WHERE email = ?", (email,))

    with patch.dict(os.environ, {"GOOGLE_CLIENT_ID": client_id}):
        mock_payload = {
            "aud": client_id,
            "iss": "https://accounts.google.com",
            "email": email,
            "email_verified": "true",
            "name": "Prompt Role User",
            "sub": sub
        }
        with patch("app.api.endpoints.google_id_token.verify_oauth2_token", return_value=mock_payload):
            # 1. No role provided -> Must prompt for role selection, NOT create user yet
            resp = client.post(
                "/api/v1/auth/google/",
                json={"credential": "mock_google_token_1234567890"}
            )
            assert resp.status_code == 200, resp.text
            data = resp.json()
            assert data["needs_role_selection"] is True
            assert data["access_token"] is None or data["access_token"] == ""
            assert data["user"]["email"] == email

            # Assert no user row in DB yet
            row_uncreated = db.fetch_one("SELECT id FROM users WHERE email = ?", (email,))
            assert row_uncreated is None

            # 2. Rejection of invalid role
            resp_bad = client.post(
                "/api/v1/auth/google/",
                json={"credential": "mock_google_token_1234567890", "role": "admin"}
            )
            assert resp_bad.status_code == 400
            assert "Invalid role" in resp_bad.json()["detail"]


def test_first_time_google_auth_creates_user_and_doctor_roles():
    client_id = "configured-client-id.apps.googleusercontent.com"
    email_u = "new_google_user_role@gmail.com"
    sub_u = "google-sub-unique-role-user-222"
    email_d = "new_google_doc_role@gmail.com"
    sub_d = "google-sub-unique-role-doc-333"

    db.execute("DELETE FROM oauth_accounts WHERE provider_subject IN (?, ?)", (sub_u, sub_d))
    db.execute("DELETE FROM users WHERE email IN (?, ?)", (email_u, email_d))

    with patch.dict(os.environ, {"GOOGLE_CLIENT_ID": client_id}):
        # A. Create as role="user"
        payload_u = {"aud": client_id, "iss": "https://accounts.google.com", "email": email_u, "email_verified": "true", "name": "Google User", "sub": sub_u}
        with patch("app.api.endpoints.google_id_token.verify_oauth2_token", return_value=payload_u):
            resp_u = client.post("/api/v1/auth/google/", json={"credential": "mock_google_token_user_1234567890", "role": "user"})
            assert resp_u.status_code == 200
            assert resp_u.json()["user"]["role"] == "user"
            assert resp_u.json()["needs_role_selection"] is False
            assert "access_token" in resp_u.json()
            row_u = db.fetch_one("SELECT role FROM users WHERE email = ?", (email_u,))
            assert row_u["role"] == "user"

        # B. Create as role="doctor"
        payload_d = {"aud": client_id, "iss": "https://accounts.google.com", "email": email_d, "email_verified": "true", "name": "Google Doc", "sub": sub_d}
        with patch("app.api.endpoints.google_id_token.verify_oauth2_token", return_value=payload_d):
            resp_d = client.post("/api/v1/auth/google/", json={"credential": "mock_google_token_doctor_1234567890", "role": "doctor"})
            assert resp_d.status_code == 200
            assert resp_d.json()["user"]["role"] == "doctor"
            assert resp_d.json()["needs_role_selection"] is False
            assert "access_token" in resp_d.json()
            row_d = db.fetch_one("SELECT role FROM users WHERE email = ?", (email_d,))
            assert row_d["role"] == "doctor"


def test_returning_google_user_preserves_role_and_blocks_mutation():
    client_id = "configured-client-id.apps.googleusercontent.com"
    email = "immutable_google_user@gmail.com"
    sub = "google-sub-immutable-999"

    db.execute("DELETE FROM oauth_accounts WHERE provider_subject = ?", (sub,))
    db.execute("DELETE FROM users WHERE email = ?", (email,))

    with patch.dict(os.environ, {"GOOGLE_CLIENT_ID": client_id}):
        mock_payload = {"aud": client_id, "iss": "https://accounts.google.com", "email": email, "email_verified": "true", "name": "Immutable User", "sub": sub}
        with patch("app.api.endpoints.google_id_token.verify_oauth2_token", return_value=mock_payload):
            # First-time: create as user
            resp1 = client.post("/api/v1/auth/google/", json={"credential": "mock_google_token_1_1234567890", "role": "user"})
            assert resp1.status_code == 200
            user_id = resp1.json()["user"]["id"]
            assert resp1.json()["user"]["role"] == "user"

            # Returning login: client maliciously attempts to elevate role to "doctor"
            resp2 = client.post("/api/v1/auth/google/", json={"credential": "mock_google_token_2_1234567890", "role": "doctor"})
            assert resp2.status_code == 200
            assert resp2.json()["user"]["id"] == user_id
            # Role MUST remain user!
            assert resp2.json()["user"]["role"] == "user"
            assert resp2.json()["needs_role_selection"] is False

            # Verify directly in database
            row = db.fetch_one("SELECT role FROM users WHERE id = ?", (user_id,))
            assert row["role"] == "user"


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
                json={"credential": "mock_google_token_1234567890", "role": "user"}
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
    """Verify that invalid role and account_type values are strictly rejected with HTTP 400."""
    db.init()
    # 1. account_type='admin' must be rejected with 400
    resp_admin = client.post(
        "/api/v1/auth/register/",
        json={
            "email": "admin_attempt@example.com",
            "full_name": "Admin Attempt",
            "password": "ValidPassword123!",
            "account_type": "admin"
        }
    )
    assert resp_admin.status_code == 400
    assert "Invalid role" in resp_admin.json()["detail"]

    # 2. role='banana' must be rejected with 400
    resp_banana = client.post(
        "/api/v1/auth/register/",
        json={
            "email": "banana_attempt@example.com",
            "full_name": "Banana Attempt",
            "password": "ValidPassword123!",
            "role": "banana"
        }
    )
    assert resp_banana.status_code == 400
    assert "Invalid role" in resp_banana.json()["detail"]

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


def test_profile_update_cannot_mutate_role():
    email = "profile_role_mutate_test@example.com"
    db.execute("DELETE FROM users WHERE email = ?", (email,))
    reg_resp = client.post(
        "/api/v1/auth/register/",
        json={
            "email": email,
            "full_name": "Original Name",
            "password": "ValidPassword123!",
            "role": "user"
        }
    )
    assert reg_resp.status_code == 200
    token = reg_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Attempt to mutate role via profile update
    upd_resp = client.put(
        "/api/v1/auth/profile/",
        json={"full_name": "New Name", "role": "doctor"},
        headers=headers
    )
    assert upd_resp.status_code == 200
    # Role must still be user
    assert upd_resp.json()["role"] == "user"
    assert upd_resp.json()["full_name"] == "New Name"

    row = db.fetch_one("SELECT role, full_name FROM users WHERE email = ?", (email,))
    assert row["role"] == "user"
    assert row["full_name"] == "New Name"


def test_ui_disclaimers_and_role_immutability():
    # 1. Check register.html contains the self-declared doctor research disclaimer
    with open("frontend/register.html", "r", encoding="utf-8") as f:
        reg_html = f.read()
    assert "Doctor role is self-declared for research and demonstration purposes. Professional credentials are not verified." in reg_html

    # 2. Check role-modal.js contains the modal copy and disclaimers
    with open("frontend/js/components/role-modal.js", "r", encoding="utf-8") as f:
        modal_js = f.read()
    assert "Choose how you want to use Breast Health Studio" in modal_js
    assert "Doctor role is self-declared for research and demonstration purposes. Professional credentials are not verified." in modal_js
    assert "Regular User" in modal_js
    assert "Doctor / Healthcare Professional" in modal_js

    # 3. Check profile.html and profile.js do NOT contain role-switch controls
    with open("frontend/pages/profile.html", "r", encoding="utf-8") as f:
        prof_html = f.read()
    assert "Switch to Doctor" not in prof_html
    assert "Switch to User" not in prof_html

    with open("frontend/js/pages/profile.js", "r", encoding="utf-8") as f:
        prof_js = f.read()
    assert "Switch to Doctor" not in prof_js
    assert "Switch to User" not in prof_js
    assert "Role Immutability Policy:" in prof_js
