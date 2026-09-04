#!/usr/bin/env python3
"""Validate frozen final research evidence and generated paper artifacts."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FINAL = ROOT / "experiments" / "final"
PAPER = ROOT / "paper_artifacts"


def rows(path: Path):
    with path.open(newline="", encoding="utf-8") as handle: return list(csv.DictReader(handle))


def require(condition: bool, message: str) -> None:
    if not condition: raise RuntimeError(message)


def main() -> None:
    required = [FINAL / "ml_metrics.csv", FINAL / "dl_metrics.csv", FINAL / "roi_ablation.csv", FINAL / "ml_bootstrap_ci.csv", FINAL / "dl_bootstrap_ci.csv", FINAL / "ml_shap_global.csv", FINAL / "gradcam" / "selection.json", FINAL / "FINAL_RESULTS_SNAPSHOT.json", PAPER / "MANIFEST.json"]
    require(all(path.is_file() for path in required), "Missing required final or paper artifact.")
    ml = rows(FINAL / "ml_metrics.csv"); dl = rows(FINAL / "dl_metrics.csv"); roi = rows(FINAL / "roi_ablation.csv")
    require({row["model"] for row in ml} == {"Logistic Regression", "Random Forest", "XGBoost"}, "Unexpected ML final model names.")
    require({row["Model"] for row in dl} == {"Custom CNN", "ResNet50", "EfficientNet-B0"}, "Unexpected DL final model names.")
    selection = json.loads((FINAL / "ml_model_selection.json").read_text(encoding="utf-8"))
    require(selection["primary_candidate"] == "Logistic Regression", "Primary ML candidate must remain Logistic Regression.")
    require(len(roi) == 2 and roi[0]["Representation"] == "EfficientNet-B0 Full" and roi[1]["Representation"] == "EfficientNet-B0 ROI", "Unexpected ROI ablation rows.")
    verification = json.loads((FINAL / "dataset_verification.json").read_text(encoding="utf-8"))
    require(all(verification[key] == 0 for key in ("train_val_group_overlap", "train_test_group_overlap", "val_test_group_overlap")), "CBIS overlap must remain zero.")
    for path in (FINAL / "ml_metrics.csv", FINAL / "dl_metrics.csv", FINAL / "roi_ablation.csv", FINAL / "ml_bootstrap_ci.csv", FINAL / "dl_bootstrap_ci.csv"):
        for row in rows(path):
            for value in row.values():
                try: require(math.isfinite(float(value)), f"Non-finite numeric value in {path}")
                except ValueError: pass
    manifest = json.loads((PAPER / "MANIFEST.json").read_text(encoding="utf-8"))
    require(len(manifest["artifacts"]) >= 23, "Paper manifest is incomplete.")
    for artifact in manifest["artifacts"]:
        require("experiments/results" not in str(artifact["source"]), "Legacy result path used as final source.")
        require((ROOT / artifact["file"]).is_file(), f"Manifest target missing: {artifact['file']}")
    print("Final research artifacts validated")


if __name__ == "__main__": main()
