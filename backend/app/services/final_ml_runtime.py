"""Checksum-verified runtime contract for the frozen WDBC final model."""

from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any, Mapping

import joblib
import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[3]
REGISTRY_PATH = PROJECT_ROOT / "models" / "model_registry.example.json"

WDBC_FEATURES = (
    "mean radius", "mean texture", "mean perimeter", "mean area", "mean smoothness",
    "mean compactness", "mean concavity", "mean concave points", "mean symmetry", "mean fractal dimension",
    "radius error", "texture error", "perimeter error", "area error", "smoothness error",
    "compactness error", "concavity error", "concave points error", "symmetry error", "fractal dimension error",
    "worst radius", "worst texture", "worst perimeter", "worst area", "worst smoothness",
    "worst compactness", "worst concavity", "worst concave points", "worst symmetry", "worst fractal dimension",
)
API_TO_WDBC_FEATURE = {feature.replace(" ", "_"): feature for feature in WDBC_FEATURES}


class FinalModelUnavailableError(RuntimeError):
    """The frozen final artifact cannot safely serve a prediction."""


def build_wdbc_feature_vector(values: Mapping[str, Any]) -> np.ndarray:
    """Build one raw WDBC row in the frozen feature order without defaults."""
    expected_api_fields = tuple(API_TO_WDBC_FEATURE)
    missing = [name for name in expected_api_fields if name not in values]
    extras = [name for name in values if name not in expected_api_fields]
    if missing or extras:
        details = []
        if missing:
            details.append(f"missing={missing}")
        if extras:
            details.append(f"duplicate_or_unknown={extras}")
        raise ValueError("Invalid WDBC feature payload: " + "; ".join(details))

    vector = []
    for api_name in expected_api_fields:
        try:
            value = float(values[api_name])
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Feature {api_name} must be numeric.") from exc
        if not math.isfinite(value):
            raise ValueError(f"Feature {api_name} must be finite.")
        vector.append(value)

    result = np.asarray(vector, dtype=np.float64).reshape(1, len(WDBC_FEATURES))
    if result.shape != (1, 30):
        raise ValueError("Frozen WDBC input contract requires shape (1, 30).")
    return result


