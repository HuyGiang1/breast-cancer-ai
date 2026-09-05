#!/usr/bin/env python3
"""Validate frozen final-model metadata and the review registry without training."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import joblib

ROOT = Path(__file__).resolve().parent.parent
FINAL = ROOT / "experiments" / "final"
REGISTRY = ROOT / "models" / "model_registry.example.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError(message)


def main() -> None:
    required = [FINAL / "FINAL_RESULTS_SNAPSHOT.json", FINAL / "ml_model_selection.json", FINAL / "ml_runs" / "logistic_regression" / "model_metadata.json", FINAL / "ml_runs" / "logistic_regression" / "threshold.json", FINAL / "runs" / "efficientnet_b0_full" / "model_metadata.json", FINAL / "runs" / "efficientnet_b0_full" / "threshold.json", FINAL / "calibration_selection.json", REGISTRY]
    require(all(path.is_file() for path in required), "Required final model contract source is missing.")
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))["models"]
    by_id = {entry["id"]: entry for entry in registry}
    ml_entry = by_id["wdbc-logistic-regression-v1"]
    dl_entry = by_id["cbis-efficientnetb0-full-v1"]
    selection = json.loads((FINAL / "ml_model_selection.json").read_text(encoding="utf-8"))
    require(selection["primary_candidate"] == "Logistic Regression", "Frozen ML candidate changed.")
    ml_meta = json.loads((FINAL / "ml_runs" / "logistic_regression" / "model_metadata.json").read_text(encoding="utf-8"))
    ml_threshold = json.loads((FINAL / "ml_runs" / "logistic_regression" / "threshold.json").read_text(encoding="utf-8"))["threshold"]
    ml_path = Path(ml_meta["model_file"])
    require(ml_path.is_file() and digest(ml_path) == ml_meta["model_sha256"], "ML artifact checksum mismatch.")
    require(float(ml_threshold) == 0.36 and ml_entry["decision"]["threshold_probability_space"] == "raw", "ML threshold contract mismatch.")
    ml_model = joblib.load(ml_path)
    require([name for name, _ in ml_model.steps] == ["scaler", "lr"], "ML preprocessing pipeline mismatch.")
    require(ml_model.n_features_in_ == 30 and ml_model.named_steps["lr"].classes_.tolist() == [0, 1], "ML feature/class contract mismatch.")
    dl_meta = json.loads((FINAL / "runs" / "efficientnet_b0_full" / "model_metadata.json").read_text(encoding="utf-8"))
    dl_threshold = json.loads((FINAL / "runs" / "efficientnet_b0_full" / "threshold.json").read_text(encoding="utf-8"))["threshold"]
    dl_path = Path(dl_meta["model_file"])
    require(dl_path.is_file() and digest(dl_path) == dl_meta["sha256"], "DL artifact checksum mismatch.")
    require(abs(float(dl_threshold) - 0.515) < 1e-12 and dl_entry["decision"]["threshold_probability_space"] == "raw", "DL threshold contract mismatch.")
    calibration = json.loads((FINAL / "calibration_selection.json").read_text(encoding="utf-8"))
    require(calibration["selected_method"] == "Platt" and "raw-probability operating points" in calibration["note"], "DL calibration decision mismatch.")
    require(ml_entry["status"] == "promotion_candidate" and dl_entry["status"] == "approved_for_integration", "Registry promotion status mismatch.")
    print("Final model contract validated")


if __name__ == "__main__":
    main()
