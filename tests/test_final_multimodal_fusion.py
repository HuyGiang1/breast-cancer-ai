"""Automated tests for final multimodal experimental fusion contract (Batch D).

Verifies:
1. Exact formula: combined = 0.4 * ML_RAW + 0.6 * DL_RAW
2. DL calibrated probability does not alter combined score
3. Schema metadata: canonical fields, 0.5 software midpoint, unpaired disclaimer
4. Agreement and disagreement state calculation
5. Base64 Grad-CAM stripping before SQLite database persistence
6. Patient context authorization & single shared patient binding
"""

from __future__ import annotations

import io
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.main import app
from app.core.database import db
from app.core.security import create_session_token, hash_password
from tests.test_schemas import valid_prediction_payload

UTC = timezone.utc
BENIGN_DEMO_PATH = Path("frontend/assets/demo-images/demo-benign-mammogram.png")
MALIGNANT_DEMO_PATH = Path("frontend/assets/demo-images/demo-malignant-mammogram.png")


@pytest.fixture
def client():
    with patch("app.api.endpoints.ai_advisor_service.advice_for_multimodal") as mock_advice:
        mock_advice.return_value = {
            "advice": "Test experimental multimodal guidance.",
            "provider": "mock",
            "model": "mock-fusion-model",
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
    db.execute(
        "INSERT INTO sessions (user_id, token, expires_at, created_at) VALUES (?, ?, ?, ?)",
        (user_id, token, expires_at, now),
    )
    return user_id, token


def _create_dummy_png() -> bytes:
    img = Image.new("RGB", (224, 224), color=(128, 128, 128))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


# ---------------------------------------------------------------------------
# 1. Exact Probability Space Contract Tests
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "ml_raw, dl_raw, expected_combined",
    [
        (0.20, 0.80, 0.56),
        (0.90, 0.10, 0.42),
        (0.00, 1.00, 0.60),
        (1.00, 0.00, 0.40),
        (0.36, 0.515, round(0.4 * 0.36 + 0.6 * 0.515, 6)),
        (0.50, 0.50, 0.50),
        (0.62, 0.71, round(0.4 * 0.62 + 0.6 * 0.71, 6)),
        (0.123456, 0.654321, round(0.4 * 0.123456 + 0.6 * 0.654321, 6)),
    ],
)
def test_fusion_formula_uses_raw_probabilities_and_correct_weights(client, ml_raw, dl_raw, expected_combined):
    """Test that combined score is strictly 0.4 * ML_RAW + 0.6 * DL_RAW."""
    mock_ml_res = {
        "model_name": "Logistic Regression",
        "prediction": int(ml_raw >= 0.36),
        "diagnosis": "Malignant" if ml_raw >= 0.36 else "Benign",
        "probability": ml_raw,  # ML probability is raw
        "raw_probability": ml_raw,
        "decision_threshold": 0.36,
        "risk_band": "High" if ml_raw >= 0.65 else "Medium" if ml_raw >= 0.35 else "Low",
        "top_features": [],
    }

    mock_dl_res = {
        "model_name": "EfficientNet-B0",
        "prediction": int(dl_raw >= 0.515),
        "diagnosis": "Malignant" if dl_raw >= 0.515 else "Benign",
        "probability": 0.999999,  # Intentionally misleading calibrated display probability
        "raw_probability": dl_raw,
        "calibrated_probability": 0.999999,  # Intentionally different from raw
        "decision_threshold": 0.515,
        "risk_band": "High",
    }

    with patch("app.api.endpoints.final_ml_runtime_service.predict", return_value=mock_ml_res), \
         patch("app.api.endpoints.final_dl_runtime_service.predict", return_value=mock_dl_res):
        
        image_bytes = _create_dummy_png()
        response = client.post(
            "/api/v1/predict/multimodal/",
            data={"clinical_data": json.dumps(valid_prediction_payload())},
            files={"image_file": ("test.png", image_bytes, "image/png")},
        )

        assert response.status_code == 200, response.text
        data = response.json()

        # Assert combined score strictly matches formula using raw probabilities
        assert abs(data["combined_malignant_score"] - expected_combined) < 1e-5
        # Assert canonical fields exist
        assert data["combined_threshold"] == 0.5
        assert data["fusion_formula"] == "0.4 * ml_raw_probability + 0.6 * dl_raw_probability"
        assert data["fusion_probability_space"] == "raw_branch_outputs"
        assert data["branches_unpaired"] is True


