#!/usr/bin/env python3

from __future__ import annotations

import json
from pathlib import Path

import numpy as np


def quantiles(values: np.ndarray) -> list[float]:
    if values.size == 0:
        return []
    return [float(v) for v in np.quantile(values, [0.01, 0.1, 0.25, 0.5, 0.75, 0.9, 0.99])]


def summarize(values: np.ndarray) -> dict:
    return {
        "count": int(values.size),
        "mean": float(np.mean(values)) if values.size else 0.0,
        "std": float(np.std(values)) if values.size else 0.0,
        "quantiles": quantiles(values),
    }


def main() -> None:
    from app.services.prediction_dl import dl_prediction_service

    dl_prediction_service.preload_models("Custom CNN")
    model_name = "Custom CNN"
    model = dl_prediction_service.models[model_name]

    def run_split(split: str) -> dict:
        split_dir = Path("data/cbis_ddsm/processed/images") / split
        y_true = []
        raw_probs = []
        calibrated_probs = []

        for label, cls in [(0, "benign"), (1, "malignant")]:
            for path in sorted((split_dir / cls).glob("*.png")):
                from PIL import Image

                img = Image.open(path).convert("RGB").resize(dl_prediction_service.target_size)
                arr = np.asarray(img, dtype=np.float32)
                x = dl_prediction_service._preprocess_for_model(model_name, arr)
                raw_p = dl_prediction_service._safe_model_probability(model, x, model_name)
                cal_p = dl_prediction_service._postprocess_probability(model_name, raw_p)
                y_true.append(label)
                raw_probs.append(raw_p)
                calibrated_probs.append(cal_p)

        y_true_arr = np.asarray(y_true, dtype=np.int32)
        raw_arr = np.asarray(raw_probs, dtype=np.float32)
        cal_arr = np.asarray(calibrated_probs, dtype=np.float32)

        return {
            "raw_all": summarize(raw_arr),
            "calibrated_all": summarize(cal_arr),
            "raw_benign": summarize(raw_arr[y_true_arr == 0]),
            "raw_malignant": summarize(raw_arr[y_true_arr == 1]),
            "calibrated_benign": summarize(cal_arr[y_true_arr == 0]),
            "calibrated_malignant": summarize(cal_arr[y_true_arr == 1]),
        }

    report = {
        "model_path": str(dl_prediction_service.model_paths.get(model_name)),
        "probability_postprocess_mode": dl_prediction_service.probability_postprocess_mode,
        "validation": run_split("val"),
        "test": run_split("test"),
    }
    print(json.dumps(report, indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
