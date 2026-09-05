#!/usr/bin/env python3
"""Generate post-hoc SHAP artifacts for the frozen final WDBC LR candidate."""

from __future__ import annotations

import csv
import hashlib
import json
import os
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")

import joblib
import matplotlib.pyplot as plt
import numpy as np
import shap
from PIL import Image
from sklearn.datasets import load_breast_cancer
from scripts.ml_shap_selection import select_cases

ROOT = Path(__file__).resolve().parent.parent
FINAL = ROOT / "experiments" / "final"
RUN = FINAL / "ml_runs" / "logistic_regression"
FIGURES = FINAL / "figures"
CASE_DIR = FINAL / "ml_shap_cases"
SEED = 42
THRESHOLD = 0.36


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def outcome(true_label: int, predicted_label: int) -> str:
    if true_label and predicted_label:
        return "TP"
    if not true_label and not predicted_label:
        return "TN"
    return "FP" if predicted_label else "FN"




def validate_feature_order(feature_names: list[str], model) -> None:
    scaler = model.named_steps.get("scaler")
    classifier = model.named_steps.get("lr")
    if scaler is None or classifier is None:
        raise RuntimeError("Frozen artifact is not the expected StandardScaler -> LogisticRegression pipeline.")
    if len(feature_names) != 30 or scaler.n_features_in_ != 30 or classifier.coef_.shape != (1, 30):
        raise RuntimeError("Frozen feature dimensions do not match the 30-feature WDBC contract.")
    if hasattr(scaler, "feature_names_in_") and list(scaler.feature_names_in_) != feature_names:
        raise RuntimeError("Frozen scaler feature order differs from WDBC feature names.")


def case_caption(case: dict) -> str:
    true_name = "malignant" if case["true_label"] else "benign"
    predicted_name = "malignant" if case["predicted_label"] else "benign"
    return f"{case['outcome']} | true {true_name}; predicted {predicted_name}; p(malignant)={case['probability']:.3f}; threshold={case['threshold']:.2f}"


def save_waterfall(explanation: shap.Explanation, case: dict) -> Path:
    CASE_DIR.mkdir(parents=True, exist_ok=True)
    path = CASE_DIR / f"{case['outcome'].lower()}_sample_{case['sample_index']}_waterfall.png"
    plt.figure(figsize=(9, 6))
    shap.plots.waterfall(explanation, max_display=10, show=False)
    plt.title(case_caption(case), fontsize=10)
    plt.tight_layout(); plt.savefig(path, dpi=180, bbox_inches="tight"); plt.close()
    return path


def save_global_plots(values: np.ndarray, transformed_test: np.ndarray, feature_names: list[str]) -> tuple[Path, Path]:
    FIGURES.mkdir(parents=True, exist_ok=True)
    summary = FIGURES / "ml_shap_summary.png"; bar = FIGURES / "ml_shap_bar.png"
    plt.figure(figsize=(9, 7))
    shap.summary_plot(values, transformed_test, feature_names=feature_names, max_display=20, show=False)
    plt.title("WDBC Logistic Regression SHAP summary (log-odds output)")
    plt.tight_layout(); plt.savefig(summary, dpi=180, bbox_inches="tight"); plt.close()
    plt.figure(figsize=(8, 6))
    shap.summary_plot(values, transformed_test, feature_names=feature_names, plot_type="bar", max_display=15, show=False)
    plt.title("Mean absolute SHAP contribution (log-odds)")
    plt.tight_layout(); plt.savefig(bar, dpi=180, bbox_inches="tight"); plt.close()
    return summary, bar


def save_composite(bar: Path, case_paths: dict[str, Path]) -> None:
    ordered = [("Global mean |SHAP|", bar), ("Representative TP", case_paths["TP"]), ("False negative", case_paths["FN"])]
    figure, axes = plt.subplots(1, 3, figsize=(18, 6))
    for axis, (title, path) in zip(axes, ordered):
        with Image.open(path) as image:
            axis.imshow(image.convert("RGB"))
        axis.set_title(title); axis.axis("off")
    figure.tight_layout(); figure.savefig(FIGURES / "ml_shap_examples.png", dpi=180); plt.close(figure)