def test_dl_calibrated_probability_does_not_affect_combined_score(client):
    """Assert changing DL calibrated probability alone must NOT alter combined score."""
    ml_raw = 0.40
    dl_raw = 0.70
    expected_score = round(0.4 * 0.40 + 0.6 * 0.70, 6)  # 0.58

    mock_ml_res = {
        "model_name": "Logistic Regression",
        "prediction": 1,
        "diagnosis": "Malignant",
        "probability": ml_raw,
        "raw_probability": ml_raw,
        "decision_threshold": 0.36,
        "risk_band": "Medium",
    }

    # Run 1: Calibrated = 0.15
    mock_dl_res_1 = {
        "model_name": "EfficientNet-B0",
        "prediction": 1,
        "diagnosis": "Malignant",
        "probability": 0.15,
        "calibrated_probability": 0.15,
        "raw_probability": dl_raw,
        "decision_threshold": 0.515,
        "risk_band": "Low",
    }

    # Run 2: Calibrated = 0.95
    mock_dl_res_2 = {
        "model_name": "EfficientNet-B0",
        "prediction": 1,
        "diagnosis": "Malignant",
        "probability": 0.95,
        "calibrated_probability": 0.95,
        "raw_probability": dl_raw,
        "decision_threshold": 0.515,
        "risk_band": "High",
    }

    image_bytes = _create_dummy_png()

    with patch("app.api.endpoints.final_ml_runtime_service.predict", return_value=mock_ml_res):
        with patch("app.api.endpoints.final_dl_runtime_service.predict", return_value=mock_dl_res_1):
            res1 = client.post(
                "/api/v1/predict/multimodal/",
                data={"clinical_data": json.dumps(valid_prediction_payload())},
                files={"image_file": ("test.png", image_bytes, "image/png")},
            ).json()

        with patch("app.api.endpoints.final_dl_runtime_service.predict", return_value=mock_dl_res_2):
            res2 = client.post(
                "/api/v1/predict/multimodal/",
                data={"clinical_data": json.dumps(valid_prediction_payload())},
                files={"image_file": ("test.png", image_bytes, "image/png")},
            ).json()

    assert res1["combined_malignant_score"] == expected_score
    assert res2["combined_malignant_score"] == expected_score
    assert res1["combined_malignant_score"] == res2["combined_malignant_score"]


# ---------------------------------------------------------------------------
# 2. Branch Agreement & Disagreement State Tests
# ---------------------------------------------------------------------------

def test_branch_agreement_and_disagreement_detection(client):
    """Test agreement flag when branches agree vs disagree."""
    image_bytes = _create_dummy_png()

    # Case A: Agreement (Both Malignant)
    ml_mal = {"model_name": "LR", "prediction": 1, "diagnosis": "Malignant", "probability": 0.8, "raw_probability": 0.8, "decision_threshold": 0.36}
    dl_mal = {"model_name": "EffNet", "prediction": 1, "diagnosis": "Malignant", "probability": 0.85, "raw_probability": 0.85, "decision_threshold": 0.515}
    with patch("app.api.endpoints.final_ml_runtime_service.predict", return_value=ml_mal), \
         patch("app.api.endpoints.final_dl_runtime_service.predict", return_value=dl_mal):
        res_agree = client.post(
            "/api/v1/predict/multimodal/",
            data={"clinical_data": json.dumps(valid_prediction_payload())},
            files={"image_file": ("test.png", image_bytes, "image/png")},
        ).json()
        assert res_agree["branch_agreement"] is True
        assert res_agree["combined_diagnosis"] == "Malignant"

    # Case B: Disagreement (ML Malignant, DL Benign)
    dl_ben = {"model_name": "EffNet", "prediction": 0, "diagnosis": "Benign", "probability": 0.2, "raw_probability": 0.2, "decision_threshold": 0.515}
    with patch("app.api.endpoints.final_ml_runtime_service.predict", return_value=ml_mal), \
         patch("app.api.endpoints.final_dl_runtime_service.predict", return_value=dl_ben):
        res_disagree = client.post(
            "/api/v1/predict/multimodal/",
            data={"clinical_data": json.dumps(valid_prediction_payload())},
            files={"image_file": ("test.png", image_bytes, "image/png")},
        ).json()
        assert res_disagree["branch_agreement"] is False
        assert any("khác nhau" in str(r) for r in res_disagree.get("uncertainty_reasons", []))

    # Case C: Disagreement (ML Benign, DL Malignant)
    ml_ben = {"model_name": "LR", "prediction": 0, "diagnosis": "Benign", "probability": 0.1, "raw_probability": 0.1, "decision_threshold": 0.36}
    with patch("app.api.endpoints.final_ml_runtime_service.predict", return_value=ml_ben), \
         patch("app.api.endpoints.final_dl_runtime_service.predict", return_value=dl_mal):
        res_disagree2 = client.post(
            "/api/v1/predict/multimodal/",
            data={"clinical_data": json.dumps(valid_prediction_payload())},
            files={"image_file": ("test.png", image_bytes, "image/png")},
        ).json()
        assert res_disagree2["branch_agreement"] is False


# ---------------------------------------------------------------------------
# 3. Database Persistence Hygiene: No Base64 Bloat
# ---------------------------------------------------------------------------

