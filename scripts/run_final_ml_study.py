#!/usr/bin/env python3
"""Reproducible final WDBC ML evaluation with a locked outer test split.

All model, calibration, and threshold choices are made from development-set
out-of-fold predictions. The outer test split is written once and only used
after those choices have been frozen.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")

import joblib
import matplotlib.pyplot as plt
import numpy as np
from sklearn.datasets import load_breast_cancer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, average_precision_score, balanced_accuracy_score,
                             brier_score_loss, confusion_matrix, f1_score, log_loss,
                             precision_score, recall_score, roc_auc_score)
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

ROOT = Path(__file__).resolve().parent.parent
FINAL = ROOT / "experiments" / "final"
RUNS = FINAL / "ml_runs"
FIGURES = FINAL / "figures"
SEED = 42
TEST_SIZE = 0.20
FOLDS = 5


@dataclass(frozen=True)
class ModelSpec:
    slug: str
    name: str


SPECS = (
    ModelSpec("logistic_regression", "Logistic Regression"),
    ModelSpec("random_forest", "Random Forest"),
    ModelSpec("xgboost", "XGBoost"),
)


def build_model(slug: str):
    if slug == "logistic_regression":
        return Pipeline([
            ("scaler", StandardScaler()),
            ("lr", LogisticRegression(max_iter=5000, solver="liblinear", random_state=SEED, class_weight="balanced")),
        ])
    if slug == "random_forest":
        return RandomForestClassifier(
            n_estimators=600, max_depth=None, min_samples_leaf=2,
            class_weight="balanced_subsample", random_state=SEED, n_jobs=-1,
        )
    if slug == "xgboost":
        return XGBClassifier(
            n_estimators=300, max_depth=3, learning_rate=0.05, subsample=0.9,
            colsample_bytree=0.9, objective="binary:logistic", eval_metric="logloss",
            random_state=SEED, n_jobs=1, tree_method="hist",
        )
    raise ValueError(f"Unknown model: {slug}")


def metrics(y: np.ndarray, probability: np.ndarray, threshold: float) -> dict[str, float | int]:
    prediction = (probability >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y, prediction, labels=[0, 1]).ravel()
    clipped = np.clip(probability, 1e-6, 1 - 1e-6)
    return {
        "accuracy": float(accuracy_score(y, prediction)),
        "precision": float(precision_score(y, prediction, zero_division=0)),
        "sensitivity": float(recall_score(y, prediction, zero_division=0)),
        "specificity": float(tn / (tn + fp)) if tn + fp else 0.0,
        "f1": float(f1_score(y, prediction, zero_division=0)),
        "balanced_accuracy": float(balanced_accuracy_score(y, prediction)),
        "roc_auc": float(roc_auc_score(y, probability)),
        "pr_auc": float(average_precision_score(y, probability)),
        "brier_score": float(brier_score_loss(y, probability)),
        "log_loss": float(log_loss(y, clipped)),
        "tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp),
    }


def ece(y: np.ndarray, probability: np.ndarray, bins: int = 10) -> float:
    result = 0.0
    for low, high in zip(np.linspace(0, 1, bins + 1)[:-1], np.linspace(0, 1, bins + 1)[1:]):
        mask = (probability >= low) & (probability < high if high < 1 else probability <= high)
        if mask.any():
            result += float(mask.mean() * abs(y[mask].mean() - probability[mask].mean()))
    return float(result)


def calibration_crossfit(y: np.ndarray, raw: np.ndarray, cv: StratifiedKFold) -> tuple[dict[str, np.ndarray], list[dict]]:
    """Evaluate raw and Platt calibration without fitting a calibrator on its scored fold."""
    platt = np.empty_like(raw)
    for train, holdout in cv.split(raw, y):
        calibrator = LogisticRegression(C=1e6, solver="lbfgs", random_state=SEED)
        calibrator.fit(raw[train].reshape(-1, 1), y[train])
        platt[holdout] = calibrator.predict_proba(raw[holdout].reshape(-1, 1))[:, 1]
    methods = {"raw": raw, "platt": platt}
    rows = []
    for method, probability in methods.items():
        clipped = np.clip(probability, 1e-6, 1 - 1e-6)
        rows.append({"calibration": method, "brier_score": float(brier_score_loss(y, probability)),
                     "log_loss": float(log_loss(y, clipped)), "ece_10bin": ece(y, probability)})
    return methods, rows


def select_threshold(y: np.ndarray, probability: np.ndarray) -> tuple[float, list[dict]]:
    rows = []
    for threshold in np.round(np.arange(0.05, 0.951, 0.01), 2):
        row = metrics(y, probability, float(threshold))
        rows.append({"threshold": float(threshold), **{key: row[key] for key in ("sensitivity", "specificity", "precision", "f1", "balanced_accuracy", "fp", "fn")}})
    selected = max(rows, key=lambda row: (row["balanced_accuracy"], row["sensitivity"], -row["fn"], -row["fp"], -row["threshold"]))
    return float(selected["threshold"]), rows


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError(f"Cannot write an empty CSV: {path}")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)


def json_write(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2, default=str) + "\n", encoding="utf-8")


def probability_checks(probability: np.ndarray) -> None:
    if not np.isfinite(probability).all() or np.any(probability < 0) or np.any(probability > 1):
        raise RuntimeError("Model produced invalid probabilities.")
    if float(np.std(probability)) < 1e-6:
        raise RuntimeError("Model produced degenerate constant probabilities.")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def plot_curves(y_test: np.ndarray, results: dict[str, dict]) -> None:
    from sklearn.metrics import PrecisionRecallDisplay, RocCurveDisplay
    FIGURES.mkdir(parents=True, exist_ok=True)
    figure, axis = plt.subplots(figsize=(6.5, 5.2))
    for name, result in results.items():
        RocCurveDisplay.from_predictions(y_test, result["test_probability"], name=name, ax=axis)
    axis.plot([0, 1], [0, 1], "k--", linewidth=1)
    figure.tight_layout(); figure.savefig(FIGURES / "ml_roc_comparison.png", dpi=180); plt.close(figure)
    figure, axis = plt.subplots(figsize=(6.5, 5.2))
    for name, result in results.items():
        PrecisionRecallDisplay.from_predictions(y_test, result["test_probability"], name=name, ax=axis)
    figure.tight_layout(); figure.savefig(FIGURES / "ml_pr_comparison.png", dpi=180); plt.close(figure)


def plot_confusions(y_test: np.ndarray, results: dict[str, dict]) -> None:
    figure, axes = plt.subplots(1, len(results), figsize=(4.4 * len(results), 4))
    for axis, (name, result) in zip(np.atleast_1d(axes), results.items()):
        matrix = confusion_matrix(y_test, result["test_prediction"], labels=[0, 1])
        axis.imshow(matrix, cmap="Blues")
        for (row, col), value in np.ndenumerate(matrix): axis.text(col, row, str(value), ha="center", va="center")
        axis.set(title=name, xticks=[0, 1], yticks=[0, 1], xticklabels=["Benign", "Malignant"], yticklabels=["Benign", "Malignant"], xlabel="Predicted", ylabel="True")
    figure.tight_layout(); figure.savefig(FIGURES / "ml_confusion_matrices.png", dpi=180); plt.close(figure)


def plot_calibration(y_dev: np.ndarray, results: dict[str, dict]) -> None:
    from sklearn.calibration import calibration_curve
    figure, axis = plt.subplots(figsize=(6.5, 5.2))
    for name, result in results.items():
        observed, predicted = calibration_curve(y_dev, result["selected_oof_probability"], n_bins=10, strategy="uniform")
        axis.plot(predicted, observed, marker="o", label=f"{name} ({result['calibration']})")
    axis.plot([0, 1], [0, 1], "k--", linewidth=1); axis.set(xlabel="Mean predicted probability", ylabel="Observed malignant frequency")
    axis.legend(fontsize=8); figure.tight_layout(); figure.savefig(FIGURES / "ml_calibration_comparison.png", dpi=180); plt.close(figure)


def plot_thresholds(results: dict[str, dict]) -> None:
    figure, axis = plt.subplots(figsize=(7, 5.2))
    for name, result in results.items():
        sweep = result["threshold_rows"]
        axis.plot([row["threshold"] for row in sweep], [row["balanced_accuracy"] for row in sweep], label=f"{name} balanced accuracy")
        axis.axvline(result["threshold"], linewidth=1, linestyle="--")
    axis.set(xlabel="Development OOF threshold", ylabel="Balanced accuracy"); axis.legend(fontsize=8); figure.tight_layout()
    figure.savefig(FIGURES / "ml_threshold_tradeoff.png", dpi=180); plt.close(figure)


def bootstrap(y: np.ndarray, probability: np.ndarray, threshold: float) -> list[dict]:
    rng = np.random.default_rng(SEED)
    values = {key: [] for key in ("roc_auc", "pr_auc", "sensitivity", "specificity", "balanced_accuracy")}
    for _ in range(2000):
        index = rng.integers(0, len(y), len(y)); y_sample, p_sample = y[index], probability[index]
        if len(np.unique(y_sample)) < 2: continue
        sample = metrics(y_sample, p_sample, threshold)
        for key in values: values[key].append(sample[key])
    point = metrics(y, probability, threshold)
    return [{"metric": key, "point_estimate": point[key], "ci95_lower": float(np.quantile(values[key], .025)),
             "ci95_upper": float(np.quantile(values[key], .975)), "bootstrap_iterations": 2000,
             "valid_iterations": len(values[key]), "seed": SEED} for key in values]


def main() -> None:
    dataset = load_breast_cancer()
    x = dataset.data
    # sklearn target 0 is malignant and 1 is benign; research convention is intentionally inverted.
    y = (dataset.target == 0).astype(int)
    if x.shape != (569, 30) or int(y.sum()) != 212 or int((y == 0).sum()) != 357:
        raise RuntimeError("Unexpected WDBC dataset contract.")
    all_index = np.arange(len(y))
    development_index, test_index = train_test_split(all_index, test_size=TEST_SIZE, random_state=SEED, stratify=y)
    split_rows = [{"sample_index": int(index), "split": "development" if index in set(development_index) else "test", "true_label": int(y[index])} for index in all_index]
    json_write(FINAL / "ml_dataset_statistics.json", {"dataset": "sklearn.datasets.load_breast_cancer", "total_samples": 569, "features": 30, "malignant_count": 212, "benign_count": 357, "label_convention": {"1": "malignant", "0": "benign"}, "outer_test_size": TEST_SIZE, "seed": SEED})
    write_csv(FINAL / "ml_split_seed42.csv", split_rows)
    x_dev, x_test, y_dev, y_test = x[development_index], x[test_index], y[development_index], y[test_index]
    cv = StratifiedKFold(n_splits=FOLDS, shuffle=True, random_state=SEED)
    results: dict[str, dict] = {}
    global_cv_rows, global_oof_rows, global_calibration_rows, global_threshold_rows, global_test_rows, global_error_rows, global_bootstrap_rows = [], [], [], [], [], [], []

    for spec in SPECS:
        run = RUNS / spec.slug; run.mkdir(parents=True, exist_ok=True)
        log_lines = [f"model={spec.name}", "protocol=outer holdout seed42; 5-fold stratified development OOF"]
        raw_oof = np.empty(len(y_dev)); fold_rows = []
        for fold, (train, holdout) in enumerate(cv.split(x_dev, y_dev), start=1):
            model = build_model(spec.slug); model.fit(x_dev[train], y_dev[train])
            probability = model.predict_proba(x_dev[holdout])[:, 1]; probability_checks(probability)
            raw_oof[holdout] = probability
            fold_metric = metrics(y_dev[holdout], probability, 0.5)
            fold_rows.append({"model": spec.name, "fold": fold, **{key: fold_metric[key] for key in ("roc_auc", "pr_auc", "sensitivity", "specificity", "balanced_accuracy")}})
        probability_checks(raw_oof)
        calibration_methods, calibration_rows = calibration_crossfit(y_dev, raw_oof, cv)
        selected_calibration = min(calibration_rows, key=lambda row: (row["brier_score"], row["log_loss"]))["calibration"]
        selected_oof = calibration_methods[selected_calibration]
        threshold, threshold_rows = select_threshold(y_dev, selected_oof)
        oof_metric = metrics(y_dev, selected_oof, threshold)
        summary_row = {"model": spec.name, "fold": "mean", **{key: float(np.mean([row[key] for row in fold_rows])) for key in ("roc_auc", "pr_auc", "sensitivity", "specificity", "balanced_accuracy")}}
        std_row = {"model": spec.name, "fold": "std", **{key: float(np.std([row[key] for row in fold_rows], ddof=1)) for key in ("roc_auc", "pr_auc", "sensitivity", "specificity", "balanced_accuracy")}}
        cv_rows = fold_rows + [summary_row, std_row]
        calibrator = None
        if selected_calibration == "platt":
            calibrator = LogisticRegression(C=1e6, solver="lbfgs", random_state=SEED).fit(raw_oof.reshape(-1, 1), y_dev)
        final_model = build_model(spec.slug); final_model.fit(x_dev, y_dev)
        model_path = run / f"{spec.slug}_final_seed42.joblib"; joblib.dump(final_model, model_path)
        raw_test = final_model.predict_proba(x_test)[:, 1]; probability_checks(raw_test)
        test_probability = calibrator.predict_proba(raw_test.reshape(-1, 1))[:, 1] if calibrator is not None else raw_test
        probability_checks(test_probability)
        test_metric = metrics(y_test, test_probability, threshold)
        test_prediction = (test_probability >= threshold).astype(int)
        metadata = {"model": spec.name, "model_file": str(model_path), "model_sha256": sha256(model_path), "dataset": "sklearn.datasets.load_breast_cancer", "label_convention": "1=malignant, 0=benign", "outer_split": {"test_size": TEST_SIZE, "random_state": SEED, "stratify": "malignant label"}, "development_cv": {"n_splits": FOLDS, "shuffle": True, "random_state": SEED}, "calibration": selected_calibration, "threshold": threshold}
        config = {"model": spec.name, "seed": SEED, "outer_test_size": TEST_SIZE, "cv": FOLDS, "configuration": final_model.get_params(deep=False)}
        json_write(run / "config.json", config); json_write(run / "cv_metrics.json", {"folds": fold_rows, "mean": summary_row, "std": std_row, "oof_metrics": oof_metric}); write_csv(run / "cv_metrics.csv", cv_rows)
        oof_rows = [{"model": spec.name, "development_index": int(development_index[index]), "fold": next(fold for fold, (_, holdout) in enumerate(cv.split(x_dev, y_dev), start=1) if index in holdout), "true_label": int(y_dev[index]), "raw_probability": float(raw_oof[index]), "selected_probability": float(selected_oof[index]), "selected_calibration": selected_calibration} for index in range(len(y_dev))]
        write_csv(run / "oof_predictions.csv", oof_rows)
        json_write(run / "calibration.json", {"selected": selected_calibration, "selection_split": "development OOF", "criterion": "minimum cross-fitted Brier score, then log loss", "methods": calibration_rows}); write_csv(run / "calibration_metrics.csv", [{"model": spec.name, **row} for row in calibration_rows])
        write_csv(run / "threshold_analysis.csv", [{"model": spec.name, **row} for row in threshold_rows]); json_write(run / "threshold.json", {"threshold": threshold, "selected_on": "development OOF", "objective": "maximum balanced accuracy; then sensitivity, fewer FN/FP, lower threshold"})
        test_rows = [{"sample_index": int(test_index[index]), "true_label": int(y_test[index]), "raw_probability": float(raw_test[index]), "probability": float(test_probability[index]), "prediction": int(test_prediction[index]), "threshold": threshold} for index in range(len(y_test))]
        write_csv(run / "test_predictions.csv", test_rows); json_write(run / "metrics.json", test_metric); json_write(run / "model_metadata.json", metadata)
        (run / "training.log").write_text("\n".join(log_lines + [f"calibration={selected_calibration}", f"threshold={threshold}", f"test_roc_auc={test_metric['roc_auc']}"]) + "\n", encoding="utf-8")
        results[spec.name] = {"spec": spec, "calibration": selected_calibration, "threshold": threshold, "raw_oof": raw_oof, "selected_oof_probability": selected_oof, "threshold_rows": threshold_rows, "test_probability": test_probability, "test_prediction": test_prediction, "test_metric": test_metric, "cv_rows": cv_rows, "calibration_rows": calibration_rows, "test_rows": test_rows, "model_metadata": metadata}
        global_cv_rows.extend(cv_rows); global_oof_rows.extend(oof_rows); global_calibration_rows.extend([{"model": spec.name, **row} for row in calibration_rows]); global_threshold_rows.extend([{"model": spec.name, **row} for row in threshold_rows]); global_test_rows.append({"model": spec.name, "calibration": selected_calibration, "threshold": threshold, **test_metric})

    # Candidate selection is completely development-first, after calibration and threshold choices.
    primary_name = max(results, key=lambda name: (metrics(y_dev, results[name]["selected_oof_probability"], results[name]["threshold"])["roc_auc"], metrics(y_dev, results[name]["selected_oof_probability"], results[name]["threshold"])["pr_auc"], metrics(y_dev, results[name]["selected_oof_probability"], results[name]["threshold"])["balanced_accuracy"]))
    for name, result in results.items():
        for index, row in enumerate(result["test_rows"]):
            outcome = "TP" if row["true_label"] and row["prediction"] else "TN" if not row["true_label"] and not row["prediction"] else "FP" if row["prediction"] else "FN"
            global_error_rows.append({"model": name, **row, "outcome_type": outcome, "confidence_distance_from_threshold": abs(row["probability"] - row["threshold"])})
        global_bootstrap_rows.extend([{"model": name, **row} for row in bootstrap(y_test, result["test_probability"], result["threshold"])])
    write_csv(FINAL / "ml_cv_metrics.csv", global_cv_rows); write_csv(FINAL / "ml_oof_predictions.csv", global_oof_rows); write_csv(FINAL / "ml_calibration_metrics.csv", global_calibration_rows); write_csv(FINAL / "ml_threshold_analysis.csv", global_threshold_rows); write_csv(FINAL / "ml_metrics.csv", global_test_rows); json_write(FINAL / "ml_metrics.json", {row["model"]: row for row in global_test_rows}); write_csv(FINAL / "ml_error_analysis.csv", global_error_rows); write_csv(FINAL / "ml_bootstrap_ci.csv", global_bootstrap_rows)
    json_write(FINAL / "ml_model_selection.json", {"primary_candidate": primary_name, "selection_split": "development OOF only", "selection_priority": ["ROC-AUC", "PR-AUC", "balanced accuracy after selected calibration/threshold"], "models": {name: {"calibration": result["calibration"], "threshold": result["threshold"], "oof_metrics": metrics(y_dev, result["selected_oof_probability"], result["threshold"])} for name, result in results.items()}})
    plot_curves(y_test, results); plot_confusions(y_test, results); plot_calibration(y_dev, results); plot_thresholds(results)
    print(json.dumps({"primary_candidate": primary_name, "models": list(results), "test_count": len(y_test), "artifacts": str(FINAL)}, indent=2))


if __name__ == "__main__":
    main()
