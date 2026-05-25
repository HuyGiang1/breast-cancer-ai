#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import roc_auc_score


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CALIB_PATH = PROJECT_ROOT / "models" / "deep_learning" / "calibration_profile.json"


def parse_args():
    parser = argparse.ArgumentParser(description="Export validation-based DL calibration into calibration_profile.json")
    parser.add_argument("--model-name", default="Custom CNN")
    parser.add_argument("--split", default="val", choices=["val", "test"])
    return parser.parse_args()


def load_profile() -> dict:
    if CALIB_PATH.exists():
        return json.loads(CALIB_PATH.read_text(encoding="utf-8"))
    return {"models": {}, "ensemble_weights": {}, "low_quality_models": []}


def save_profile(profile: dict) -> None:
    CALIB_PATH.write_text(json.dumps(profile, indent=2, ensure_ascii=True), encoding="utf-8")


def main():
    args = parse_args()

    from app.services.prediction_dl import dl_prediction_service

    dl_prediction_service.skip_health_check = True
    dl_prediction_service.preload_models(args.model_name)
    model = dl_prediction_service.models[args.model_name]

    split_dir = PROJECT_ROOT / "data" / "cbis_ddsm" / "processed" / "images" / args.split
    y_true = []
    probs = []

    for label, cls in [(0, "benign"), (1, "malignant")]:
        for path in sorted((split_dir / cls).glob("*.png")):
            arr = np.asarray(Image.open(path).convert("RGB"), dtype=np.float32)
            x = dl_prediction_service._preprocess_for_model(args.model_name, arr)
            p = dl_prediction_service._safe_model_probability(model, x, args.model_name)
            y_true.append(label)
            probs.append(p)

    y = np.asarray(y_true, dtype=np.int32)
    p = np.asarray(probs, dtype=np.float32)
    calibrator = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0)
    calibrator.fit(p, y.astype(np.float32))

    profile = load_profile()
    profile.setdefault("models", {})
    entry = profile["models"].setdefault(args.model_name, {})
    entry["reference_probabilities"] = [float(v) for v in np.sort(p)]
    entry["isotonic_x"] = [float(v) for v in calibrator.X_thresholds_]
    entry["isotonic_y"] = [float(v) for v in calibrator.y_thresholds_]
    entry["validation_auc"] = float(roc_auc_score(y, p)) if len(np.unique(y)) > 1 else 0.0
    entry["std_probability"] = float(np.std(p))
    profile["probability_postprocess_mode"] = "empirical"
    save_profile(profile)

    print(
        json.dumps(
            {
                "model_name": args.model_name,
                "split": args.split,
                "count": int(len(p)),
                "std_probability": float(np.std(p)),
                "validation_auc": entry["validation_auc"],
                "reference_count": len(entry["reference_probabilities"]),
                "isotonic_points": len(entry["isotonic_x"]),
            },
            indent=2,
            ensure_ascii=True,
        )
    )


if __name__ == "__main__":
    main()
