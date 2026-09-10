from datetime import datetime, timedelta, timezone
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import db
from app.core.security import create_session_token, hash_password
from tests.test_schemas import valid_prediction_payload

UTC = timezone.utc



@pytest.fixture
def client():
    with patch("app.api.endpoints.ai_advisor_service.advice_for_single") as mock_advice:
        mock_advice.return_value = {
            "advice": "Test advisory guidance.",
            "provider": "mock",
            "model": "mock-model",
        }
        yield TestClient(app)



def _create_user_and_token(email: str, role: str) -> tuple[int, str]:
    db.execute("DELETE FROM sessions WHERE user_id IN (SELECT id FROM users WHERE email = ?)", (email,))
    db.execute("DELETE FROM users WHERE email = ?", (email,))
    now = datetime.now(UTC).isoformat()
    user_id = db.execute(
        "INSERT INTO users (email, password_hash, full_name, role, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
        (email, hash_password("Password123!"), f"Test {role.title()}", role, now, now),
    )
    token = create_session_token()
    expires_at = (datetime.now(UTC) + timedelta(days=1)).isoformat()
    db.execute("INSERT INTO sessions (user_id, token, expires_at, created_at) VALUES (?, ?, ?, ?)", (user_id, token, expires_at, now))
    return user_id, token


def test_normal_user_cannot_pass_patient_id(client):
    user_id, token = _create_user_and_token("normal_user_ml_test@test.local", "user")

    # Try to predict with patient_id=1
    payload = valid_prediction_payload()
    resp = client.post(
        "/api/v1/predict/?patient_id=1",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403
    assert "doctor" in resp.json().get("detail", "").lower()


def test_doctor_cannot_predict_on_unowned_patient(client):
    doc1_id, token1 = _create_user_and_token("doc1_ml_test@test.local", "doctor")
    doc2_id, token2 = _create_user_and_token("doc2_ml_test@test.local", "doctor")

    now = datetime.now(UTC).isoformat()
    # Patient belongs to doc2
    p_id = db.execute(
        "INSERT INTO patients (user_id, full_name, date_of_birth, gender, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
        (doc2_id, "Patient of Doc2", "1980-01-01", "female", now, now),
    )


    # Doc1 tries to predict on Doc2's patient
    payload = valid_prediction_payload()
    resp = client.post(
        f"/api/v1/predict/?patient_id={p_id}",
        json=payload,
        headers={"Authorization": f"Bearer {token1}"},
    )
    assert resp.status_code == 404

    # Doc2 predicts on their own patient -> SUCCESS
    resp2 = client.post(
        f"/api/v1/predict/?patient_id={p_id}",
        json=payload,
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert resp2.status_code == 200
    data = resp2.json()
    assert data["prediction_id"] is not None