def test_database_persistence_strips_base64_explanation_image(client):
    """Assert response returns base64 image, but SQLite persisted payload does NOT contain it."""
    user_id, token = _create_user_and_token("fusion_hygiene_test@test.local", "user")

    dummy_b64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="

    mock_ml_res = {
        "model_name": "Logistic Regression",
        "prediction": 1,
        "diagnosis": "Malignant",
        "probability": 0.75,
        "raw_probability": 0.75,
        "decision_threshold": 0.36,
    }

    mock_dl_res = {
        "model_name": "EfficientNet-B0",
        "prediction": 1,
        "diagnosis": "Malignant",
        "probability": 0.85,
        "raw_probability": 0.80,
        "calibrated_probability": 0.85,
        "decision_threshold": 0.515,
        "explanation_image": dummy_b64,
        "explanation_status": "available",
        "explanation_method": "Grad-CAM",
        "explanation_layer": "top_conv",
        "explanation_disclaimer": "Research only.",
    }

    with patch("app.api.endpoints.final_ml_runtime_service.predict", return_value=mock_ml_res), \
         patch("app.api.endpoints.final_dl_runtime_service.predict", return_value=mock_dl_res):
        
        image_bytes = _create_dummy_png()
        response = client.post(
            "/api/v1/predict/multimodal/",
            data={"clinical_data": json.dumps(valid_prediction_payload()), "include_explanation": "true"},
            files={"image_file": ("test.png", image_bytes, "image/png")},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        live_res = response.json()
        # The live HTTP response MUST contain the explanation image for browser inspection
        assert live_res["dl_result"]["explanation_image"] == dummy_b64

        # Now inspect SQLite directly
        saved_row = db.fetch_one(
            "SELECT * FROM predictions WHERE user_id = ? ORDER BY id DESC LIMIT 1",
            (user_id,),
        )
        assert saved_row is not None
        saved_payload = json.loads(saved_row["response_payload"])

        # Base64 MUST be stripped from persisted payload
        assert "explanation_image" not in saved_payload["dl_result"] or saved_payload["dl_result"]["explanation_image"] is None
        # Metadata must be preserved
        assert saved_payload["dl_result"]["explanation_status"] == "available"
        assert saved_payload["dl_result"]["explanation_method"] == "Grad-CAM"
        assert saved_payload["dl_result"]["explanation_layer"] == "top_conv"
        assert saved_payload["combined_malignant_score"] == round(0.4 * 0.75 + 0.6 * 0.80, 6)


# ---------------------------------------------------------------------------
# 4. Patient Context Authorization
# ---------------------------------------------------------------------------

def test_patient_context_authorization_in_fusion(client):
    """Test normal user cannot bind patient, doctor cannot bind unowned patient."""
    normal_id, normal_token = _create_user_and_token("fusion_normal@test.local", "user")
    doc1_id, doc1_token = _create_user_and_token("fusion_doc1@test.local", "doctor")
    doc2_id, doc2_token = _create_user_and_token("fusion_doc2@test.local", "doctor")

    now = datetime.now(UTC).isoformat()
    # Patient belongs to doc2
    p_id = db.execute(
        "INSERT INTO patients (user_id, full_name, date_of_birth, gender, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
        (doc2_id, "Patient Under Doc2", "1980-05-15", "female", now, now),
    )

    image_bytes = _create_dummy_png()
    mock_ml = {"model_name": "LR", "prediction": 0, "diagnosis": "Benign", "probability": 0.1, "raw_probability": 0.1, "decision_threshold": 0.36}
    mock_dl = {"model_name": "EffNet", "prediction": 0, "diagnosis": "Benign", "probability": 0.1, "raw_probability": 0.1, "decision_threshold": 0.515}

    with patch("app.api.endpoints.final_ml_runtime_service.predict", return_value=mock_ml), \
         patch("app.api.endpoints.final_dl_runtime_service.predict", return_value=mock_dl):
        
        # 1) Normal user cannot pass patient_id
        res1 = client.post(
            "/api/v1/predict/multimodal/",
            data={"clinical_data": json.dumps(valid_prediction_payload()), "patient_id": str(p_id)},
            files={"image_file": ("test.png", image_bytes, "image/png")},
            headers={"Authorization": f"Bearer {normal_token}"},
        )
        assert res1.status_code == 403

        # 2) Doc1 cannot access Doc2's patient
        res2 = client.post(
            "/api/v1/predict/multimodal/",
            data={"clinical_data": json.dumps(valid_prediction_payload()), "patient_id": str(p_id)},
            files={"image_file": ("test.png", image_bytes, "image/png")},
            headers={"Authorization": f"Bearer {doc1_token}"},
        )
        assert res2.status_code in {403, 404}

        # 3) Doc2 (owner) succeeds
        res3 = client.post(
            "/api/v1/predict/multimodal/",
            data={"clinical_data": json.dumps(valid_prediction_payload()), "patient_id": str(p_id)},
            files={"image_file": ("test.png", image_bytes, "image/png")},
            headers={"Authorization": f"Bearer {doc2_token}"},
        )
        assert res3.status_code == 200
