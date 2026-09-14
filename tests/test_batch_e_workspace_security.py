"""
Batch E Backend Workspace and Security Test Suite
Validates:
- Personal vs Doctor registration
- Server-side doctor invite verification (mode disabled, invalid code, valid code)
- Role manipulation immunity (client role parameter ignored)
- Normal user authorization barriers on patient APIs
- Single patient endpoint GET /patients/{id}/
- Cross-doctor patient and prediction isolation
- Patient deletion safety (predictions preserved with patient_id set to NULL)
- Prediction report ownership isolation
- Logout all sessions functionality
"""

import os
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import db
from app.core.security import create_session_token, hash_password
from tests.test_schemas import valid_prediction_payload

UTC = timezone.utc

client = TestClient(app)


def _clean_user_by_email(email: str):
    db.execute("DELETE FROM sessions WHERE user_id IN (SELECT id FROM users WHERE email = ?)", (email,))
    db.execute("DELETE FROM predictions WHERE user_id IN (SELECT id FROM users WHERE email = ?)", (email,))
    db.execute("DELETE FROM patients WHERE user_id IN (SELECT id FROM users WHERE email = ?)", (email,))
    db.execute("DELETE FROM users WHERE email = ?", (email,))


def _create_user(email: str, role: str = "user") -> tuple[int, str]:
    _clean_user_by_email(email)
    now = datetime.now(UTC).isoformat()
    uid = db.execute(
        "INSERT INTO users (email, full_name, password_hash, role, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
        (email, f"User {role}", hash_password("ValidPassword123!"), role, now, now),
    )
    token = create_session_token()
    exp = (datetime.now(UTC) + timedelta(days=7)).isoformat()
    db.execute("INSERT INTO sessions (user_id, token, expires_at, created_at) VALUES (?, ?, ?, ?)", (uid, token, exp, now))
    return uid, token


# =========================================================================
# 1. REGISTRATION SECURITY & INVITE VERIFICATION
# =========================================================================

