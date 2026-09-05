from pathlib import Path

import pytest

from app.services.final_dl_runtime import FinalDLRuntimeService, InvalidFinalDLImageError, preprocess_final_dl_image


def test_final_dl_status_is_research_demo_when_local_artifacts_exist():
    service = FinalDLRuntimeService()
    configured_path = service._model_path(service._registry_entry())
    if not configured_path.is_file():
        pytest.skip("Final DL model artifact is not available in weight-free CI.")
    status = service.get_model_status()
    assert status["status"] == "research_demo"
    assert status["artifact_verified"] is True
    assert status["decision_threshold"] == 0.515
    assert status["decision_probability_space"] == "raw"


def test_final_dl_missing_artifact_has_no_fallback():
    service = FinalDLRuntimeService(model_path=Path("/does/not/exist.keras"))
    assert service.get_available_models() == []
    assert service.get_model_status()["status"] == "unavailable"


def test_preprocess_rejects_corrupted_input():
    with pytest.raises(InvalidFinalDLImageError):
        preprocess_final_dl_image(b"not-an-image")


def test_final_preprocess_is_deterministic_for_rgb_png():
    pytest.importorskip("tensorflow")
    image_path = Path(__file__).resolve().parents[1] / "data" / "cbis_ddsm" / "processed" / "images" / "test" / "benign"
    sample = next(image_path.glob("*.png"), None)
    if sample is None:
        pytest.skip("Local CBIS test image is unavailable.")
    left = preprocess_final_dl_image(sample.read_bytes()).numpy()
    right = preprocess_final_dl_image(sample.read_bytes()).numpy()
    assert left.shape == (1, 224, 224, 3)
    assert (left == right).all()
