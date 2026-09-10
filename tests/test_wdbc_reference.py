from __future__ import annotations

import json
from pathlib import Path
import pytest
from sklearn.datasets import load_breast_cancer

from scripts.build_wdbc_feature_reference import (
    API_FEATURE_ORDER,
    FEATURE_DEFINITIONS,
    generate_reference_data,
    load_development_indices,
)

ROOT = Path(__file__).resolve().parents[1]
EXP_REF = ROOT / "experiments" / "final" / "wdbc_feature_reference.json"
FE_REF = ROOT / "frontend" / "content" / "wdbc_feature_reference.json"


def test_development_split_counts_and_exclusion():
    dev_idx, test_idx = load_development_indices()
    assert len(dev_idx) == 455
    assert len(test_idx) == 114
    assert len(dev_idx) + len(test_idx) == 569

    # Strict exclusion check: no overlap between dev and test
    dev_set = set(dev_idx)
    test_set = set(test_idx)
    assert len(dev_set.intersection(test_set)) == 0


def test_reference_artifact_structure_and_order():
    data = generate_reference_data()
    meta = data["metadata"]

    assert meta["dataset"] == "WDBC"
    assert meta["source"] == "sklearn.datasets.load_breast_cancer"
    assert meta["outer_split_seed"] == 42
    assert meta["development_n"] == 455
    assert meta["test_n"] == 114
    assert meta["reference_scope"] == "development_only"
    assert meta["feature_count"] == 30

    features = data["features"]
    assert len(features) == 30
    assert list(features.keys()) == API_FEATURE_ORDER

    required_keys = {
        "api_name",
        "display_name",
        "group",
        "description",
        "min",
        "p01",
        "p05",
        "median",
        "p95",
        "p99",
        "max",
        "mean",
        "std",
        "n_development",
    }

    for name, feat in features.items():
        assert required_keys.issubset(feat.keys()), f"Missing keys in {name}"
        assert feat["n_development"] == 455
        assert feat["min"] <= feat["p01"] <= feat["p05"] <= feat["median"] <= feat["p95"] <= feat["p99"] <= feat["max"]
        assert feat["std"] > 0
        assert feat["group"] in {"Mean", "Standard Error", "Worst"}


def test_saved_json_files_match_deterministic_generation():
    assert EXP_REF.is_file(), f"Missing {EXP_REF}"
    assert FE_REF.is_file(), f"Missing {FE_REF}"

    fresh = generate_reference_data()

    with open(EXP_REF, "r", encoding="utf-8") as f:
        saved_exp = json.load(f)
    with open(FE_REF, "r", encoding="utf-8") as f:
        saved_fe = json.load(f)

    assert saved_exp == fresh
    assert saved_fe == fresh