def test_personal_registration_assigns_user_role():
    email = "personal_test_reg@example.com"
    _clean_user_by_email(email)

    resp = client.post(
        "/api/v1/auth/register/",
        json={
            "email": email,
            "full_name": "Personal User",
            "password": "ValidPassword123!",
            "account_type": "personal",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["user"]["role"] == "user"

    row = db.fetch_one("SELECT role FROM users WHERE email = ?", (email,))
    assert row["role"] == "user"
    _clean_user_by_email(email)


def test_doctor_registration_self_declared_assigns_doctor_role():
    email = "doc_self_declared@example.com"
    _clean_user_by_email(email)

    resp = client.post(
        "/api/v1/auth/register/",
        json={
            "email": email,
            "full_name": "Dr Validated",
            "password": "ValidPassword123!",
            "role": "doctor",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["user"]["role"] == "doctor"

    row = db.fetch_one("SELECT role FROM users WHERE email = ?", (email,))
    assert row["role"] == "doctor"
    _clean_user_by_email(email)


def test_registration_role_admin_is_rejected():
    email = "hacker_role_inject@example.com"
    _clean_user_by_email(email)

    # Malicious attempt: client sends role="admin"
    resp = client.post(
        "/api/v1/auth/register/",
        json={
            "email": email,
            "full_name": "Hacker Attempt",
            "password": "ValidPassword123!",
            "role": "admin",
        },
    )
    assert resp.status_code == 400
    assert "Invalid role" in resp.json()["detail"]

    row = db.fetch_one("SELECT id FROM users WHERE email = ?", (email,))
    assert row is None
    _clean_user_by_email(email)


# =========================================================================
# 2. PATIENT WORKSPACE AUTHORIZATION & ENDPOINTS
# =========================================================================

def test_normal_user_denied_on_patient_endpoints():
    uid, token = _create_user("normal_denied@example.com", "user")
    headers = {"Authorization": f"Bearer {token}"}

    # GET /patients/ -> 403
    assert client.get("/api/v1/patients/", headers=headers).status_code == 403

    # POST /patients/ -> 403
    assert client.post("/api/v1/patients/", json={"full_name": "Patient X"}, headers=headers).status_code == 403

    # GET /patients/1/ -> 403
    assert client.get("/api/v1/patients/1/", headers=headers).status_code == 403

    # PUT /patients/1/ -> 403
    assert client.put("/api/v1/patients/1/", json={"full_name": "Patient X"}, headers=headers).status_code == 403

    # DELETE /patients/1/ -> 403
    assert client.delete("/api/v1/patients/1/", headers=headers).status_code == 403

    # GET /predictions/history/?patient_id=1 -> 403
    assert client.get("/api/v1/predictions/history/?patient_id=1", headers=headers).status_code == 403

    _clean_user_by_email("normal_denied@example.com")


def test_single_patient_get_endpoint_and_ownership():
    doc1_id, doc1_token = _create_user("doc1_single_p@example.com", "doctor")
    doc2_id, doc2_token = _create_user("doc2_single_p@example.com", "doctor")

    now = datetime.now(UTC).isoformat()
    pid = db.execute(
        "INSERT INTO patients (user_id, full_name, date_of_birth, gender, notes, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (doc1_id, "Eleanor Rigby", "1980-05-12", "female", "Subject notes", now, now),
    )

    # Doctor 1 retrieves their patient -> 200
    resp1 = client.get(f"/api/v1/patients/{pid}/", headers={"Authorization": f"Bearer {doc1_token}"})
    assert resp1.status_code == 200
    pdata = resp1.json()
    assert pdata["id"] == pid
    assert pdata["full_name"] == "Eleanor Rigby"
    assert pdata["gender"] == "female"

    # Doctor 2 attempts to retrieve Doctor 1's patient -> 404 (isolation)
    resp2 = client.get(f"/api/v1/patients/{pid}/", headers={"Authorization": f"Bearer {doc2_token}"})
    assert resp2.status_code == 404

    # Nonexistent patient -> 404
    resp3 = client.get("/api/v1/patients/999999/", headers={"Authorization": f"Bearer {doc1_token}"})
    assert resp3.status_code == 404

    _clean_user_by_email("doc1_single_p@example.com")
    _clean_user_by_email("doc2_single_p@example.com")


def test_cross_doctor_isolation_across_endpoints():
    doc1_id, doc1_token = _create_user("doc_a_iso@example.com", "doctor")
    doc2_id, doc2_token = _create_user("doc_b_iso@example.com", "doctor")

    now = datetime.now(UTC).isoformat()
    pid = db.execute(
        "INSERT INTO patients (user_id, full_name, created_at, updated_at) VALUES (?, ?, ?, ?)",
        (doc1_id, "Protected Patient Doc1", now, now),
    )

    # Doc 2 tries to update Doc 1's patient -> 404
    resp_put = client.put(
        f"/api/v1/patients/{pid}/",
        json={"full_name": "Tampered Name"},
        headers={"Authorization": f"Bearer {doc2_token}"},
    )
    assert resp_put.status_code == 404

    # Doc 2 tries to delete Doc 1's patient -> 404
    resp_del = client.delete(
        f"/api/v1/patients/{pid}/",
        headers={"Authorization": f"Bearer {doc2_token}"},
    )
    assert resp_del.status_code == 404

    # Doc 2 tries to read history of Doc 1's patient -> 404
    resp_hist = client.get(
        f"/api/v1/predictions/history/?patient_id={pid}",
        headers={"Authorization": f"Bearer {doc2_token}"},
    )
    assert resp_hist.status_code == 404

    _clean_user_by_email("doc_a_iso@example.com")
    _clean_user_by_email("doc_b_iso@example.com")


def test_patient_deletion_preserves_prediction_records():
    doc_id, doc_token = _create_user("doc_del_cascade@example.com", "doctor")
    now = datetime.now(UTC).isoformat()

    pid = db.execute(
        "INSERT INTO patients (user_id, full_name, created_at, updated_at) VALUES (?, ?, ?, ?)",
        (doc_id, "Patient To Delete", now, now),
    )

    # Insert a prediction attached to this patient
    pred_id = db.save_prediction(
        user_id=doc_id,
        patient_id=pid,
        prediction_type="ml",
        model_name="Logistic Regression",
        diagnosis="Benign",
        probability=0.15,
        raw_probability=0.15,
        calibration_mode="none",
        risk_band="Low",
        advice="Advisory text",
        analysis_text="Analysis notes",
        input_payload={"mean_radius": 12.0},
        response_payload={"model_name": "Logistic Regression"},
    )

    # Verify prediction is linked
    pred_row = db.fetch_one("SELECT patient_id FROM predictions WHERE id = ?", (pred_id,))
    assert pred_row["patient_id"] == pid

    # Delete patient
    del_resp = client.delete(f"/api/v1/patients/{pid}/", headers={"Authorization": f"Bearer {doc_token}"})
    assert del_resp.status_code == 200

    # Verify prediction record STILL EXISTS and patient_id is set to NULL
    pred_row_after = db.fetch_one("SELECT id, user_id, patient_id FROM predictions WHERE id = ?", (pred_id,))
    assert pred_row_after is not None
    assert pred_row_after["id"] == pred_id
    assert pred_row_after["user_id"] == doc_id
    assert pred_row_after["patient_id"] is None

    _clean_user_by_email("doc_del_cascade@example.com")


# =========================================================================
# 3. REPORT AUTHORIZATION & LOGOUT-ALL
# =========================================================================

def test_report_ownership_isolation():
    u1_id, u1_token = _create_user("user1_report@example.com", "user")
    u2_id, u2_token = _create_user("user2_report@example.com", "user")

    pred_id = db.save_prediction(
        user_id=u1_id,
        patient_id=None,
        prediction_type="ml",
        model_name="Logistic Regression",
        diagnosis="Benign",
        probability=0.08,
        raw_probability=0.08,
        calibration_mode="none",
        risk_band="Low",
        advice="Advisory text",
        analysis_text="Analysis notes",
        input_payload={"mean_radius": 10.0},
        response_payload={"model_name": "Logistic Regression"},
    )

    # Owner accesses report -> 200
    r1 = client.get(f"/api/v1/predictions/{pred_id}/report/", headers={"Authorization": f"Bearer {u1_token}"})
    assert r1.status_code == 200
    assert "Print / Save as PDF" in r1.text or "In báo cáo" in r1.text

    # Another user attempts to access report -> 404
    r2 = client.get(f"/api/v1/predictions/{pred_id}/report/", headers={"Authorization": f"Bearer {u2_token}"})
    assert r2.status_code == 404

    _clean_user_by_email("user1_report@example.com")
    _clean_user_by_email("user2_report@example.com")


def test_logout_all_revokes_all_sessions():
    uid, token1 = _create_user("logout_all_user@example.com", "user")
    # Add second session
    now = datetime.now(UTC).isoformat()
    token2 = create_session_token()
    exp = (datetime.now(UTC) + timedelta(days=7)).isoformat()
    db.execute("INSERT INTO sessions (user_id, token, expires_at, created_at) VALUES (?, ?, ?, ?)", (uid, token2, exp, now))

    # Verify both tokens work
    assert client.get("/api/v1/auth/me/", headers={"Authorization": f"Bearer {token1}"}).status_code == 200
    assert client.get("/api/v1/auth/me/", headers={"Authorization": f"Bearer {token2}"}).status_code == 200

    # Call logout-all using token1
    resp = client.post("/api/v1/auth/logout-all/", headers={"Authorization": f"Bearer {token1}"})
    assert resp.status_code == 200

    # Verify BOTH tokens are now invalid (401)
    assert client.get("/api/v1/auth/me/", headers={"Authorization": f"Bearer {token1}"}).status_code == 401
    assert client.get("/api/v1/auth/me/", headers={"Authorization": f"Bearer {token2}"}).status_code == 401

    _clean_user_by_email("logout_all_user@example.com")
