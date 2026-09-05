import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from app.api.schemas import PredictionRequest
from app.services.final_ml_runtime import (
    API_TO_WDBC_FEATURE,
    FinalMLRuntimeService,
    build_wdbc_feature_vector,
)
from tests.test_schemas import valid_prediction_payload


def test_feature_vector_uses_exact_frozen_order():
    payload = {name: float(index) for index, name in enumerate(API_TO_WDBC_FEATURE, start=1)}
    vector = build_wdbc_feature_vector(payload)
    assert vector.shape == (1, 30)
    assert vector.tolist()[0] == list(range(1, 31))


def test_feature_vector_rejects_missing_and_non_finite_values():
    payload = valid_prediction_payload()
    payload.pop("smoothness_error")
    with pytest.raises(ValueError, match="missing"):
        build_wdbc_feature_vector(payload)
    payload = valid_prediction_payload()
    payload["smoothness_error"] = float("nan")
    with pytest.raises(ValueError, match="finite"):
        build_wdbc_feature_vector(payload)


class CapturingPipeline:
    classes_ = np.array([0, 1])

    def __init__(self):
        self.received = None

    def predict_proba(self, values):
        self.received = values.copy()
        return np.array([[0.64, 0.36]])


def _ready_service() -> tuple[FinalMLRuntimeService, CapturingPipeline]:
    service = FinalMLRuntimeService(model_path=Path("/does/not/exist"))
    pipeline = CapturingPipeline()
    service.model = pipeline
    service.health_error = None
    return service, pipeline


def test_prediction_uses_raw_pipeline_probability_without_extra_scaling():
    service, pipeline = _ready_service()
    request = PredictionRequest(**valid_prediction_payload())
    result = service.predict(request)
    assert np.isclose(result["raw_probability"], 0.36)
    assert result["prediction"] == 1
    assert result["decision_threshold"] == 0.36
    assert np.isclose(pipeline.received[0, 0], request.mean_radius)


def test_threshold_boundary_is_malignant():
    service, pipeline = _ready_service()
    pipeline.predict_proba = lambda values: np.array([[0.6400001, 0.3599999]])
    assert service.predict(PredictionRequest(**valid_prediction_payload()))["diagnosis"] == "Benign"
    pipeline.predict_proba = lambda values: np.array([[0.64, 0.36]])
    assert service.predict(PredictionRequest(**valid_prediction_payload()))["diagnosis"] == "Malignant"


def test_missing_artifact_never_trains_or_discovers_legacy_models(tmp_path):
    registry = tmp_path / "registry.json"
    registry.write_text(json.dumps({"models": [{"id": "wdbc-logistic-regression-v1", "artifact_filename": "missing.joblib", "sha256": "0", "input": {"feature_count": 30}}]}))
    service = FinalMLRuntimeService(registry_path=registry)
    assert service.model is None
    assert service.get_available_models() == []
    assert service.get_model_status()["status"] == "unavailable"


def test_checksum_mismatch_marks_model_unhealthy(tmp_path):
    artifact = tmp_path / "candidate.joblib"
    artifact.write_bytes(b"not the expected artifact")
    registry = tmp_path / "registry.json"
    registry.write_text(json.dumps({"models": [{"id": "wdbc-logistic-regression-v1", "artifact_filename": str(artifact), "sha256": hashlib.sha256(b"different").hexdigest(), "input": {"feature_count": 30}}]}))
    service = FinalMLRuntimeService(registry_path=registry)
    assert service.model is None
    assert "checksum mismatch" in (service.health_error or "")
