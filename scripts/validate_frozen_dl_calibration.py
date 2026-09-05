#!/usr/bin/env python3
"""Validate the versioned EfficientNet-B0 Platt calibration freeze without fitting."""

from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path

from sklearn.metrics import brier_score_loss, log_loss

from app.services.final_dl_calibration import apply_platt_calibration

ROOT = Path(__file__).resolve().parent.parent
FINAL = ROOT / "experiments" / "final"
ARTIFACT = ROOT / "models" / "calibration" / "efficientnet_b0_platt_final_seed42.json"
REGISTRY = ROOT / "models" / "model_registry.example.json"
EQUIVALENCE = FINAL / "dl_calibration" / "efficientnet_b0_platt_equivalence.json"
TOLERANCE = 1e-12


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> None:
    artifact = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    registry = {entry["id"]: entry for entry in json.loads(REGISTRY.read_text(encoding="utf-8"))["models"]}
    dl = registry["cbis-efficientnetb0-full-v1"]
    expected_sha = hashlib.sha256(ARTIFACT.read_bytes()).hexdigest()
    calibration = dl["calibration"]
    require(calibration["artifact"] == "models/calibration/efficientnet_b0_platt_final_seed42.json", "Registry calibration artifact path mismatch.")
    require(calibration["sha256"] == expected_sha, "Registry calibration checksum mismatch.")
    require(artifact["method"] == "platt_logistic_regression" and artifact["classes"] == [0, 1], "Frozen Platt schema mismatch.")
    require(artifact["input_probability_space"] == "raw_malignant_probability" and artifact["decision_probability_space"] == "raw", "Probability space mismatch.")
    require(abs(float(artifact["decision_threshold"]) - 0.515) <= TOLERANCE, "Frozen threshold mismatch.")
    require(all(math.isfinite(float(artifact[key])) for key in ("coefficient", "intercept")), "Frozen Platt parameters are not finite.")
    require("calibration_profile.json" not in json.dumps(artifact), "Legacy calibration profile referenced by final artifact.")
    require(Path(ROOT / artifact["source_validation_predictions"]).is_file(), "Validation prediction source missing.")
    require(json.loads((FINAL / "calibration_selection.json").read_text(encoding="utf-8"))["selected_method"] == "Platt", "Historical selection is not Platt.")
    require(dl["status"] == "approved_for_integration", "DL promotion readiness has not been approved after freeze.")
    require(dl["decision"]["threshold_probability_space"] == "raw", "Registry decision is not raw-space.")

    report = json.loads(EQUIVALENCE.read_text(encoding="utf-8"))
    require(report["calibration_freeze"] == "PASSED" and report["artifact_sha256"] == expected_sha, "Equivalence report does not match artifact.")
    require(max(float(value) for value in report["absolute_deltas"].values()) <= TOLERANCE, "Historical metrics were not reproduced.")
    with (FINAL / "dl_calibration" / "efficientnet_b0_test_calibrated_predictions.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    labels = [int(row["true_label"]) for row in rows]
    calibrated = [apply_platt_calibration(float(row["raw_probability"]), artifact) for row in rows]
    exported = [float(row["calibrated_probability"]) for row in rows]
    require(max(abs(left - right) for left, right in zip(calibrated, exported)) <= TOLERANCE, "Exported test calibrated probabilities do not match frozen JSON.")
    expected = report["expected"]
    require(abs(float(brier_score_loss(labels, calibrated)) - float(expected["Test_Brier"])) <= TOLERANCE, "Test Brier mismatch.")
    require(abs(float(log_loss(labels, calibrated)) - float(expected["Test_LogLoss"])) <= TOLERANCE, "Test log loss mismatch.")
    print("Frozen DL calibration validated")


if __name__ == "__main__":
    main()
