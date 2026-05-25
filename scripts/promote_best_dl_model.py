#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DL_DIR = PROJECT_ROOT / "models" / "deep_learning"
CALIB_PATH = DL_DIR / "calibration_profile.json"


def parse_args():
    parser = argparse.ArgumentParser(description="Promote the best DL artifact based on exported summaries")
    parser.add_argument("--dry-run", action="store_true", help="Only print the winner without editing calibration profile")
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def infer_label(summary_path: Path, payload: dict[str, Any]) -> str:
    model_name = str(payload.get("model_name", "")).strip()
    stem = summary_path.stem.lower()
    if model_name:
        if "custom" in model_name.lower():
            return "Custom CNN"
        if "efficient" in model_name.lower():
            return "EfficientNet-B0"
        if "resnet" in model_name.lower():
            return "ResNet50"
        if "imagerf" in model_name.lower():
            return "ImageRF"
    if "custom" in stem:
        return "Custom CNN"
    if "efficient" in stem:
        return "EfficientNet-B0"
    if "resnet" in stem:
        return "ResNet50"
    if "image_rf" in stem:
        return "ImageRF"
    return summary_path.stem


def infer_artifact_path(summary_path: Path, payload: dict[str, Any]) -> str:
    model_path = payload.get("model_path") or payload.get("model")
    if isinstance(model_path, str) and model_path.strip():
        return model_path

    stem = summary_path.stem.removesuffix("_summary")
    keras_path = summary_path.with_name(f"{stem}.keras")
    if keras_path.exists():
        return str(keras_path)

    pkl_path = summary_path.with_name(f"{stem}.pkl")
    if pkl_path.exists():
        return str(pkl_path)

    return str(summary_path)


def infer_metric_name(payload: dict[str, Any]) -> str:
    for key in ("test_tta_auc", "test_auc", "val_auc"):
        if key in payload:
            return key
    return "val_auc"


def infer_validation_accuracy(payload: dict[str, Any]) -> float:
    for key in ("val_accuracy", "val_acc", "validation_accuracy"):
        if key in payload:
            return float(payload.get(key, 0.0))
    return 0.0


def build_record(summary_path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    metric_name = infer_metric_name(payload)
    artifact_path = infer_artifact_path(summary_path, payload)
    artifact_name = Path(artifact_path).name
    return {
        "label": infer_label(summary_path, payload),
        "artifact": artifact_name,
        "model_name": payload.get("model_name") or infer_label(summary_path, payload),
        "summary_path": str(summary_path),
        "model_path": artifact_path,
        "score": float(payload.get(metric_name, 0.0)),
        "val_auc": float(payload.get("val_auc", 0.0)),
        "threshold": float(payload.get("threshold", 0.5)),
        "validation_accuracy": infer_validation_accuracy(payload),
        "spread_factor": float(payload.get("spread_factor", 1.0)),
        "reference_threshold": float(payload.get("reference_threshold", payload.get("threshold", 0.5))),
        "centering_gain": float(payload.get("centering_gain", 1.0)),
        "std_probability": float(payload.get("std_probability", 0.0)),
        "metric_name": metric_name,
    }


def candidate_records() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for summary_path in sorted(DL_DIR.glob("*_summary.json")):
        payload = load_json(summary_path)
        if not isinstance(payload, dict):
            continue
        try:
            records.append(build_record(summary_path, payload))
        except Exception:
            continue
    return records


def choose_best(records: list[dict[str, Any]]) -> dict[str, Any]:
    if not records:
        raise SystemExit("No DL summary files found to compare.")
    return max(records, key=lambda item: (item["score"], item["val_auc"]))


def load_profile() -> dict[str, Any]:
    profile = load_json(CALIB_PATH)
    if isinstance(profile, dict):
        return profile
    return {"models": {}, "ensemble_weights": {}, "low_quality_models": []}


def save_profile(profile: dict[str, Any]) -> None:
    CALIB_PATH.write_text(json.dumps(profile, indent=2, ensure_ascii=True), encoding="utf-8")


def main():
    args = parse_args()
    records = candidate_records()
    best = choose_best(records)

    print("DL candidates:")
    for item in sorted(records, key=lambda row: row["score"], reverse=True):
        print(
            f"- {item['artifact']}: {item['metric_name']}={item['score']:.4f}, "
            f"val_auc={item['val_auc']:.4f}, threshold={item['threshold']:.3f}"
        )

    print(
        f"\nSelected winner: {best['artifact']} "
        f"({best['metric_name']}={best['score']:.4f}, val_auc={best['val_auc']:.4f})"
    )

    if args.dry_run:
        return

    profile = load_profile()
    profile.setdefault("models", {})
    profile["models"][best["label"]] = {
        "validation_accuracy": best["validation_accuracy"],
        "validation_auc": best["val_auc"],
        "threshold": best["threshold"],
        "spread_factor": best["spread_factor"],
        "reference_threshold": best["reference_threshold"],
        "centering_gain": best["centering_gain"],
        "std_probability": best["std_probability"],
    }
    profile["ensemble_weights"] = {best["label"]: 1.0}
    profile["ensemble_threshold"] = best["threshold"]
    profile["low_quality_models"] = [
        name for name in profile.get("low_quality_models", []) if name != best["label"]
    ]
    profile["primary_explain_model"] = best["label"]
    profile["promotion_record"] = {
        "artifact": best["artifact"],
        "model_path": best["model_path"],
        "summary_path": best["summary_path"],
        "metric_name": best["metric_name"],
        "metric_value": best["score"],
        "val_auc": best["val_auc"],
    }
    save_profile(profile)
    print(f"Updated calibration profile: {CALIB_PATH}")


if __name__ == "__main__":
    main()
