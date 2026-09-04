from scripts.generate_final_ml_shap import select_cases


def test_shap_case_selection_is_deterministic_and_includes_all_errors():
    rows = [
        {"sample_index": 1, "outcome": "TP", "confidence_distance_from_threshold": 0.10},
        {"sample_index": 2, "outcome": "TP", "confidence_distance_from_threshold": 0.20},
        {"sample_index": 3, "outcome": "TP", "confidence_distance_from_threshold": 0.30},
        {"sample_index": 4, "outcome": "TN", "confidence_distance_from_threshold": 0.10},
        {"sample_index": 5, "outcome": "TN", "confidence_distance_from_threshold": 0.20},
        {"sample_index": 6, "outcome": "TN", "confidence_distance_from_threshold": 0.30},
        {"sample_index": 7, "outcome": "FP", "confidence_distance_from_threshold": 0.15},
        {"sample_index": 8, "outcome": "FN", "confidence_distance_from_threshold": 0.25},
        {"sample_index": 9, "outcome": "FN", "confidence_distance_from_threshold": 0.35},
    ]
    selected = select_cases(rows)
    assert [row["sample_index"] for row in selected] == [2, 5, 7, 8, 9]
