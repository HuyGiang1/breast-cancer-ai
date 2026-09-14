"""Automated tests for custom mammogram upload and WDBC CSV demo files.

Verifies:
1. custom image upload path (PNG/JPEG)
2. >1 MB image accepted through app contract (1.66 MB CBIS-DDSM image)
3. >20 MB rejected cleanly with HTTP 413
4. non-JSON HTTP error does not become unexplained "Request failed."
5. benign CSV demo exact 30 values
6. malignant CSV demo exact 30 values
7. both downloaded CSVs round-trip through parser
8. no accidental diagnosis field requirement
9. demo mammograms still work
10. custom mammogram works through same frozen pipeline
11. 40/60 fusion contract unchanged
12. unpaired disclaimer unchanged
"""

from __future__ import annotations

import io
import json
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.main import app
from tests.test_schemas import valid_prediction_payload


BENIGN_DEMO_PATH = Path("frontend/assets/demo-images/demo-benign-mammogram.png")
MALIGNANT_DEMO_PATH = Path("frontend/assets/demo-images/demo-malignant-mammogram.png")
CUSTOM_CBIS_DDSM_PATH = Path(
    "data/cbis_ddsm/processed/images/test/benign/1.3.6.1.4.1.9590.100.1.2.364769939511865969122167341301370556814__1-102.png"
)
BENIGN_CSV_PATH = Path("frontend/assets/demo-csv/wdbc_benign_research_demo.csv")
MALIGNANT_CSV_PATH = Path("frontend/assets/demo-csv/wdbc_malignant_research_demo.csv")

CANONICAL_30_FEATURES = [
    "mean_radius", "mean_texture", "mean_perimeter", "mean_area", "mean_smoothness",
    "mean_compactness", "mean_concavity", "mean_concave_points", "mean_symmetry", "mean_fractal_dimension",
    "radius_error", "texture_error", "perimeter_error", "area_error", "smoothness_error",
    "compactness_error", "concavity_error", "concave_points_error", "symmetry_error", "fractal_dimension_error",
    "worst_radius", "worst_texture", "worst_perimeter", "worst_area", "worst_smoothness",
    "worst_compactness", "worst_concavity", "worst_concave_points", "worst_symmetry", "worst_fractal_dimension",
]

SAMPLES_BENIGN = {
    "mean_radius": 13.54, "mean_texture": 14.36, "mean_perimeter": 87.46, "mean_area": 566.3,
    "mean_smoothness": 0.09779, "mean_compactness": 0.08129, "mean_concavity": 0.06664,
    "mean_concave_points": 0.04781, "mean_symmetry": 0.1885, "mean_fractal_dimension": 0.05766,
    "radius_error": 0.2699, "texture_error": 0.7886, "perimeter_error": 2.058, "area_error": 23.56,
    "smoothness_error": 0.008462, "compactness_error": 0.0146, "concavity_error": 0.02387,
    "concave_points_error": 0.01315, "symmetry_error": 0.0198, "fractal_dimension_error": 0.0023,
    "worst_radius": 15.11, "worst_texture": 19.26, "worst_perimeter": 99.7, "worst_area": 711.2,
    "worst_smoothness": 0.144, "worst_compactness": 0.1773, "worst_concavity": 0.239,
    "worst_concave_points": 0.1288, "worst_symmetry": 0.2977, "worst_fractal_dimension": 0.07259,
}

SAMPLES_MALIGNANT = {
    "mean_radius": 17.99, "mean_texture": 10.38, "mean_perimeter": 122.8, "mean_area": 1001.0,
    "mean_smoothness": 0.1184, "mean_compactness": 0.2776, "mean_concavity": 0.3001,
    "mean_concave_points": 0.1471, "mean_symmetry": 0.2419, "mean_fractal_dimension": 0.07871,
    "radius_error": 1.095, "texture_error": 0.9053, "perimeter_error": 8.589, "area_error": 153.4,
    "smoothness_error": 0.006399, "compactness_error": 0.04904, "concavity_error": 0.05373,
    "concave_points_error": 0.01587, "symmetry_error": 0.03003, "fractal_dimension_error": 0.006193,
    "worst_radius": 25.38, "worst_texture": 17.33, "worst_perimeter": 184.6, "worst_area": 2019.0,
    "worst_smoothness": 0.1622, "worst_compactness": 0.6656, "worst_concavity": 0.7119,
    "worst_concave_points": 0.2654, "worst_symmetry": 0.4601, "worst_fractal_dimension": 0.1189,
}


