#!/usr/bin/env python3
"""Materialize the already-selected final EfficientNet-B0 Platt transform.

This is an artifact-freeze procedure, not a new calibration experiment. It
reuses the historical scalar-probability LogisticRegression implementation and
fits only frozen validation labels. Test labels are read only after fitting to
verify the historical descriptive metrics.
"""

from __future__ import annotations

import csv
import hashlib
import json
import platform
import sys
from pathlib import Path

import numpy as np
import sklearn
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, log_loss
from sklearn.model_selection import StratifiedKFold

ROOT = Path(__file__).resolve().parent.parent
FINAL = ROOT / "experiments" / "final"
RUN = FINAL / "runs" / "efficientnet_b0_full"
ARTIFACT = ROOT / "models" / "calibration" / "efficientnet_b0_platt_final_seed42.json"
CALIBRATION_DIR = FINAL / "dl_calibration"
SEED = 42
TOLERANCE = 1e-12


def load_predictions(name: str) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    with (RUN / f"{name}_predictions.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    required = {"index", "label", "malignant_probability"}
    if not rows or set(rows[0]) < required:
        raise RuntimeError(f"{name} prediction export is missing required columns.")
    indices = np.asarray([int(row["index"]) for row in rows], dtype=int)
    labels = np.asarray([int(row["label"]) for row in rows], dtype=int)
    probabilities = np.asarray([float(row["malignant_probability"]) for row in rows], dtype=float)
    if set(np.unique(labels)) != {0, 1} or not np.isfinite(probabilities).all() or np.any((probabilities < 0) | (probabilities > 1)):
        raise RuntimeError(f"{name} prediction export violates the frozen binary raw-probability contract.")
    return indices, labels, probabilities


def platt_model(raw_probability: np.ndarray, labels: np.ndarray) -> LogisticRegression:
    """Exact historical `platt_fit`: LogisticRegression on scalar raw p, identity input."""
    return LogisticRegression(C=1e6, solver="lbfgs").fit(raw_probability.reshape(-1, 1), labels)


def platt_oof(raw_probability: np.ndarray, labels: np.ndarray) -> np.ndarray:
    output = np.zeros_like(raw_probability)
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
    for train, holdout in cv.split(raw_probability, labels):
        output[holdout] = platt_model(raw_probability[train], labels[train]).predict_proba(raw_probability[holdout].reshape(-1, 1))[:, 1]
    return output


def ece(labels: np.ndarray, probabilities: np.ndarray, bins: int = 10) -> float:
    edges = np.linspace(0, 1, bins + 1)
    result = 0.0
    for lo, hi in zip(edges[:-1], edges[1:]):
        mask = (probabilities >= lo) & (probabilities < hi if hi < 1 else probabilities <= hi)
        if mask.any():
            result += mask.mean() * abs(labels[mask].mean() - probabilities[mask].mean())
    return float(result)


def metrics(labels: np.ndarray, probabilities: np.ndarray) -> dict[str, float]:
    clipped = np.clip(probabilities, 1e-6, 1 - 1e-6)
    return {
        "Brier": float(brier_score_loss(labels, probabilities)),
        "LogLoss": float(log_loss(labels, clipped)),
        "ECE_10bin": ece(labels, probabilities),
    }


def historical_platt_metrics() -> dict[str, float]:
    with (FINAL / "calibration_metrics.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    row = next((row for row in rows if row["Method"] == "Platt"), None)
    if row is None:
        raise RuntimeError("Historical Platt metrics row is missing.")
    return {"Validation_Brier": float(row["Validation_Brier"]), "Validation_LogLoss": float(row["Validation_LogLoss"]), "Validation_ECE_10bin": float(row["Validation_ECE_10bin"]), "Test_Brier": float(row["Test_Brier"]), "Test_LogLoss": float(row["Test_LogLoss"]), "Test_ECE_10bin": float(row["Test_ECE_10bin"])}


def write_predictions(path: Path, indices: np.ndarray, labels: np.ndarray, raw: np.ndarray, calibrated: np.ndarray) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["sample_index", "true_label", "raw_probability", "calibrated_probability"])
        writer.writeheader()
        writer.writerows({"sample_index": int(index), "true_label": int(label), "raw_probability": float(raw_value), "calibrated_probability": float(calibrated_value)} for index, label, raw_value, calibrated_value in zip(indices, labels, raw, calibrated))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    selection = json.loads((FINAL / "calibration_selection.json").read_text(encoding="utf-8"))
    if selection.get("selected_method") != "Platt":
        raise RuntimeError("Frozen calibration selection is not Platt.")
    metadata = json.loads((RUN / "model_metadata.json").read_text(encoding="utf-8"))
    threshold = float(json.loads((RUN / "threshold.json").read_text(encoding="utf-8"))["threshold"])
    if abs(threshold - 0.515) > TOLERANCE:
        raise RuntimeError("Frozen DL threshold is not 0.515 raw probability.")

    val_index, y_val, p_val = load_predictions("validation")
    test_index, y_test, p_test = load_predictions("test")
    # Historical selection metric: five independently fit validation-fold models.
    p_val_oof = platt_oof(p_val, y_val)
    # Runtime display artifact: one model fit on all frozen validation data only.
    model = platt_model(p_val, y_val)
    p_test_calibrated = model.predict_proba(p_test.reshape(-1, 1))[:, 1]

    expected = historical_platt_metrics()
    observed = {**{f"Validation_{name}": value for name, value in metrics(y_val, p_val_oof).items()}, **{f"Test_{name}": value for name, value in metrics(y_test, p_test_calibrated).items()}}
    deltas = {name: abs(observed[name] - expected[name]) for name in expected}
    if any(delta > TOLERANCE for delta in deltas.values()):
        raise RuntimeError(f"CALIBRATION_FREEZE = FAILED: historical metric mismatch: {deltas}")

    artifact = {
        "schema_version": 1,
        "id": "efficientnet-b0-platt-final-seed42",
        "method": "platt_logistic_regression",
        "study": "CBIS-DDSM imaging DL",
        "model_id": "cbis-efficientnetb0-full-v1",
        "fitting_split": "validation",
        "selection_method": "5-fold OOF validation",
        "input_probability_space": "raw_malignant_probability",
        "output_probability_space": "platt_calibrated_malignant_probability",
        "fit_input_transform": "identity",
        "coefficient": float(model.coef_[0][0]),
        "intercept": float(model.intercept_[0]),
        "classes": [int(value) for value in model.classes_],
        "C": 1000000.0,
        "solver": "lbfgs",
        "validation_sample_count": int(len(y_val)),
        "source_validation_predictions": "experiments/final/runs/efficientnet_b0_full/validation_predictions.csv",
        "source_selection": "experiments/final/calibration_selection.json",
        "source_script": "scripts/analyze_final_dl_reliability.py",
        "sklearn_version": sklearn.__version__,
        "python_implementation": platform.python_implementation(),
        "model_sha256": metadata["sha256"],
        "decision_probability_space": "raw",
        "decision_threshold": threshold,
        "notes": "Calibration is for reliability/display; frozen classification operating point remains raw-space. Validation calibrated predictions reproduce the historical 5-fold OOF selection procedure; test predictions use this full-validation frozen transform.",
    }
    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    CALIBRATION_DIR.mkdir(parents=True, exist_ok=True)
    write_predictions(CALIBRATION_DIR / "efficientnet_b0_validation_calibrated_predictions.csv", val_index, y_val, p_val, p_val_oof)
    write_predictions(CALIBRATION_DIR / "efficientnet_b0_test_calibrated_predictions.csv", test_index, y_test, p_test, p_test_calibrated)
    report = {"calibration_freeze": "PASSED", "tolerance": TOLERANCE, "historical_validation_mode": "5-fold OOF Platt", "frozen_runtime_transform_fit": "all frozen validation rows", "observed": observed, "expected": expected, "absolute_deltas": deltas, "artifact_sha256": sha256(ARTIFACT), "test_labels_used_for_fit": False}
    (CALIBRATION_DIR / "efficientnet_b0_platt_equivalence.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"CALIBRATION_FREEZE = PASSED; artifact_sha256={report['artifact_sha256']}; max_delta={max(deltas.values()):.3e}")


if __name__ == "__main__":
    main()
