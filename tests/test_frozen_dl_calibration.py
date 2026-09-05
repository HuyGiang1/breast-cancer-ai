import inspect
import json
import math
from pathlib import Path

import pytest

from app.services.final_dl_calibration import apply_platt_calibration, classify_final_dl_raw_probability
from scripts import freeze_final_dl_calibration


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "models" / "calibration" / "efficientnet_b0_platt_final_seed42.json"


def artifact():
    return json.loads(ARTIFACT.read_text(encoding="utf-8"))


def test_frozen_platt_json_has_finite_parameters():
    payload = artifact()
    assert payload["method"] == "platt_logistic_regression"
    assert all(math.isfinite(float(payload[key])) for key in ("coefficient", "intercept"))


def test_known_raw_probability_reproduces_exported_calibrated_probability():
    with (ROOT / "experiments/final/dl_calibration/efficientnet_b0_test_calibrated_predictions.csv").open() as handle:
        header = next(handle)
        row = next(handle).strip().split(",")
    assert header.startswith("sample_index,true_label,raw_probability,calibrated_probability")
    assert apply_platt_calibration(float(row[2]), artifact()) == pytest.approx(float(row[3]), abs=1e-12)


def test_platt_output_is_bounded_and_raw_decision_is_independent():
    payload = artifact()
    for value in (0.0, 0.48, 0.515, 1.0):
        assert 0.0 <= apply_platt_calibration(value, payload) <= 1.0
    assert classify_final_dl_raw_probability(0.514999999) == 0
    assert classify_final_dl_raw_probability(0.515) == 1
    assert payload["decision_probability_space"] == "raw"


def test_legacy_profile_is_not_a_final_calibration_source():
    assert "calibration_profile.json" not in json.dumps(artifact())


def test_freeze_fit_uses_validation_labels_not_test_labels():
    source = inspect.getsource(freeze_final_dl_calibration.main)
    assert "platt_model(p_val, y_val)" in source
    assert "platt_model(p_test, y_test)" not in source