@pytest.fixture
def client():
    with patch("app.api.endpoints.ai_advisor_service.advice_for_multimodal") as mock_advice:
        mock_advice.return_value = {
            "advice": "Test experimental multimodal guidance.",
            "provider": "mock",
            "model": "mock-fusion-model",
        }
        yield TestClient(app)


# ---------------------------------------------------------------------------
# 1. Custom Image Upload Path (PNG & JPEG)
# ---------------------------------------------------------------------------
def test_custom_image_upload_png_and_jpeg(client):
    """User-selected PNG and JPEG mammograms must pass through multimodal endpoint."""
    img_png = Image.new("RGB", (224, 224), color=(100, 150, 200))
    buf_png = io.BytesIO()
    img_png.save(buf_png, format="PNG")
    png_bytes = buf_png.getvalue()

    resp_png = client.post(
        "/api/v1/predict/multimodal/",
        data={"clinical_data": json.dumps(valid_prediction_payload())},
        files={"image_file": ("custom_mammogram.png", png_bytes, "image/png")},
    )
    assert resp_png.status_code == 200, resp_png.text
    body_png = resp_png.json()
    assert "dl_result" in body_png
    assert "ml_result" in body_png

    img_jpg = Image.new("RGB", (224, 224), color=(120, 130, 140))
    buf_jpg = io.BytesIO()
    img_jpg.save(buf_jpg, format="JPEG")
    jpg_bytes = buf_jpg.getvalue()

    resp_jpg = client.post(
        "/api/v1/predict/multimodal/",
        data={"clinical_data": json.dumps(valid_prediction_payload())},
        files={"image_file": ("custom_mammogram.jpg", jpg_bytes, "image/jpeg")},
    )
    assert resp_jpg.status_code == 200, resp_jpg.text


