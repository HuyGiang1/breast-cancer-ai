"""Checksum-verified runtime for the frozen EfficientNet-B0 full-image candidate."""

from __future__ import annotations

import hashlib
import io
import json
import os
from pathlib import Path
from typing import Any, Mapping

import numpy as np
from PIL import Image

from app.services.final_dl_calibration import apply_platt_calibration, classify_final_dl_raw_probability

PROJECT_ROOT = Path(__file__).resolve().parents[3]
REGISTRY_PATH = PROJECT_ROOT / "models" / "model_registry.example.json"
CALIBRATION_PATH = PROJECT_ROOT / "models" / "calibration" / "efficientnet_b0_platt_final_seed42.json"


class FinalDLUnavailableError(RuntimeError):
    pass


class InvalidFinalDLImageError(ValueError):
    pass


def _tensorflow():
    import tensorflow as tf
    return tf


def preprocess_final_dl_image(image_bytes: bytes):
    """Match the frozen trainer: TF decode RGB, float32 cast, TF resize only."""
    try:
        tf = _tensorflow()
        decoded = tf.io.decode_image(image_bytes, channels=3, expand_animations=False)
        decoded.set_shape([None, None, 3])
        image = tf.image.resize(tf.cast(decoded, tf.float32), (224, 224))
        return tf.expand_dims(image, axis=0)
    except Exception as exc:
        raise InvalidFinalDLImageError("Image cannot be decoded as a valid RGB image.") from exc


class FinalDLRuntimeService:
    def __init__(self, registry_path: Path | None = None, model_path: Path | None = None, calibration_path: Path | None = None):
        self.registry_path = registry_path or REGISTRY_PATH
        self.model_path_override = model_path
        self.calibration_path = calibration_path or CALIBRATION_PATH
        self.model: Any | None = None
        self.calibration: dict[str, Any] | None = None
        self.config: dict[str, Any] = {}
        self.model_sha256: str | None = None
        self.error: str | None = None
        self._load()

    @staticmethod
    def _sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def _registry_entry(self) -> dict[str, Any]:
        entries = json.loads(self.registry_path.read_text(encoding="utf-8"))["models"]
        return next(entry for entry in entries if entry["id"] == "cbis-efficientnetb0-full-v1")

    def _model_path(self, entry: Mapping[str, Any]) -> Path:
        configured = self.model_path_override or os.getenv("FINAL_DL_MODEL_PATH")
        if configured:
            candidate = Path(configured).expanduser()
            return candidate if candidate.is_absolute() else PROJECT_ROOT / candidate
        return PROJECT_ROOT / entry["artifact_filename"]

    def _load(self) -> None:
        try:
            entry = self._registry_entry()
            self.config = entry
            path = self._model_path(entry)
            if not path.is_file():
                raise FinalDLUnavailableError("Final DL model artifact is missing.")
            checksum = self._sha256(path)
            if checksum != entry["sha256"]:
                raise FinalDLUnavailableError("Final DL model checksum mismatch.")
            calibration = json.loads(self.calibration_path.read_text(encoding="utf-8"))
            expected_calibration_sha = entry["calibration"]["sha256"]
            if self._sha256(self.calibration_path) != expected_calibration_sha:
                raise FinalDLUnavailableError("Frozen Platt calibration checksum mismatch.")
            if calibration["model_sha256"] != checksum or calibration["decision_probability_space"] != "raw" or abs(float(calibration["decision_threshold"]) - 0.515) > 1e-12:
                raise FinalDLUnavailableError("Frozen Platt calibration contract mismatch.")
            if calibration["method"] != "platt_logistic_regression" or calibration["classes"] != [0, 1]:
                raise FinalDLUnavailableError("Frozen Platt calibration schema mismatch.")
            model = _tensorflow().keras.models.load_model(path)
            if tuple(model.input_shape[1:]) != (224, 224, 3) or tuple(model.output_shape[1:]) != (1,):
                raise FinalDLUnavailableError("Final DL model shape does not match the frozen contract.")
            self.model, self.calibration, self.model_sha256, self.error = model, calibration, checksum, None
        except Exception as exc:
            self.model, self.calibration, self.model_sha256, self.error = None, None, None, str(exc)

    def get_available_models(self) -> list[str]:
        return ["EfficientNet-B0"] if self.model is not None else []

    def get_model_status(self) -> dict[str, Any]:
        healthy = self.model is not None and self.calibration is not None
        return {
            "model_id": "cbis-efficientnetb0-full-v1", "model_version": "final-candidate",
            "study": "CBIS-DDSM", "model": "EfficientNet-B0 full processed image",
            "artifact_verified": healthy, "sha256": self.model_sha256[:12] if self.model_sha256 else None,
            "input_shape": [224, 224, 3], "representation": "full image",
            "calibration": "Platt" if healthy else None, "decision_threshold": 0.515,
            "decision_probability_space": "raw", "status": "research_demo" if healthy else "unavailable",
            "clinical_use": False, "legacy_models": "development_only", "error": None if healthy else self.error,
        }

    def preload_models(self, model_name: str | None = None) -> dict[str, Any]:
        return self.get_model_status()

    def predict(self, image_bytes: bytes, model_name: str | None = None, include_explanation: bool = False) -> dict[str, Any]:
        if self.model is None or self.calibration is None:
            raise FinalDLUnavailableError(self.error or "Final DL model is unavailable.")
        if model_name and model_name not in {"EfficientNet-B0", "cbis-efficientnetb0-full-v1"}:
            raise ValueError("Only the final EfficientNet-B0 candidate is available.")
        tensor = preprocess_final_dl_image(image_bytes)
        raw_probability = float(np.asarray(self.model(tensor, training=False)).reshape(-1)[0])
        if not 0.0 <= raw_probability <= 1.0:
            raise FinalDLUnavailableError("Final DL model returned an invalid probability.")
        calibrated = apply_platt_calibration(raw_probability, self.calibration)
        is_malignant = bool(classify_final_dl_raw_probability(raw_probability))
        return {
            "model_name": "EfficientNet-B0", "model_id": "cbis-efficientnetb0-full-v1",
            "prediction": int(is_malignant), "diagnosis": "Malignant" if is_malignant else "Benign",
            "probability": calibrated, "raw_probability": raw_probability,
            "calibrated_probability": calibrated, "calibration_mode": "platt_frozen",
            "calibration": "Platt", "decision_threshold": 0.515,
            "decision_probability_space": "raw", "probability_space": "calibrated_display",
            "artifact_verified": True, "status": "research_demo", "risk_band": "High" if calibrated >= .65 else "Medium" if calibrated >= .35 else "Low",
            "risk_band_scope": "research_demo_display_only", "analysis_text": "Research/demo model output. Runtime Grad-CAM is not integrated.",
            "explanation_image": None,
        }


final_dl_runtime_service = FinalDLRuntimeService()
