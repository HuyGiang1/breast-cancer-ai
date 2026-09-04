#!/usr/bin/env python3
"""Write validation-first EfficientNet full-image versus ROI ablation outputs."""

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
    "EfficientNet-B0 Full": FINAL / "runs" / "efficientnet_b0_full",
    "EfficientNet-B0 ROI": FINAL / "runs" / "efficientnet_b0_roi",
}
METRICS = ("roc_auc", "pr_auc", "sensitivity", "specificity", "balanced_accuracy", "brier_score")


def load_predictions(path: Path) -> tuple[np.ndarray, np.ndarray]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    return np.array([int(row["label"]) for row in rows]), np.array([float(row["malignant_probability"]) for row in rows])


def main() -> int:
    data = {name: json.loads((directory / "metrics.json").read_text(encoding="utf-8")) for name, directory in RUNS.items()}
    full = data["EfficientNet-B0 Full"]
    fields = ["Representation", *[f"Validation_{name}" for name in ("ROC_AUC", "PR_AUC", "Sensitivity", "Specificity", "Balanced_Accuracy", "Brier")], *[f"Test_{name}" for name in ("ROC_AUC", "PR_AUC", "Sensitivity", "Specificity", "Balanced_Accuracy", "Brier", "FN")]]
    mapping = {"ROC_AUC": "roc_auc", "PR_AUC": "pr_auc", "Sensitivity": "sensitivity", "Specificity": "specificity", "Balanced_Accuracy": "balanced_accuracy", "Brier": "brier_score"}
    with (FINAL / "roi_ablation.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader()
        for name, metrics in data.items():
            row = {"Representation": name}
            for display, key in mapping.items(): row[f"Validation_{display}"] = metrics["validation"][key]; row[f"Test_{display}"] = metrics["test"][key]
            row["Test_FN"] = metrics["test"]["fn"]
            writer.writerow(row)

    figures = FINAL / "figures"; figures.mkdir(exist_ok=True)
    for kind, output in (("roc", "efficientnet_full_vs_roi_roc.png"), ("pr", "efficientnet_full_vs_roi_pr.png")):
        plt.figure(figsize=(7, 5))
        for name, directory in RUNS.items():
            labels, probabilities = load_predictions(directory / "test_predictions.csv")
            if kind == "roc":
                x, y, _ = roc_curve(labels, probabilities); label = f"{name} (AUC={auc(x, y):.3f})"; plt.xlabel("False positive rate"); plt.ylabel("True positive rate")
            else:
                y, x, _ = precision_recall_curve(labels, probabilities); label = name; plt.xlabel("Recall"); plt.ylabel("Precision")
            plt.plot(x, y, label=label)
        plt.legend(); plt.tight_layout(); plt.savefig(figures / output, dpi=160); plt.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
