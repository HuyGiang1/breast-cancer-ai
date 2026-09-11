"""Unit and numerical parity tests for frozen EfficientNet-B0 Grad-CAM runtime."""

from __future__ import annotations

import base64
import io
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest
from PIL import Image

from app.services.final_dl_gradcam import (
    GRADCAM_DISCLAIMER,
    GRADCAM_LAYER,
    GRADCAM_METHOD,
    build_gradcam_models,
    generate_gradcam_overlay,
)
from app.services.final_dl_runtime import (
    FinalDLRuntimeService,
    preprocess_final_dl_image,
)

BENIGN_DEMO_PATH = Path("frontend/assets/demo-images/demo-benign-mammogram.png")
MALIGNANT_DEMO_PATH = Path("frontend/assets/demo-images/demo-malignant-mammogram.png")


@pytest.fixture(scope="module")
def runtime_service():
    service = FinalDLRuntimeService()
    assert service.model is not None, f"Model failed to load: {service.error}"
    return service


def test_gradcam_target_layer_resolution(runtime_service):
    """Verify target convolutional layer resolves to top_conv in the backbone."""
    backbone_grad_model, classifier_head, layer_name = build_gradcam_models(runtime_service.model)
    assert layer_name == "top_conv"
    assert backbone_grad_model is not None
    assert classifier_head is not None
    assert runtime_service.backbone_grad_model is not None
    assert runtime_service.classifier_head is not None


def test_positive_class_is_malignant(runtime_service):
    """Verify the scalar output explained by Grad-CAM is the malignant probability."""
    output_layer = runtime_service.model.layers[-1]
    assert output_layer.name == "malignant_probability"
    assert output_layer.units == 1

    # Verify malignant demo returns probability >= threshold 0.515
    malignant_bytes = MALIGNANT_DEMO_PATH.read_bytes()
    res = runtime_service.predict(malignant_bytes, include_explanation=True)
    assert res["raw_probability"] >= 0.515
    assert res["prediction"] == 1
    assert res["diagnosis"] == "Malignant"


def test_gradcam_heatmap_validity_and_bounds(runtime_service):
    """Verify heatmap is finite, normalized in [0, 1], and produces a valid PNG data URL."""
    benign_bytes = BENIGN_DEMO_PATH.read_bytes()
    tensor = preprocess_final_dl_image(benign_bytes)
    raw_prob, data_url = generate_gradcam_overlay(
        runtime_service.backbone_grad_model, runtime_service.classifier_head, tensor
    )

    assert 0.0 <= raw_prob <= 1.0
    assert data_url.startswith("data:image/png;base64,")

    # Decode and verify overlay dimensions
    b64_content = data_url.split(",", 1)[1]
    img_bytes = base64.b64decode(b64_content)
    with Image.open(io.BytesIO(img_bytes)) as img:
        assert img.size == (224, 224)
        assert img.mode == "RGB"


def test_gradcam_numerical_parity_with_and_without_explanation(runtime_service):
    """Hard gate: predictions must be numerically identical with and without explanation."""
    for path in (BENIGN_DEMO_PATH, MALIGNANT_DEMO_PATH):
        image_bytes = path.read_bytes()
        res_no_exp = runtime_service.predict(image_bytes, include_explanation=False)
        res_with_exp = runtime_service.predict(image_bytes, include_explanation=True)

        assert abs(res_no_exp["raw_probability"] - res_with_exp["raw_probability"]) <= 1e-7
        assert abs(res_no_exp["calibrated_probability"] - res_with_exp["calibrated_probability"]) <= 1e-7
        assert res_no_exp["prediction"] == res_with_exp["prediction"]
        assert res_no_exp["diagnosis"] == res_with_exp["diagnosis"]
        assert res_no_exp["decision_threshold"] == res_with_exp["decision_threshold"]
        assert res_no_exp["model_id"] == res_with_exp["model_id"]

        # Verify contract fields
        assert res_with_exp["explanation_status"] == "available"
        assert res_with_exp["explanation_method"] == GRADCAM_METHOD
        assert res_with_exp["explanation_layer"] == GRADCAM_LAYER
        assert res_with_exp["explanation_disclaimer"] == GRADCAM_DISCLAIMER
        assert res_with_exp["explanation_image"] is not None


def test_gradcam_failure_fallback(runtime_service):
    """If Grad-CAM fails, prediction must still return successfully without HTTP error."""
    benign_bytes = BENIGN_DEMO_PATH.read_bytes()

    with patch(
        "app.services.final_dl_runtime.generate_gradcam_overlay",
        side_effect=RuntimeError("Simulated GradientTape breakdown"),
    ):
        res = runtime_service.predict(benign_bytes, include_explanation=True)
        assert res["raw_probability"] is not None
        assert res["prediction"] == 0
        assert res["diagnosis"] == "Benign"
        assert res["explanation_status"] == "unavailable"
        assert res["explanation_image"] is None
        assert "could not be generated" in res["analysis_text"]