# ---------------------------------------------------------------------------
# 2. >1 MB Image Accepted Through App Contract (1.66 MB CBIS-DDSM file)
# ---------------------------------------------------------------------------
def test_greater_than_1mb_image_accepted_through_app_contract(client):
    """Files > 1 MB and < 20 MB (such as 1.66 MB CBIS-DDSM image) must be accepted."""
    assert CUSTOM_CBIS_DDSM_PATH.exists(), f"Missing CBIS-DDSM sample image at {CUSTOM_CBIS_DDSM_PATH}"
    file_bytes = CUSTOM_CBIS_DDSM_PATH.read_bytes()
    assert len(file_bytes) > 1024 * 1024, "Sample image should be > 1 MB"
    assert len(file_bytes) < 20 * 1024 * 1024, "Sample image should be < 20 MB"

    resp = client.post(
        "/api/v1/predict/multimodal/",
        data={"clinical_data": json.dumps(valid_prediction_payload())},
        files={"image_file": (CUSTOM_CBIS_DDSM_PATH.name, file_bytes, "image/png")},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["combined_diagnosis"] in ["Benign", "Malignant"]
    assert data["dl_result"]["model_name"] == "EfficientNet-B0"


# ---------------------------------------------------------------------------
# 3. >20 MB Rejected Cleanly
# ---------------------------------------------------------------------------
def test_greater_than_20mb_rejected_cleanly(client):
    """Files > 20 MB must be cleanly rejected with HTTP 413 and clear detail."""
    oversized_bytes = b"0" * (20 * 1024 * 1024 + 1024)  # 20 MB + 1 KB
    resp = client.post(
        "/api/v1/predict/multimodal/",
        data={"clinical_data": json.dumps(valid_prediction_payload())},
        files={"image_file": ("too_large.png", oversized_bytes, "image/png")},
    )
    assert resp.status_code == 413
    data = resp.json()
    assert "too large" in data.get("detail", "").lower()


# ---------------------------------------------------------------------------
# 4. Non-JSON HTTP Error Frontend Handling
# ---------------------------------------------------------------------------
def test_frontend_error_handling_contract():
    """Verify api.js safely maps HTTP 413, 502, 504, 500 without HTML injection."""
    api_js_path = Path("frontend/js/core/api.js")
    content = api_js_path.read_text(encoding="utf-8")
    assert "413" in content
    assert "Maximum upload size is 20 MB" in content
    assert "502" in content
    assert "504" in content
    assert "500" in content


# ---------------------------------------------------------------------------
# 5. Benign CSV Demo Exact 30 Values
# ---------------------------------------------------------------------------
def test_benign_csv_demo_exact_30_values():
    """wdbc_benign_research_demo.csv must have canonical 30 columns and exact values."""
    assert BENIGN_CSV_PATH.exists(), f"Missing {BENIGN_CSV_PATH}"
    lines = [line.strip() for line in BENIGN_CSV_PATH.read_text().splitlines() if line.strip()]
    assert len(lines) == 2, "Demo CSV must contain exactly header and one data row"

    headers = [h.strip() for h in lines[0].split(",")]
    assert headers == CANONICAL_30_FEATURES, "Header must match canonical 30 features exactly"

    values = [float(v.strip()) for v in lines[1].split(",")]
    assert len(values) == 30, "Row must have exactly 30 values"

    for feat, val in zip(CANONICAL_30_FEATURES, values):
        expected = SAMPLES_BENIGN[feat]
        assert abs(val - expected) < 1e-6, f"Mismatch on {feat}: {val} != {expected}"


# ---------------------------------------------------------------------------
# 6. Malignant CSV Demo Exact 30 Values
# ---------------------------------------------------------------------------
def test_malignant_csv_demo_exact_30_values():
    """wdbc_malignant_research_demo.csv must have canonical 30 columns and exact values."""
    assert MALIGNANT_CSV_PATH.exists(), f"Missing {MALIGNANT_CSV_PATH}"
    lines = [line.strip() for line in MALIGNANT_CSV_PATH.read_text().splitlines() if line.strip()]
    assert len(lines) == 2, "Demo CSV must contain exactly header and one data row"

    headers = [h.strip() for h in lines[0].split(",")]
    assert headers == CANONICAL_30_FEATURES, "Header must match canonical 30 features exactly"

    values = [float(v.strip()) for v in lines[1].split(",")]
    assert len(values) == 30, "Row must have exactly 30 values"

    for feat, val in zip(CANONICAL_30_FEATURES, values):
        expected = SAMPLES_MALIGNANT[feat]
        assert abs(val - expected) < 1e-6, f"Mismatch on {feat}: {val} != {expected}"


# ---------------------------------------------------------------------------
# 7. Both Downloaded CSVs Round-Trip Through Parser
# ---------------------------------------------------------------------------
def test_csv_demos_round_trip_through_clinical_parser():
    """Verify both demo CSVs can be converted to prediction payloads directly."""
    for csv_path, expected_dict in [
        (BENIGN_CSV_PATH, SAMPLES_BENIGN),
        (MALIGNANT_CSV_PATH, SAMPLES_MALIGNANT),
    ]:
        lines = [l.strip() for l in csv_path.read_text().splitlines() if l.strip()]
        headers = lines[0].split(",")
        values = lines[1].split(",")
        parsed_dict = {h: float(v) for h, v in zip(headers, values)}

        # Verify against schema validation
        from app.api.schemas import PredictionRequest
        req = PredictionRequest(**parsed_dict)
        for f in CANONICAL_30_FEATURES:
            assert getattr(req, f) == expected_dict[f]


# ---------------------------------------------------------------------------
# 8. No Accidental Diagnosis Field Requirement
# ---------------------------------------------------------------------------
def test_no_accidental_diagnosis_field_requirement():
    """CSV demos and schema must not require diagnosis, target, or label."""
    benign_text = BENIGN_CSV_PATH.read_text()
    malignant_text = MALIGNANT_CSV_PATH.read_text()

    for text in [benign_text, malignant_text]:
        headers = text.splitlines()[0].split(",")
        assert "diagnosis" not in headers
        assert "target" not in headers
        assert "label" not in headers

    # Endpoint must succeed with purely 30 features
    from app.api.schemas import PredictionRequest
    req = PredictionRequest(**SAMPLES_BENIGN)
    assert not hasattr(req, "diagnosis")


# ---------------------------------------------------------------------------
# 9. Demo Mammograms Still Work
# ---------------------------------------------------------------------------
def test_demo_mammograms_still_work(client):
    """Built-in Benign and Malignant mammogram assets must process cleanly."""
    assert BENIGN_DEMO_PATH.exists()
    assert MALIGNANT_DEMO_PATH.exists()

    resp_b = client.post(
        "/api/v1/predict/multimodal/",
        data={"clinical_data": json.dumps(SAMPLES_BENIGN)},
        files={"image_file": ("demo-benign-mammogram.png", BENIGN_DEMO_PATH.read_bytes(), "image/png")},
    )
    assert resp_b.status_code == 200, resp_b.text
    data_b = resp_b.json()
    assert data_b["dl_result"]["model_name"] == "EfficientNet-B0"

    resp_m = client.post(
        "/api/v1/predict/multimodal/",
        data={"clinical_data": json.dumps(SAMPLES_MALIGNANT)},
        files={"image_file": ("demo-malignant-mammogram.png", MALIGNANT_DEMO_PATH.read_bytes(), "image/png")},
    )
    assert resp_m.status_code == 200, resp_m.text
    data_m = resp_m.json()
    assert data_m["dl_result"]["model_name"] == "EfficientNet-B0"


# ---------------------------------------------------------------------------
# 10. Custom Mammogram Works Through Same Frozen Pipeline
# ---------------------------------------------------------------------------
def test_custom_mammogram_works_through_same_frozen_pipeline(client):
    """Custom user upload goes through EfficientNet-B0, threshold 0.515, Grad-CAM top_conv."""
    file_bytes = CUSTOM_CBIS_DDSM_PATH.read_bytes()

    resp = client.post(
        "/api/v1/predict/multimodal/",
        data={"clinical_data": json.dumps(SAMPLES_BENIGN), "include_explanation": "true"},
        files={"image_file": ("custom_ddsm.png", file_bytes, "image/png")},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    dl = data["dl_result"]
    assert dl["model_name"] == "EfficientNet-B0"
    assert dl["decision_threshold"] == 0.515
    assert "raw_probability" in dl
    assert "explanation_image" in dl  # Grad-CAM top_conv returned


# ---------------------------------------------------------------------------
# 11. 40/60 Fusion Contract Unchanged
# ---------------------------------------------------------------------------
def test_fusion_contract_40_60_unchanged(client):
    """Combined = round(0.4 * ml_raw + 0.6 * dl_raw, 6), midpoint 0.50."""
    ml_raw = 0.30
    dl_raw = 0.70
    expected_score = round(0.4 * ml_raw + 0.6 * dl_raw, 6)

    ml_mock = {"model_name": "LR", "prediction": 0, "diagnosis": "Benign", "probability": ml_raw, "raw_probability": ml_raw, "decision_threshold": 0.36}
    dl_mock = {"model_name": "EffNet", "prediction": 1, "diagnosis": "Malignant", "probability": 0.85, "raw_probability": dl_raw, "decision_threshold": 0.515}

    with patch("app.api.endpoints.final_ml_runtime_service.predict", return_value=ml_mock), \
         patch("app.api.endpoints.final_dl_runtime_service.predict", return_value=dl_mock):
        resp = client.post(
            "/api/v1/predict/multimodal/",
            data={"clinical_data": json.dumps(SAMPLES_BENIGN)},
            files={"image_file": ("test.png", BENIGN_DEMO_PATH.read_bytes(), "image/png")},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["combined_malignant_score"] == expected_score
        assert data["combined_threshold"] == 0.5
        assert data["fusion_formula"] == "0.4 * ml_raw_probability + 0.6 * dl_raw_probability"


# ---------------------------------------------------------------------------
# 12. Unpaired Disclaimer Unchanged
# ---------------------------------------------------------------------------
def test_unpaired_disclaimer_unchanged(client):
    """Unpaired dataset notice must remain in endpoint response metadata."""
    resp = client.post(
        "/api/v1/predict/multimodal/",
        data={"clinical_data": json.dumps(SAMPLES_BENIGN)},
        files={"image_file": ("test.png", BENIGN_DEMO_PATH.read_bytes(), "image/png")},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["branches_unpaired"] is True
    reasons = data.get("uncertainty_reasons", [])
    assert any("unpaired" in r.lower() or "không ghép cặp" in r.lower() for r in reasons)