def main() -> None:
    metadata = json.loads((RUN / "model_metadata.json").read_text(encoding="utf-8"))
    model_path = Path(metadata["model_file"])
    if not model_path.is_file() or sha256(model_path) != metadata["model_sha256"]:
        raise RuntimeError("Frozen Logistic Regression artifact is missing or its SHA-256 does not match metadata.")
    if metadata["calibration"] != "raw" or float(metadata["threshold"]) != THRESHOLD or metadata["label_convention"] != "1=malignant, 0=benign":
        raise RuntimeError("Frozen ML metadata does not match the pre-specified raw/0.36/malignant convention.")
    model = joblib.load(model_path)
    dataset = load_breast_cancer()
    feature_names = list(dataset.feature_names)
    validate_feature_order(feature_names, model)
    labels = (dataset.target == 0).astype(int)
    split_rows = read_csv(FINAL / "ml_split_seed42.csv")
    development_indices = np.asarray([int(row["sample_index"]) for row in split_rows if row["split"] == "development"])
    locked_test_indices = {int(row["sample_index"]) for row in split_rows if row["split"] == "test"}
    prediction_rows = read_csv(RUN / "test_predictions.csv")
    test_indices = np.asarray([int(row["sample_index"]) for row in prediction_rows])
    if len(development_indices) != 455 or len(test_indices) != 114 or set(test_indices) != locked_test_indices:
        raise RuntimeError("Frozen split/test prediction mapping is inconsistent.")
    if any(int(row["true_label"]) != int(labels[index]) for row, index in zip(prediction_rows, test_indices)):
        raise RuntimeError("Frozen prediction labels do not match the WDBC label convention.")
    scaler = model.named_steps["scaler"]
    classifier = model.named_steps["lr"]
    background = scaler.transform(dataset.data[development_indices])
    transformed_test = scaler.transform(dataset.data[test_indices])
    frozen_probability = model.predict_proba(dataset.data[test_indices])[:, 1]
    exported_probability = np.asarray([float(row["probability"]) for row in prediction_rows])
    if not np.allclose(frozen_probability, exported_probability, atol=1e-12):
        raise RuntimeError("Frozen model probabilities do not reproduce the final test export.")
    explainer = shap.LinearExplainer(classifier, background, feature_perturbation="interventional")
    raw_explanation = explainer(transformed_test)
    explanation = shap.Explanation(
        values=raw_explanation.values,
        base_values=raw_explanation.base_values,
        data=transformed_test,
        feature_names=feature_names,
    )
    values = np.asarray(explanation.values)
    if values.shape != (114, 30) or not np.isfinite(values).all():
        raise RuntimeError("Unexpected SHAP value shape or non-finite SHAP values.")
    mean_abs = np.mean(np.abs(values), axis=0); mean = np.mean(values, axis=0)
    order = np.argsort(-mean_abs, kind="stable")
    global_rows = [{"Feature": feature_names[index], "MeanAbsSHAP": float(mean_abs[index]), "MeanSHAP": float(mean[index]), "Rank": rank} for rank, index in enumerate(order, start=1)]
    write_csv(FINAL / "ml_shap_global.csv", global_rows)
    coefficient_rows = [{"Feature": feature_names[index], "StandardizedCoefficient": float(classifier.coef_[0, index])} for index in range(30)]
    write_csv(FINAL / "ml_logistic_coefficients.csv", coefficient_rows)
    row_by_index = {}
    for position, (index, export) in enumerate(zip(test_indices, prediction_rows)):
        probability = float(export["probability"]); predicted = int(export["prediction"]); true = int(export["true_label"])
        row_by_index[int(index)] = {"sample_index": int(index), "test_position": position, "true_label": true, "predicted_label": predicted, "probability": probability, "threshold": THRESHOLD, "outcome": outcome(true, predicted), "confidence_distance_from_threshold": abs(probability - THRESHOLD)}
    selected = select_cases(list(row_by_index.values()))
    for case in selected:
        case["output_scale"] = "log-odds of malignant class"
        case["explainer"] = "shap.LinearExplainer"
    selection = {"model": "Logistic Regression", "model_sha256": metadata["model_sha256"], "dataset": "sklearn.datasets.load_breast_cancer", "label_convention": "1=malignant, 0=benign", "threshold": THRESHOLD, "calibration": "raw", "background": "455 frozen development samples only", "explainer": "shap.LinearExplainer(classifier, standardized development background, feature_perturbation=interventional)", "output_scale": "log-odds of malignant class", "selection_rule": "TP/TN nearest median absolute distance from frozen threshold; all FP; all FN.", "selected_cases": selected}
    (FINAL / "ml_shap_selection.json").write_text(json.dumps(selection, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    case_paths: dict[str, Path] = {}
    local_rows, contribution_rows = [], []
    for case in selected:
        path = save_waterfall(explanation[case["test_position"]], case)
        case_paths.setdefault(case["outcome"], path)
        local_rows.append({**case, "waterfall_path": str(path.relative_to(ROOT))})
        local_values = values[case["test_position"]]
        for rank, feature_index in enumerate(np.argsort(-np.abs(local_values), kind="stable"), start=1):
            contribution_rows.append({"sample_index": case["sample_index"], "outcome": case["outcome"], "Feature": feature_names[feature_index], "SHAP": float(local_values[feature_index]), "AbsSHAP": float(abs(local_values[feature_index])), "Rank": rank})
    write_csv(CASE_DIR / "metadata.csv", local_rows)
    write_csv(CASE_DIR / "local_contributions.csv", contribution_rows)
    summary, bar = save_global_plots(values, transformed_test, feature_names)
    save_composite(bar, case_paths)
    print(json.dumps({"explainer": selection["explainer"], "output_scale": selection["output_scale"], "top_features": [row["Feature"] for row in global_rows[:10]], "selected_cases": len(selected), "summary": str(summary)}, indent=2))


if __name__ == "__main__":
    main()
