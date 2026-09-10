from __future__ import annotations

import math
import numpy as np
import pytest
from sklearn.datasets import load_breast_cancer

from app.api.schemas import PredictionRequest
from app.services.final_ml_runtime import (
    API_TO_WDBC_FEATURE,
    final_ml_runtime_service,
)


def _sigmoid(logit: float) -> float:
    return 1.0 / (1.0 + math.exp(-logit))


def test_frozen_logistic_regression_contribution_parity():
    """Verify that reconstructed LR probability from contribution equation matches model.predict_proba exactly."""
    dataset = load_breast_cancer()
    feature_names = list(API_TO_WDBC_FEATURE.keys())

    # Test benign preset (row 19), malignant preset (row 0), and diverse index rows
    test_indices = [0, 19, 42, 100, 250, 455, 500]

    for idx in test_indices:
        row = dataset.data[idx]
        payload = {feat: float(row[i]) for i, feat in enumerate(feature_names)}
        req = PredictionRequest(**payload)

        result = final_ml_runtime_service.predict(req)

        raw_prob = result["raw_probability"]
        assert result["decision_threshold"] == 0.36
        expected_class = int(raw_prob >= 0.36)
        assert result["prediction"] == expected_class
        assert result["diagnosis"] == ("Malignant" if expected_class == 1 else "Benign")

        # Top features & contributions
        top_features = result["top_features"]
        all_features = result["all_features"]
        assert len(all_features) == 30
        assert len(top_features) == 30

        intercept = result["intercept"]
        total_logit = result["total_logit"]
        assert intercept is not None
        assert total_logit is not None

        # Sum of contributions
        contrib_sum = sum(f["log_odds_contribution"] for f in all_features)
        # Note: all_features rounded to 4 decimals in dict, but unrounded logit is exact
        reconstructed_prob = _sigmoid(total_logit)

        # Parity with raw probability
        assert np.isclose(raw_prob, reconstructed_prob, atol=1e-12)

        # Direction checks
        for item in all_features:
            if item["log_odds_contribution"] > 0:
                assert item["direction"] == "toward_malignant"
            elif item["log_odds_contribution"] < 0:
                assert item["direction"] == "toward_benign"

        # Input quality check
        iq = result["input_quality"]
        total_counted = (
            iq["within_common_range_count"]
            + iq["unusual_count"]
            + iq["extreme_count"]
            + iq["outside_observed_count"]
        )
        assert total_counted == 30


def test_extreme_outlier_safeguard_detection():
    """Verify input quality identifies extreme outliers outside observed development min/max."""
    dataset = load_breast_cancer()
    feature_names = list(API_TO_WDBC_FEATURE.keys())

    # Start with benign sample
    row = dataset.data[19].copy()
    payload = {feat: float(row[i]) for i, feat in enumerate(feature_names)}

    # Inject an extreme outlier: mean_radius = 999.0
    payload["mean_radius"] = 999.0
    req = PredictionRequest(**payload)
    result = final_ml_runtime_service.predict(req)

    iq = result["input_quality"]
    assert iq["outside_observed_count"] >= 1
    outlier_names = [o["feature"] for o in iq["outliers"]]
    assert "mean_radius" in outlier_names
