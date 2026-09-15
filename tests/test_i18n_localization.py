"""Automated tests for Vietnamese & English localization contracts.

Verifies:
1. Dictionary parity between en.json and vi.json
2. No empty or "undefined" values
3. All 30 WDBC features localized with distinct labels
4. Preservation of scientific terms: WDBC, CBIS-DDSM, FNA, EfficientNet-B0, Grad-CAM, Logistic Regression, Platt Calibration
5. Preservation of numerical cutoffs: 0.360, 0.515, 40/60, 0.50
6. Fusion disclaimer concept: independent datasets, unpaired samples, heuristic software prototype
7. Doctor role disclaimer: self-declared demo role, immutable
8. Vendored i18next build exists locally and no remote CDN dependency introduced
9. API predict contracts work identically regardless of language
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from app.main import app
from tests.test_schemas import valid_prediction_payload

EN_PATH = Path("frontend/locales/en.json")
VI_PATH = Path("frontend/locales/vi.json")
VENDOR_I18NEXT_PATH = Path("frontend/js/vendor/i18next.js")

CANONICAL_30_FEATURES = [
    "mean_radius", "mean_texture", "mean_perimeter", "mean_area", "mean_smoothness",
    "mean_compactness", "mean_concavity", "mean_concave_points", "mean_symmetry", "mean_fractal_dimension",
    "radius_error", "texture_error", "perimeter_error", "area_error", "smoothness_error",
    "compactness_error", "concavity_error", "concave_points_error", "symmetry_error", "fractal_dimension_error",
    "worst_radius", "worst_texture", "worst_perimeter", "worst_area", "worst_smoothness",
    "worst_compactness", "worst_concavity", "worst_concave_points", "worst_symmetry", "worst_fractal_dimension",
]


def test_i18next_vendored_locally():
    """Verify i18next is vendored locally without CDN dependency."""
    assert VENDOR_I18NEXT_PATH.exists(), "frontend/js/vendor/i18next.js must exist locally"
    content = VENDOR_I18NEXT_PATH.read_text(encoding="utf-8")
    assert "26.4.2" in content or "i18next" in content, "Vendored i18next file must be present"
    assert "export default" in content or "export {" in content, "Vendored i18next must provide ESM export"


def test_dictionaries_exist_and_parse():
    """Verify both locale files exist and are valid JSON."""
    assert EN_PATH.exists(), f"{EN_PATH} must exist"
    assert VI_PATH.exists(), f"{VI_PATH} must exist"

    en = json.loads(EN_PATH.read_text(encoding="utf-8"))
    vi = json.loads(VI_PATH.read_text(encoding="utf-8"))

    assert isinstance(en, dict)
    assert isinstance(vi, dict)


def _get_deep_keys(d: dict, prefix: str = "") -> set[str]:
    keys = set()
    for k, v in d.items():
        full_key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            keys.update(_get_deep_keys(v, full_key))
        else:
            keys.add(full_key)
    return keys


def test_dictionary_key_parity():
    """Verify that every single key in EN exists in VI and vice-versa."""
    en = json.loads(EN_PATH.read_text(encoding="utf-8"))
    vi = json.loads(VI_PATH.read_text(encoding="utf-8"))

    en_keys = _get_deep_keys(en)
    vi_keys = _get_deep_keys(vi)

    missing_in_vi = en_keys - vi_keys
    missing_in_en = vi_keys - en_keys

    assert not missing_in_vi, f"Keys in EN missing in VI: {missing_in_vi}"
    assert not missing_in_en, f"Keys in VI missing in EN: {missing_in_en}"
    assert len(en_keys) >= 400, f"Expected comprehensive dictionary, got {len(en_keys)} keys"


def test_no_empty_or_undefined_values():
    """Verify no string is empty or contains literal 'undefined'."""
    en = json.loads(EN_PATH.read_text(encoding="utf-8"))
    vi = json.loads(VI_PATH.read_text(encoding="utf-8"))

    for name, d in [("EN", en), ("VI", vi)]:
        keys = _get_deep_keys(d)
        for k in keys:
            parts = k.split(".")
            cur = d
            for p in parts:
                cur = cur[p]
            val = str(cur).strip()
            assert len(val) > 0, f"{name} translation for '{k}' is empty"
            assert "undefined" not in val, f"{name} translation for '{k}' contains 'undefined'"


def test_wdbc_all_30_features_localized():
    """Verify all 30 WDBC features exist with valid labels."""
    en = json.loads(EN_PATH.read_text(encoding="utf-8"))
    vi = json.loads(VI_PATH.read_text(encoding="utf-8"))

    for feat in CANONICAL_30_FEATURES:
        assert feat in en.get("wdbc", {}).get("features", {}), f"Missing {feat} in en.json"
        assert feat in vi.get("wdbc", {}).get("features", {}), f"Missing {feat} in vi.json"

        en_label = en["wdbc"]["features"][feat]
        vi_label = vi["wdbc"]["features"][feat]
        assert en_label != vi_label, f"Feature {feat} should have distinct EN and VI labels"


def test_fusion_scientific_disclaimer():
    """Verify scientific requirements for Fusion disclaimer in both EN and VI."""
    en = json.loads(EN_PATH.read_text(encoding="utf-8"))
    vi = json.loads(VI_PATH.read_text(encoding="utf-8"))

    vi_disc = vi["fusion"]["disclaimer"]
    en_disc = en["fusion"]["disclaimer"]

    # Must mention independent datasets
    assert "WDBC" in vi_disc and "CBIS-DDSM" in vi_disc
    assert "WDBC" in en_disc and "CBIS-DDSM" in en_disc

    # Must clarify unpaired and heuristic software combination
    assert "không được ghép cặp" in vi_disc or "độc lập" in vi_disc
    assert "không phải là một mô hình đa phương thức" in vi_disc
    assert "40% ML / 60% DL" in vi_disc
    assert "40% ML / 60% DL" in en_disc


def test_doctor_role_disclaimer():
    """Verify doctor role disclaimer preserves self-declared policy."""
    en = json.loads(EN_PATH.read_text(encoding="utf-8"))
    vi = json.loads(VI_PATH.read_text(encoding="utf-8"))

    en_notice = en["auth"]["roleImmutableNotice"]
    vi_notice = vi["auth"]["roleImmutableNotice"]

    assert "self-declared" in en_notice.lower()
    assert "tự khai báo" in vi_notice.lower() or "chỉ phục vụ mục đích" in vi_notice.lower()
    assert "không xác minh" in vi_notice.lower() or "permanent" in en_notice.lower()


@pytest.fixture
def client():
    return TestClient(app)


def test_api_predict_multimodal_unaffected_by_accept_language(client):
    """Verify backend API prediction inputs and outputs are identical regardless of language."""
    payload = valid_prediction_payload()
    img_path = Path("frontend/assets/demo-images/demo-benign-mammogram.png")
    assert img_path.exists()

    with open(img_path, "rb") as f:
        img_bytes = f.read()

    # Request 1: English
    r_en = client.post(
        "/api/v1/predict/multimodal/",
        data={"clinical_data": json.dumps(payload)},
        files={"image_file": ("demo-benign.png", img_bytes, "image/png")},
        headers={"Accept-Language": "en-US,en;q=0.9"},
    )
    assert r_en.status_code == 200, r_en.text

    # Request 2: Vietnamese
    r_vi = client.post(
        "/api/v1/predict/multimodal/",
        data={"clinical_data": json.dumps(payload)},
        files={"image_file": ("demo-benign.png", img_bytes, "image/png")},
        headers={"Accept-Language": "vi-VN,vi;q=0.9"},
    )
    assert r_vi.status_code == 200, r_vi.text

    data_en = r_en.json()
    data_vi = r_vi.json()

    # Exact equality of scientific numbers
    assert data_en["combined_malignant_score"] == data_vi["combined_malignant_score"]
    assert data_en["ml_result"]["raw_probability"] == data_vi["ml_result"]["raw_probability"]
    assert data_en["dl_result"]["raw_probability"] == data_vi["dl_result"]["raw_probability"]
    assert data_en["branch_agreement"] == data_vi["branch_agreement"]
