#!/usr/bin/env python3
"""Create final DL baseline tables and figures from completed run artifacts."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import auc, precision_recall_curve, roc_curve


ROOT = Path(__file__).resolve().parent.parent
FINAL = ROOT / "experiments" / "final"
RUNS = {
    "Custom CNN": FINAL / "runs" / "custom_cnn_full",
    "ResNet50": FINAL / "runs" / "resnet50_full",
    "EfficientNet-B0": FINAL / "runs" / "efficientnet_b0_full",
}
METRIC_COLUMNS = ["accuracy", "precision", "sensitivity", "specificity", "f1", "balanced_accuracy", "roc_auc", "pr_auc", "brier_score", "tn", "fp", "fn", "tp"]


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def predictions(run_dir: Path) -> tuple[np.ndarray, np.ndarray]:
    with (run_dir / "test_predictions.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    return np.array([int(row["label"]) for row in rows]), np.array([float(row["malignant_probability"]) for row in rows])


def main() -> int:
    figures = FINAL / "figures"
    figures.mkdir(parents=True, exist_ok=True)
    rows, prediction_data = [], {}
    for name, run_dir in RUNS.items():
        metrics = load_json(run_dir / "metrics.json")["test"]
        rows.append({"Model": name, **{key: metrics[key] for key in METRIC_COLUMNS}})
        prediction_data[name] = predictions(run_dir)

    with (FINAL / "dl_metrics.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["Model", "Accuracy", "Precision", "Sensitivity", "Specificity", "F1", "Balanced Accuracy", "ROC-AUC", "PR-AUC", "Brier", "TN", "FP", "FN", "TP"])
        writer.writeheader()
        for row in rows:
            writer.writerow({
                "Model": row["Model"], "Accuracy": row["accuracy"], "Precision": row["precision"], "Sensitivity": row["sensitivity"], "Specificity": row["specificity"], "F1": row["f1"], "Balanced Accuracy": row["balanced_accuracy"], "ROC-AUC": row["roc_auc"], "PR-AUC": row["pr_auc"], "Brier": row["brier_score"], "TN": row["tn"], "FP": row["fp"], "FN": row["fn"], "TP": row["tp"],
            })

    plt.figure(figsize=(7, 5))
    for name, (labels, probabilities) in prediction_data.items():
        fpr, tpr, _ = roc_curve(labels, probabilities)
        plt.plot(fpr, tpr, label=f"{name} (AUC={auc(fpr, tpr):.3f})")
    plt.plot([0, 1], [0, 1], "k--", linewidth=1)
    plt.xlabel("False positive rate"); plt.ylabel("True positive rate"); plt.legend(); plt.tight_layout()
    plt.savefig(figures / "dl_roc_comparison.png", dpi=160); plt.close()

    plt.figure(figsize=(7, 5))
    for name, (labels, probabilities) in prediction_data.items():
        precision, recall, _ = precision_recall_curve(labels, probabilities)
        plt.plot(recall, precision, label=name)
    plt.xlabel("Recall"); plt.ylabel("Precision"); plt.legend(); plt.tight_layout()
    plt.savefig(figures / "dl_pr_comparison.png", dpi=160); plt.close()

    fig, axes = plt.subplots(1, 3, figsize=(10, 3.2))
    for axis, row in zip(axes, rows):
        matrix = np.array([[row["tn"], row["fp"]], [row["fn"], row["tp"]]])
        image = axis.imshow(matrix, cmap="Blues")
        axis.set_title(row["Model"]); axis.set_xticks([0, 1], ["Benign", "Malignant"]); axis.set_yticks([0, 1], ["Benign", "Malignant"])
        for i in range(2):
            for j in range(2): axis.text(j, i, matrix[i, j], ha="center", va="center")
    fig.colorbar(image, ax=axes.ravel().tolist(), shrink=0.8); fig.tight_layout()
    fig.savefig(figures / "dl_confusion_matrices.png", dpi=160); plt.close(fig)

    plt.figure(figsize=(7, 5))
    for name, run_dir in RUNS.items():
        with (run_dir / "history.csv").open(newline="", encoding="utf-8") as handle: history = list(csv.DictReader(handle))
        if history and "val_auc" in history[0]: plt.plot([int(row["epoch"]) for row in history], [float(row["val_auc"]) for row in history], label=name)
    plt.xlabel("Epoch"); plt.ylabel("Validation ROC-AUC"); plt.legend(); plt.tight_layout()
    plt.savefig(figures / "dl_training_curves.png", dpi=160); plt.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
