from app.api.endpoints import _build_uncertainty_payload


def test_final_ml_uncertainty_uses_its_frozen_threshold_not_fifty_percent():
    payload = _build_uncertainty_payload(
        displayed_malignant_probability=0.36,
        decision_probability=0.36,
        decision_threshold=0.36,
        label="ML",
    )
    assert "36%" in payload["uncertainty_reasons"][0]
    assert "50%" not in payload["uncertainty_reasons"][0]


def test_final_dl_uncertainty_uses_raw_probability_against_raw_threshold():
    payload = _build_uncertainty_payload(
        displayed_malignant_probability=0.62,
        decision_probability=0.515,
        decision_threshold=0.515,
        label="DL",
    )
    assert "51.5%" in payload["uncertainty_reasons"][0]


def test_multimodal_uncertainty_does_not_mislabel_probability_ambiguity_as_threshold():
    payload = _build_uncertainty_payload(displayed_malignant_probability=0.5, label="đa phương thức")
    assert "không phải ngưỡng phân loại" in payload["uncertainty_reasons"][0]