class FinalMLRuntimeService:
    """Serve only the approved WDBC Logistic Regression research/demo candidate."""

    def __init__(self, registry_path: Path | None = None, model_path: Path | None = None):
        self.registry_path = registry_path or REGISTRY_PATH
        self.model_path_override = model_path
        self.model: Any | None = None
        self.config: dict[str, Any] = {}
        self.health_error: str | None = None
        self.artifact_sha256: str | None = None
        self._load_final_model()

    def _load_final_model(self) -> None:
        try:
            entry = self._registry_entry()
            self.config = entry
            artifact_path = self._artifact_path(entry)
            if not artifact_path.is_file():
                raise FinalModelUnavailableError("Final ML artifact is missing.")

            actual_sha = self._sha256(artifact_path)
            expected_sha = str(entry["sha256"])
            if actual_sha != expected_sha:
                raise FinalModelUnavailableError("Final ML artifact checksum mismatch.")

            model = joblib.load(artifact_path)
            self._validate_pipeline(model, entry)
            self.model = model
            self.artifact_sha256 = actual_sha
            self.health_error = None
        except Exception as exc:
            self.model = None
            self.artifact_sha256 = None
            self.health_error = str(exc)

    def _registry_entry(self) -> dict[str, Any]:
        with self.registry_path.open(encoding="utf-8") as handle:
            payload = json.load(handle)
        for item in payload.get("models", []):
            if item.get("id") == "wdbc-logistic-regression-v1":
                return item
        raise FinalModelUnavailableError("Final WDBC registry entry is missing.")

    def _artifact_path(self, entry: Mapping[str, Any]) -> Path:
        configured = self.model_path_override or os.getenv("FINAL_ML_MODEL_PATH")
        if configured:
            path = Path(configured).expanduser()
            return path if path.is_absolute() else PROJECT_ROOT / path
        return PROJECT_ROOT / str(entry["artifact_filename"])

    @staticmethod
    def _sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    @staticmethod
    def _validate_pipeline(model: Any, entry: Mapping[str, Any]) -> None:
        steps = getattr(model, "named_steps", {})
        if list(steps) != ["scaler", "lr"]:
            raise FinalModelUnavailableError("Final ML artifact is not the expected scaler/lr pipeline.")
        if type(steps["scaler"]).__name__ != "StandardScaler" or type(steps["lr"]).__name__ != "LogisticRegression":
            raise FinalModelUnavailableError("Final ML pipeline step types do not match the frozen contract.")
        classes = np.asarray(getattr(model, "classes_", []), dtype=int)
        if not np.array_equal(classes, np.array([0, 1])):
            raise FinalModelUnavailableError("Final ML class order is not [0, 1].")
        feature_count = int(getattr(model, "n_features_in_", 0))
        if feature_count != int(entry["input"]["feature_count"]):
            raise FinalModelUnavailableError("Final ML feature count is not 30.")

    def get_available_models(self) -> list[str]:
        return ["Logistic Regression"] if self.model is not None else []

    def get_model_status(self) -> dict[str, Any]:
        healthy = self.model is not None
        return {
            "model_id": self.config.get("id", "wdbc-logistic-regression-v1"),
            "model_version": "v1",
            "study": "WDBC",
            "model": "Logistic Regression",
            "framework": "scikit-learn",
            "artifact_verified": healthy,
            "sha256": self.artifact_sha256[:12] if self.artifact_sha256 else None,
            "feature_count": 30,
            "positive_class": "malignant",
            "probability_space": "raw",
            "calibration": "none",
            "decision_threshold": 0.36,
            "status": "research_demo" if healthy else "unavailable",
            "clinical_use": False,
            "error": None if healthy else self.health_error,
        }

    def get_model_benchmarks(self) -> dict[str, Any]:
        metrics_path = PROJECT_ROOT / "experiments" / "final" / "ml_metrics.json"
        try:
            with metrics_path.open(encoding="utf-8") as handle:
                metrics = json.load(handle)["Logistic Regression"]
            return {"Logistic Regression": {**metrics, "status": self.get_model_status()["status"]}}
        except (OSError, KeyError, json.JSONDecodeError):
            return {"Logistic Regression": {"status": self.get_model_status()["status"]}}

    @staticmethod
    def _risk_band_from_probability(probability: float) -> str:
        if probability < 0.35:
            return "Low"
        if probability < 0.65:
            return "Medium"
        return "High"

    def _load_reference_data(self) -> dict[str, Any]:
        ref_path = PROJECT_ROOT / "experiments" / "final" / "wdbc_feature_reference.json"
        if not ref_path.is_file():
            ref_path = PROJECT_ROOT / "frontend" / "content" / "wdbc_feature_reference.json"
        if ref_path.is_file():
            try:
                with ref_path.open(encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def predict(self, request_data: Any, model_name: str | None = None) -> dict[str, Any]:
        if self.model is None:
            raise FinalModelUnavailableError(self.health_error or "Final ML model is unavailable.")
        if model_name and model_name not in {"Logistic Regression", "wdbc-logistic-regression-v1"}:
            raise ValueError("Only the final Logistic Regression candidate is available.")

        values = request_data.model_dump() if hasattr(request_data, "model_dump") else request_data.dict()
        raw_input = build_wdbc_feature_vector(values)
        probabilities = np.asarray(self.model.predict_proba(raw_input)[0], dtype=float)
        probability = float(probabilities[1])
        if not 0.0 <= probability <= 1.0:
            raise FinalModelUnavailableError("Final ML model returned an invalid probability.")

        threshold = 0.36
        is_malignant = probability >= threshold

        top_features: list[dict[str, Any]] = []
        all_features: list[dict[str, Any]] = []
        input_quality: dict[str, Any] = {
            "within_common_range_count": 0,
            "unusual_count": 0,
            "extreme_count": 0,
            "outside_observed_count": 0,
            "outliers": [],
        }
        intercept: float | None = None
        total_logit: float | None = None

        if hasattr(self.model, "named_steps") and "scaler" in self.model.named_steps and "lr" in self.model.named_steps:
            scaler = self.model.named_steps["scaler"]
            lr = self.model.named_steps["lr"]
            raw_row = raw_input[0]
            std_row = (raw_row - scaler.mean_) / scaler.scale_
            coefs = lr.coef_[0]
            contribs = std_row * coefs
            intercept = float(lr.intercept_[0])
            total_logit = float(intercept + np.sum(contribs))

            ref_map = self._load_reference_data().get("features", {})
            api_names = list(API_TO_WDBC_FEATURE.keys())

            for i, api_name in enumerate(api_names):
                raw_val = float(raw_row[i])
                std_val = float(std_row[i])
                coef_val = float(coefs[i])
                log_odds = float(contribs[i])
                direction = "toward_malignant" if log_odds > 0 else "toward_benign"

                feat_ref = ref_map.get(api_name, {})
                display_name = feat_ref.get("display_name", api_name.replace("_", " ").title())
                group = feat_ref.get("group", "Other")
                description = feat_ref.get("description", "")
                min_val = feat_ref.get("min")
                p01 = feat_ref.get("p01")
                p05 = feat_ref.get("p05")
                p95 = feat_ref.get("p95")
                p99 = feat_ref.get("p99")
                max_val = feat_ref.get("max")

                # Reference state check against WDBC development cohort
                if min_val is not None and max_val is not None and (raw_val < min_val or raw_val > max_val):
                    ref_state = "outside_observed"
                    input_quality["outside_observed_count"] += 1
                    input_quality["outliers"].append({
                        "feature": api_name,
                        "display_name": display_name,
                        "raw_value": raw_val,
                        "state": "outside_observed",
                        "min": min_val,
                        "max": max_val,
                    })
                elif p01 is not None and p99 is not None and (raw_val < p01 or raw_val > p99):
                    ref_state = "extreme"
                    input_quality["extreme_count"] += 1
                    input_quality["outliers"].append({
                        "feature": api_name,
                        "display_name": display_name,
                        "raw_value": raw_val,
                        "state": "extreme",
                        "p01": p01,
                        "p99": p99,
                    })
                elif p05 is not None and p95 is not None and (raw_val < p05 or raw_val > p95):
                    ref_state = "unusual"
                    input_quality["unusual_count"] += 1
                else:
                    ref_state = "within_reference"
                    input_quality["within_common_range_count"] += 1

                item = {
                    "feature": api_name,
                    "display_name": display_name,
                    "group": group,
                    "description": description,
                    "raw_value": raw_val,
                    "standardized_value": round(std_val, 4),
                    "coefficient": round(coef_val, 4),
                    "log_odds_contribution": round(log_odds, 4),
                    "direction": direction,
                    "reference_state": ref_state,
                    "reference_p05": p05,
                    "reference_p95": p95,
                    "reference_min": min_val,
                    "reference_max": max_val,
                }
                all_features.append(item)

            top_features = sorted(all_features, key=lambda x: abs(x["log_odds_contribution"]), reverse=True)

        return {
            "model_name": "Logistic Regression",
            "model_id": "wdbc-logistic-regression-v1",
            "prediction": int(is_malignant),
            "diagnosis": "Malignant" if is_malignant else "Benign",
            "probability": probability,
            "raw_probability": probability,
            "calibration_mode": "none_raw",
            "decision_threshold": threshold,
            "probability_space": "raw",
            "risk_band": self._risk_band_from_probability(probability),
            "risk_band_scope": "research_demo_display_only",
            "analysis_text": (
                f"Frozen Logistic Regression result: raw probability {probability * 100:.1f}%, "
                f"classification '{'Malignant' if is_malignant else 'Benign'}' at cutoff {threshold}."
            ),
            "top_features": top_features,
            "all_features": all_features,
            "input_quality": input_quality,
            "intercept": intercept,
            "total_logit": total_logit,
        }


final_ml_runtime_service = FinalMLRuntimeService()
