import io
import re
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_multimodal_js_consumes_active_parser_contract():
    """multimodal.js must consume parseClinicalCsv { isMultiRow, rowCount, rows } and not obsolete parsed.success / parsed.data."""
    js_path = REPO_ROOT / "frontend" / "js" / "pages" / "multimodal.js"
    assert js_path.exists(), "multimodal.js must exist"
    content = js_path.read_text(encoding="utf-8")

    # Obsolete contract check
    assert "parsed.success" not in content, "multimodal.js must not check obsolete parsed.success"
    assert "parsed.data[" not in content, "multimodal.js must not access obsolete parsed.data"

    # Current contract check
    assert "parsed.isMultiRow" in content, "multimodal.js must check parsed.isMultiRow"
    assert "parsed.rows[0]" in content, "multimodal.js must access parsed.rows"
    assert "selectedCsvRowIndex" in content, "multimodal.js must manage selectedCsvRowIndex for explicit selection"


def test_scientific_terminology_and_ux_in_multimodal():
    """Check required WDBC FNA terminology, modal title, description, and input methods in Branch 1."""
    js_path = REPO_ROOT / "frontend" / "js" / "pages" / "multimodal.js"
    content = js_path.read_text(encoding="utf-8")

    # Terminology checks
    assert "Import WDBC FNA Features CSV" in content, "Modal title must be 'Import WDBC FNA Features CSV'"
    assert "Upload a CSV containing the 30 WDBC nuclear morphology features" in content, (
        "Modal description must describe 30 WDBC nuclear morphology features"
    )
    assert "Import Clinical Features CSV" not in content, (
        "Obsolete 'Import Clinical Features CSV' must be replaced"
    )

    # Branch 1 Input Methods
    assert "Import WDBC CSV" in content, "Branch 1 must offer 'Import WDBC CSV' button"
    assert "Manual Entry" in content, "Branch 1 must offer 'Manual Entry' input method button"
    assert "1 valid WDBC observation loaded." in content, (
        "Must display '1 valid WDBC observation loaded.' upon successful import"
    )


def test_unpaired_dataset_disclaimer_preserved():
    """Ensure the scientific unpaired dataset contract disclaimer is preserved in hero and modal."""
    js_path = REPO_ROOT / "frontend" / "js" / "pages" / "multimodal.js"
    content = js_path.read_text(encoding="utf-8")

    assert "fusion-unpaired-banner" in content, "Hero must render unpaired banner"
    assert "Unpaired Dataset Scientific Contract" in content, (
        "Hero banner must state 'Unpaired Dataset Scientific Contract'"
    )
    assert "Unpaired Dataset Notice" in content, "Modal must include 'Unpaired Dataset Notice'"


def test_fusion_requires_both_modalities_backend():
    """Verify backend fusion endpoint strictly requires both 30 clinical features AND a mammogram image."""
    # 1. Missing image entirely
    response_no_image = client.post(
        "/api/v1/predict/multimodal/",
        data={
            "mean_radius": 13.54,
            "mean_texture": 14.36,
            "mean_perimeter": 87.46,
            "mean_area": 566.3,
            "mean_smoothness": 0.09779,
        },
    )
    # FastApi validation returns 422 if required file/fields are missing
    assert response_no_image.status_code in (400, 422), (
        f"Fusion endpoint must reject execution when mammography image is missing (got {response_no_image.status_code})"
    )
