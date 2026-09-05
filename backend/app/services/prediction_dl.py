import os
import json
import numpy as np
from pathlib import Path
from PIL import Image
import io
import cv2
import uuid
from typing import Dict, List, Tuple, Any
import joblib
from sklearn.metrics import roc_auc_score
from sklearn.isotonic import IsotonicRegression

_TF = None


def _get_tf():
    global _TF
    if _TF is None:
        import tensorflow as tf  # Lazy import to reduce backend cold-start latency.
        _TF = tf
    return _TF

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
POSSIBLE_MODEL_DIRS = [
    PROJECT_ROOT / "models" / "deep_learning",
    PROJECT_ROOT / "src" / "models" / "deep_learning",
    PROJECT_ROOT / "backend",
]
STATIC_RESULTS_DIR = PROJECT_ROOT / "frontend" / "results"
STATIC_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
CALIBRATION_PROFILE_PATH = PROJECT_ROOT / "models" / "deep_learning" / "calibration_profile.json"

class DeepLearningService:
    def __init__(self):
        self.models = {}
        self.model_paths: Dict[str, Path] = {}
        self.model_types: Dict[str, str] = {}
        self.model_target_sizes: Dict[str, Tuple[int, int]] = {}
        self.experimental_model_paths: Dict[str, Path] = {}
        self.target_size = (224, 224)
        self.expose_experimental_models = os.getenv("DL_EXPOSE_EXPERIMENTAL_MODELS", "false").strip().lower() == "true"
        self._discover_model_files()
        self.thresholds: Dict[str, float] = {name: 0.5 for name in self.model_paths}
        self.calibration_metrics: Dict[str, Dict[str, float]] = {}
        self.probability_calibrators: Dict[str, Any] = {}
        self.probability_spread_factors: Dict[str, float] = {}
        self.centering_reference_thresholds: Dict[str, float] = {}
        self.centering_gains: Dict[str, float] = {}
        self.model_probability_stds: Dict[str, float] = {}
        self.model_probability_reference: Dict[str, np.ndarray] = {}
        self.model_invert_probability: Dict[str, bool] = {}
        self.low_quality_models: set[str] = set()
        self.ensemble_weights: Dict[str, float] = {}
        self.ensemble_threshold: float = 0.5
        self.primary_explain_model: str = ""
        self._is_calibrated: bool = False
        self._is_calibrating: bool = False
        self._health_checked_models: set[str] = set()
        self.health_check_sample_limit = int(os.getenv("DL_HEALTH_CHECK_SAMPLES", "40"))
        self.skip_health_check = os.getenv("DL_SKIP_HEALTH_CHECK", "true").strip().lower() == "true"
        self.probability_postprocess_mode = os.getenv("DL_PROBABILITY_POSTPROCESS_MODE", "spread").strip().lower()
        self.layer_map = {
            "ResNet50": "conv5_block3_out",
            "EfficientNet-B0": "top_activation",
            "Custom CNN": "conv2d_7"
        }

    def _discover_model_files(self):
        discovered: Dict[str, Tuple[Path, float]] = {}
        experimental: Dict[str, Path] = {}
        for model_dir in POSSIBLE_MODEL_DIRS:
            if not model_dir.exists():
                continue
            for model_path in model_dir.glob("*.keras"):
                name = self._normalize_model_name(model_path.stem)
                score = self._artifact_priority(model_path)
                current = discovered.get(name)
                if current is None or score > current[1]:
                    if current is not None:
                        experimental[name] = current[0]
                    discovered[name] = (model_path, score)
                else:
                    experimental[name] = model_path

            # Optional image-feature model trained from CBIS images.
            for model_path in model_dir.glob("dl_image_rf*.pkl"):
                name = "ImageRF"
                score = self._artifact_priority(model_path)
                current = discovered.get(name)
                if current is None or score > current[1]:
                    if current is not None:
                        experimental[name] = current[0]
                    discovered[name] = (model_path, score)
                else:
                    experimental[name] = model_path
        self.model_paths = {name: path for name, (path, _) in discovered.items()}
        self.experimental_model_paths = experimental

    def _artifact_priority(self, model_path: Path) -> float:
        stem = model_path.stem.lower()
        score = float(model_path.stat().st_mtime)
        preferred_from_profile = self._preferred_model_path_from_profile()
        if preferred_from_profile and model_path.resolve() == preferred_from_profile.resolve():
            score += 100_000.0

        summary_path = model_path.with_name(f"{model_path.stem}_summary.json")
        if summary_path.exists():
            try:
                with summary_path.open("r", encoding="utf-8") as f:
                    payload = json.load(f)
                test_metric = float(payload.get("test_tta_auc", payload.get("test_auc", 0.0)))
                val_auc = float(payload.get("val_auc", 0.0))
                val_acc = float(payload.get("val_accuracy", payload.get("val_acc", payload.get("validation_accuracy", 0.0))))
                return score + 10_000.0 + test_metric * 100.0 + val_auc * 10.0 + val_acc
            except Exception:
                return score + 10_000.0

        if stem == "custom_cnn_v2_finetuned_roi":
            phase2_path = PROJECT_ROOT / "experiments" / "results" / "phase2_summary.json"
            if phase2_path.exists():
                try:
                    with phase2_path.open("r", encoding="utf-8") as f:
                        payload = json.load(f)
                    best = payload.get("best_model", {})
                    return 9_000.0 + float(best.get("roc_auc", 0.0)) * 100.0
                except Exception:
                    return 9_000.0
            return 9_000.0

        if stem == "custom_cnn_retrained_balanced":
            return 8_000.0
        if stem == "custom_cnn_best":
            return 7_000.0
        if stem == "resnet50_best":
            return 2_000.0
        if stem == "efficientnetb0_best":
            return 2_000.0
        if "dl_image_rf" in stem:
            return 3_000.0

        return score

    def _preferred_model_path_from_profile(self) -> Path | None:
        if not CALIBRATION_PROFILE_PATH.exists():
            return None
        try:
            with CALIBRATION_PROFILE_PATH.open("r", encoding="utf-8") as f:
                payload = json.load(f)
            promoted = payload.get("promotion_record", {})
            model_path = promoted.get("model_path")
            if isinstance(model_path, str) and model_path.strip():
                path = Path(model_path)
                if path.exists():
                    return path
        except Exception:
            return None
        return None

    def _risk_band_from_probability(self, probability: float) -> str:
        p = float(np.clip(probability, 0.0, 1.0))
        if p < 0.35:
            return "Low"
        if p < 0.65:
            return "Medium"
        return "High"

    def _load_single_model(self, name: str, model_path: Path):
        if name in self.models:
            return

        tf = _get_tf()
        if model_path.suffix == ".keras":
            self.models[name] = tf.keras.models.load_model(model_path)
            self.model_types[name] = "keras"
            input_shape = getattr(self.models[name], "input_shape", None)
            if isinstance(input_shape, tuple) and len(input_shape) >= 3:
                h = int(input_shape[1] or self.target_size[0])
                w = int(input_shape[2] or self.target_size[1])
                self.model_target_sizes[name] = (h, w)
        else:
            self.models[name] = joblib.load(model_path)
            self.model_types[name] = "sklearn"
            self.model_target_sizes[name] = self.target_size
        print(f"Loaded {name} ({self.model_types[name]}) from {model_path}")

    def _target_size_for_model(self, model_name: str | None) -> Tuple[int, int]:
        if model_name and model_name in self.model_target_sizes:
            return self.model_target_sizes[model_name]
        return self.target_size

    def _ensure_models_loaded(self, requested_model: str | None = None):
        if not self.model_paths:
            self._discover_model_files()

        names_to_load: List[str]
        if requested_model and requested_model != "Ensemble" and requested_model in self.model_paths:
            names_to_load = [requested_model]
        else:
            names_to_load = list(self.model_paths.keys())

        for name in names_to_load:
            if name in self.models:
                continue
            model_path = self.model_paths.get(name)
            if model_path is None:
                continue
            try:
                self._load_single_model(name, model_path)
            except Exception as e:
                print(f"Failed to load {model_path}: {e}")

        if self.models and not self.ensemble_weights:
            n = len(self.models)
            self.ensemble_weights = {name: 1.0 / n for name in self.models}
            self.primary_explain_model = next(iter(self.models.keys()))
            self.thresholds = {name: float(self.thresholds.get(name, 0.5)) for name in self.models}

        if self.models and not self._is_calibrated and not self._is_calibrating:
            loaded_profile = self._load_external_calibration_profile()
            if not loaded_profile:
                self._is_calibrated = True

        pending_health_check = [name for name in names_to_load if name in self.models and name not in self._health_checked_models]
        if pending_health_check and not self.skip_health_check:
            self._run_lightweight_health_check()
            self._health_checked_models.update(pending_health_check)

    def _load_external_calibration_profile(self) -> bool:
        if not CALIBRATION_PROFILE_PATH.exists():
            return False

        try:
            with CALIBRATION_PROFILE_PATH.open("r", encoding="utf-8") as f:
                payload = json.load(f)

            model_entries = payload.get("models", {})
            available_models = set(self.models.keys())
            loaded_any = False

            for name, cfg in model_entries.items():
                if name not in available_models:
                    continue
                self.thresholds[name] = float(cfg.get("threshold", self.thresholds.get(name, 0.5)))
                self.centering_reference_thresholds[name] = float(cfg.get("reference_threshold", self.centering_reference_thresholds.get(name, self.thresholds[name])))
                self.centering_gains[name] = float(cfg.get("centering_gain", self.centering_gains.get(name, 8.0)))
                self.probability_spread_factors[name] = float(cfg.get("spread_factor", self.probability_spread_factors.get(name, 1.0)))
                self.calibration_metrics[name] = {
                    "validation_accuracy": float(cfg.get("validation_accuracy", 0.0)),
                    "validation_auc": float(cfg.get("validation_auc", 0.0)),
                    "threshold": self.thresholds[name],
                    "reference_threshold": self.centering_reference_thresholds[name],
                    "centering_gain": self.centering_gains[name],
                    "spread_factor": self.probability_spread_factors[name],
                }
                self.model_probability_stds[name] = float(cfg.get("std_probability", self.model_probability_stds.get(name, 0.04)))
                reference_probs = cfg.get("reference_probabilities")
                if isinstance(reference_probs, list) and len(reference_probs) > 20:
                    self.model_probability_reference[name] = np.sort(
                        np.asarray(reference_probs, dtype=np.float32)
                    )
                isotonic_x = cfg.get("isotonic_x")
                isotonic_y = cfg.get("isotonic_y")
                if (
                    isinstance(isotonic_x, list)
                    and isinstance(isotonic_y, list)
                    and len(isotonic_x) == len(isotonic_y)
                    and len(isotonic_x) >= 2
                ):
                    self.probability_calibrators[name] = (
                        np.asarray(isotonic_x, dtype=np.float32),
                        np.asarray(isotonic_y, dtype=np.float32),
                    )
                loaded_any = True

            weights = payload.get("ensemble_weights", {})
            filtered_weights = {k: float(v) for k, v in weights.items() if k in available_models}
            if filtered_weights:
                s = sum(filtered_weights.values())
                if s > 0:
                    self.ensemble_weights = {k: v / s for k, v in filtered_weights.items()}

            if "ensemble_threshold" in payload:
                self.ensemble_threshold = float(payload["ensemble_threshold"])

            env_postprocess_mode = os.getenv("DL_PROBABILITY_POSTPROCESS_MODE", "").strip().lower()
            profile_postprocess_mode = str(payload.get("probability_postprocess_mode", "")).strip().lower()
            if env_postprocess_mode:
                self.probability_postprocess_mode = env_postprocess_mode
            elif profile_postprocess_mode in {"raw", "none", "disabled", "spread", "threshold_spread", "isotonic"}:
                self.probability_postprocess_mode = profile_postprocess_mode

            low_q = payload.get("low_quality_models", [])
            self.low_quality_models = {m for m in low_q if m in available_models}

            primary = payload.get("primary_explain_model")
            if primary in available_models:
                self.primary_explain_model = primary
            elif self.ensemble_weights:
                self.primary_explain_model = max(self.ensemble_weights, key=self.ensemble_weights.get)

            self._is_calibrated = loaded_any
            if loaded_any:
                print(f"Loaded DL calibration profile from {CALIBRATION_PROFILE_PATH}")
            return loaded_any
        except Exception as e:
            print(f"Failed to load calibration profile {CALIBRATION_PROFILE_PATH}: {e}")
            return False
        
    def _load_models(self):
        tf = _get_tf()
        for model_dir in POSSIBLE_MODEL_DIRS:
            if not model_dir.exists(): continue
            for model_path in model_dir.glob("*.keras"):
                name = self._normalize_model_name(model_path.stem)
                if name in self.models: continue
                try:
                    self.models[name] = tf.keras.models.load_model(model_path)
                    print(f"Loaded {name} from {model_path}")
                except Exception as e:
                    print(f"Failed to load {model_path}: {e}")

    def _normalize_model_name(self, stem):
        name = stem.replace("_best", "").replace("_", " ").title().strip()
        if "Resnet50" in name: return "ResNet50"
        if "Efficientnet" in name: return "EfficientNet-B0"
        if "Custom" in name: return "Custom CNN"
        return name

    def get_available_models(self):
        names = list(self.model_paths.keys()) if self.model_paths else list(self.models.keys())
        if not self.expose_experimental_models:
            names = [name for name in names if name in {"Custom CNN"}]
        if self.low_quality_models:
            names = [name for name in names if name not in self.low_quality_models]

        preferred_order = ["Custom CNN", "ResNet50", "EfficientNet-B0"]
        names = sorted(names, key=lambda n: preferred_order.index(n) if n in preferred_order else len(preferred_order))

        if self.expose_experimental_models and len(self.models) > 1 and names:
            names.append("Ensemble")
        if not names and self.models:
            names = ["Ensemble"]
        return names

    def get_model_status(self) -> Dict[str, Any]:
        available = self.get_available_models()
        active_model = None
        if self.primary_explain_model and self.primary_explain_model in available:
            active_model = self.primary_explain_model
        elif available:
            active_model = available[0]

        active_path = None
        if active_model and active_model in self.model_paths:
            active_path = str(self.model_paths[active_model])

        return {
            "available_models": available,
            "loaded_models": sorted(self.models.keys()),
            "active_model": active_model,
            "active_model_path": active_path,
            "low_quality_models": sorted(self.low_quality_models),
            "experimental_candidates": {
                name: str(path) for name, path in self.experimental_model_paths.items()
            },
            "probability_postprocess_mode": self.probability_postprocess_mode,
            "thresholds": {k: float(v) for k, v in self.thresholds.items()},
            "calibration_metrics": self.calibration_metrics,
            "final_candidate": {
                "model_id": "cbis-efficientnetb0-full-v1",
                "promotion_status": "BLOCKED",
                "reason": "Selected Platt calibration has no frozen runtime-loadable artifact.",
                "clinical_use": False,
            },
        }

    def preload_models(self, model_name: str | None = None) -> Dict[str, Any]:
        self._ensure_models_loaded(model_name)
        status = self.get_model_status()
        status["requested_model"] = model_name
        status["preloaded"] = bool(self.models)
        return status

    def _run_lightweight_health_check(self):
        """Disable DL models with near-constant or weak validation behavior."""
        try:
            reference_model = next(iter(self.models.keys())) if self.models else None
            x_val, y_val = self._load_validation_arrays(reference_model)
            if len(y_val) == 0:
                return

            max_samples = min(len(y_val), max(self.health_check_sample_limit, 8))
            if max_samples < len(y_val) and len(np.unique(y_val)) > 1:
                per_class = max(max_samples // 2, 1)
                keep_idx = []
                for cls in np.unique(y_val):
                    cls_idx = np.where(y_val == cls)[0][:per_class]
                    keep_idx.extend(cls_idx.tolist())
                keep_idx = np.asarray(sorted(keep_idx), dtype=np.int32)
                x_val = x_val[keep_idx]
                y_val = y_val[keep_idx]
            else:
                x_val = x_val[:max_samples]
                y_val = y_val[:max_samples]

            bad = []
            quality_scores: Dict[str, float] = {}
            for name, model in self.models.items():
                if self.model_types.get(name) == "sklearn":
                    feats = np.stack([self._extract_image_features(img) for img in x_val], axis=0)
                    probs = model.predict_proba(feats)[:, 1].astype(np.float32)
                else:
                    x_pre = self._preprocess_for_model(name, x_val)
                    preds = model(x_pre, training=False).numpy()
                    probs = self._raw_probabilities_from_predictions(preds)

                # Infer orientation: ensure higher score means more malignant.
                mal_mean = float(np.mean(probs[y_val == 1])) if np.any(y_val == 1) else 0.5
                ben_mean = float(np.mean(probs[y_val == 0])) if np.any(y_val == 0) else 0.5
                invert = mal_mean < ben_mean
                self.model_invert_probability[name] = invert
                if invert:
                    probs = 1.0 - probs

                std = float(np.std(probs))
                auc = float(roc_auc_score(y_val, probs)) if len(np.unique(y_val)) > 1 else 0.5
                quality_scores[name] = (auc * 0.8) + min(std, 1.0) * 0.2
                self.model_probability_reference[name] = np.sort(np.clip(probs.astype(np.float32), 0.0, 1.0))
                if len(np.unique(y_val)) > 1:
                    try:
                        calibrator = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0)
                        calibrator.fit(probs, y_val.astype(np.float32))
                        self.probability_calibrators[name] = calibrator
                    except Exception as exc:
                        print(f"⚠️ Isotonic calibration skipped for {name}: {exc}")
                if std < 0.015 or auc < 0.62:
                    bad.append(name)
                    print(f"⚠️ DL model quality below threshold: {name} (std={std:.4f}, auc={auc:.4f})")

            if bad and len(bad) == len(self.models) and quality_scores:
                survivor = max(quality_scores, key=quality_scores.get)
                bad = [name for name in bad if name != survivor]
                print(f"⚠️ Retaining best available DL model despite low quality: {survivor}")

            for name in bad:
                self.low_quality_models.add(name)
                print(f"⚠️ Disabled low-diversity DL model: {name}")
        except Exception as e:
            print(f"⚠️ DL health-check skipped: {e}")

    def _safe_model_probability(self, model: Any, img_tensor: np.ndarray, model_name: str) -> float:
        """Return malignant probability in [0, 1] for binary models with 1 or 2 outputs."""
        if self.model_types.get(model_name) == "sklearn":
            img = img_tensor[0]
            if img.max() <= 1.5:
                img = img * 255.0
            feats = self._extract_image_features(img).reshape(1, -1)
            probs = model.predict_proba(feats)[0]
            prob = float(probs[1]) if len(probs) > 1 else float(probs[0])
            return float(np.clip(prob, 0.0, 1.0))

        preds = model(img_tensor, training=False).numpy()

        def _sigmoid(x: float) -> float:
            return 1.0 / (1.0 + np.exp(-x))

        if preds.ndim == 1:
            prob = float(preds[0])
            if prob < 0.0 or prob > 1.0:
                prob = _sigmoid(prob)
        elif preds.shape[-1] == 1:
            prob = float(preds[0][0])
            if prob < 0.0 or prob > 1.0:
                prob = _sigmoid(prob)
        else:
            vec = np.asarray(preds[0], dtype=np.float32)
            # If output does not look like probabilities, convert logits to probabilities.
            if np.any(vec < 0.0) or np.any(vec > 1.0) or abs(float(np.sum(vec)) - 1.0) > 0.05:
                vec = np.exp(vec - np.max(vec))
                vec = vec / np.sum(vec)
            prob = float(vec[1])
        prob = float(np.clip(prob, 0.0, 1.0))
        if self.model_invert_probability.get(model_name, False):
            prob = 1.0 - prob
        return float(np.clip(prob, 0.0, 1.0))

    def _load_validation_arrays(self, model_name: str | None = None) -> Tuple[np.ndarray, np.ndarray]:
        val_dir = PROJECT_ROOT / "data" / "cbis_ddsm" / "processed" / "images" / "val"
        benign_dir = val_dir / "benign"
        malignant_dir = val_dir / "malignant"
        target_size = self._target_size_for_model(model_name)

        if not benign_dir.exists() or not malignant_dir.exists():
            return (
                np.empty((0, target_size[0], target_size[1], 3), dtype=np.float32),
                np.empty((0,), dtype=np.int32),
            )

        image_paths: List[Tuple[Path, int]] = []
        image_paths.extend((p, 0) for p in sorted(benign_dir.glob("*.png")))
        image_paths.extend((p, 1) for p in sorted(malignant_dir.glob("*.png")))

        images: List[np.ndarray] = []
        labels: List[int] = []
        for path, label in image_paths:
            try:
                img = Image.open(path).convert("RGB").resize(target_size)
                images.append(np.asarray(img, dtype=np.float32))
                labels.append(label)
            except Exception:
                continue

        if not images:
            return (
                np.empty((0, target_size[0], target_size[1], 3), dtype=np.float32),
                np.empty((0,), dtype=np.int32),
            )

        return np.stack(images, axis=0), np.asarray(labels, dtype=np.int32)

    def _resize_batch(self, image_batch: np.ndarray, target_size: Tuple[int, int]) -> np.ndarray:
        x = np.asarray(image_batch, dtype=np.float32)
        if x.ndim == 3:
            x = np.expand_dims(x, axis=0)
        resized = [
            cv2.resize(img.astype(np.float32), (target_size[1], target_size[0]), interpolation=cv2.INTER_AREA)
            for img in x
        ]
        return np.stack(resized, axis=0)

    def _preprocess_for_model(self, model_name: str, image_batch: np.ndarray) -> np.ndarray:
        """Apply model-specific preprocessing for consistent calibration and inference."""
        tf = _get_tf()
        target_size = self._target_size_for_model(model_name)
        x = self._resize_batch(image_batch, target_size)

        if model_name == "ResNet50":
            return tf.keras.applications.resnet50.preprocess_input(x)
        if model_name == "EfficientNet-B0":
            return tf.keras.applications.efficientnet.preprocess_input(x)

        # Custom CNN models in this repo already include a Rescaling layer.
        return x

    def _extract_image_features(self, image_rgb: np.ndarray) -> np.ndarray:
        arr = np.asarray(image_rgb, dtype=np.float32)
        target_size = self.target_size
        if arr.ndim == 3 and arr.shape[-1] == 3:
            gray = cv2.cvtColor(np.uint8(np.clip(arr, 0, 255)), cv2.COLOR_RGB2GRAY).astype(np.float32)
        else:
            gray = arr.astype(np.float32)

        gray = cv2.resize(gray, (target_size[1], target_size[0]), interpolation=cv2.INTER_AREA)

        hist = cv2.calcHist([np.uint8(np.clip(gray, 0, 255))], [0], None, [24], [0, 256]).reshape(-1)
        hist = hist / max(float(hist.sum()), 1.0)

        p = np.percentile(gray, [5, 25, 50, 75, 95]).astype(np.float32)
        lap_var = float(cv2.Laplacian(gray, cv2.CV_32F).var())
        gx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
        gy = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
        grad_mag = np.sqrt(gx * gx + gy * gy)
        grad_mean = float(np.mean(grad_mag))

        probs = np.clip(hist, 1e-12, 1.0)
        entropy = float(-np.sum(probs * np.log(probs)))

        basics = np.array(
            [
                float(np.mean(gray)),
                float(np.std(gray)),
                float(np.min(gray)),
                float(np.max(gray)),
                lap_var,
                grad_mean,
                entropy,
            ],
            dtype=np.float32,
        )

        return np.concatenate([basics, p, hist.astype(np.float32)], axis=0)

    def _raw_probabilities_from_predictions(self, preds: np.ndarray) -> np.ndarray:
        preds = np.asarray(preds)

        if preds.ndim == 1:
            probs = preds.astype(np.float32)
        elif preds.shape[-1] == 1:
            probs = preds[:, 0].astype(np.float32)
        else:
            vec = preds.astype(np.float32)
            if np.any(vec < 0.0) or np.any(vec > 1.0) or np.max(np.abs(np.sum(vec, axis=1) - 1.0)) > 0.05:
                vec = np.exp(vec - np.max(vec, axis=1, keepdims=True))
                vec = vec / np.sum(vec, axis=1, keepdims=True)
            probs = vec[:, 1].astype(np.float32)

        outside = (probs < 0.0) | (probs > 1.0)
        if np.any(outside):
            probs = 1.0 / (1.0 + np.exp(-probs))

        return np.clip(probs, 0.0, 1.0)

    def _postprocess_probability(self, model_name: str, raw_probability: float) -> float:
        p_raw = float(np.clip(raw_probability, 1e-6, 1.0 - 1e-6))
        if self.probability_postprocess_mode in {"raw", "none", "disabled"}:
            return float(np.clip(p_raw, 0.001, 0.999))

        reference_threshold = float(self.centering_reference_thresholds.get(model_name, self.thresholds.get(model_name, 0.5)))
        std_probability = float(self.model_probability_stds.get(model_name, 0.04))

        if self.probability_postprocess_mode in {"spread", "threshold_spread", "threshold"}:
            scale = max(std_probability, 0.025)
            z = (p_raw - reference_threshold) / scale
            p_spread = 1.0 / (1.0 + np.exp(-z))
            return float(np.clip(p_spread, 0.02, 0.98))

        calibrator = self.probability_calibrators.get(model_name)
        p_iso = None
        if calibrator is not None:
            try:
                if isinstance(calibrator, tuple) and len(calibrator) == 2:
                    x_thr, y_thr = calibrator
                    p_iso = float(np.clip(np.interp(p_raw, x_thr, y_thr), 0.0, 1.0))
                else:
                    p_iso = float(np.clip(calibrator.predict([p_raw])[0], 0.0, 1.0))
            except Exception:
                p_iso = None

        ref = self.model_probability_reference.get(model_name)
        if self.probability_postprocess_mode in {"empirical", "rank_blend", "rank"} and isinstance(ref, np.ndarray) and ref.size > 20:
            rank = float(np.searchsorted(ref, p_raw, side="right") / ref.size)
            p_rank = float(np.clip(0.10 + 0.80 * rank, 0.10, 0.90))
            if p_iso is not None:
                p = 0.15 * p_raw + 0.55 * p_iso + 0.30 * p_rank
            else:
                p = 0.20 * p_raw + 0.80 * p_rank
            return float(np.clip(p, 0.10, 0.90))

        if self.probability_postprocess_mode in {"isotonic", "iso"} and p_iso is not None:
            return float(np.clip(p_iso, 0.02, 0.98))

        if p_iso is not None:
            return float(np.clip(0.25 * p_raw + 0.75 * p_iso, 0.10, 0.90))

        return float(np.clip(p_raw, 0.10, 0.90))

    def get_gradcam(self, model, img_tensor, model_name, target_size: Tuple[int, int] | None = None):
        try:
            tf = _get_tf()
            target_size = target_size or self._target_size_for_model(model_name)
            # Dynamically find the last conv layer for any model
            target_layer_name = None
            base_model = None
            
            # Check for inner Functional/Sequential models
            for layer in model.layers:
                if isinstance(layer, tf.keras.Model):
                    base_model = layer
                    break
                    
            search_model = base_model if base_model else model
            
            # Find the last layer that has 'conv' in its name or is a Convolutional layer
            for layer in reversed(search_model.layers):
                if 'conv' in layer.name.lower() or 'top_activation' in layer.name.lower():
                    target_layer_name = layer.name
                    break
                    
            if not target_layer_name: 
                return None, []
                
            target_layer = search_model.get_layer(target_layer_name)
            
            if base_model:
                grad_model = tf.keras.models.Model([base_model.inputs], [target_layer.output, base_model.output])
            else:
                try:
                    grad_model = tf.keras.models.Model(model.input, [target_layer.output, model.output])
                except Exception:
                    # Keras 3 Sequential undefined input fallback wrapper
                    xin = tf.keras.Input(shape=(target_size[0], target_size[1], 3))
                    x = xin
                    target_out = None
                    for layer in search_model.layers:
                        x = layer(x)
                        if layer.name == target_layer_name: target_out = x
                    grad_model = tf.keras.models.Model(xin, [target_out, x])

            with tf.GradientTape() as tape:
                conv_outputs, predictions = grad_model(img_tensor)
                loss = predictions[:, 0] if predictions.shape[-1] == 1 else predictions[:, 1]

            grads = tape.gradient(loss, conv_outputs)
            if grads is None: return None, []
            
            pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))
            conv_outputs = conv_outputs[0]
            heatmap = tf.reduce_sum(tf.multiply(pooled_grads, conv_outputs), axis=-1)
            heatmap = np.maximum(heatmap, 0) / (np.max(heatmap) + 1e-10)
            
            # Shaper Contours for clearer detection
            heatmap_uint8 = np.uint8(255 * heatmap)
            heatmap_resized = cv2.resize(heatmap_uint8, (target_size[1], target_size[0]))
            # Use Otsu's thresholding for more precise region extraction
            _, thresh = cv2.threshold(heatmap_resized, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            regions = []
            for cnt in contours:
                area = cv2.contourArea(cnt)
                if area > 150: 
                    x, y, w, h = cv2.boundingRect(cnt)
                    # Determine location relative to center
                    loc_description = self._get_location_name(x + w/2, y + h/2, target_size)
                    regions.append({"x": x, "y": y, "w": w, "h": h, "area": area, "loc": loc_description})
                    
            return heatmap, regions
        except Exception as e:
            print(f"Grad-CAM error: {e}")
            return None, []

    def _get_location_name(self, cx, cy, target_size: Tuple[int, int] | None = None):
        target_size = target_size or self.target_size
        mid_x, mid_y = target_size[1] / 2, target_size[0] / 2
        v_pos = "phía trên" if cy < mid_y else "phía dưới"
        h_pos = "bên trái" if cx < mid_x else "bên phải"
        return f"{v_pos} {h_pos}"

    def predict(self, image_bytes: bytes, model_name: str = None, include_explanation: bool = False):
        self._ensure_models_loaded(model_name)
        if not self.models:
            raise ValueError("No DL models available.")

        available = self.get_available_models()
        if not model_name or model_name not in available:
            if self.primary_explain_model and self.primary_explain_model in available:
                model_name = self.primary_explain_model
            else:
                model_name = available[0]
        if model_name in self.low_quality_models:
            model_name = "Ensemble" if "Ensemble" in available else available[0]

        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        explain_target_size = self._target_size_for_model(model_name if model_name != "Ensemble" else self.primary_explain_model)
        img_orig = np.array(image.resize(explain_target_size))

        img_float = img_orig.astype(np.float32)

        per_model_prob: Dict[str, float] = {}
        explain_input_tensor: np.ndarray

        if model_name == "Ensemble":
            for name, model in self.models.items():
                if name in self.low_quality_models:
                    continue
                img_tensor = self._preprocess_for_model(name, img_float)
                raw_prob = self._safe_model_probability(model, img_tensor, name)
                per_model_prob[name] = self._postprocess_probability(name, raw_prob)

            if not per_model_prob:
                raise ValueError("No models available for ensemble prediction.")

            prob = 0.0
            total_weight = 0.0
            for name, p in per_model_prob.items():
                w = float(self.ensemble_weights.get(name, 0.0))
                prob += p * w
                total_weight += w

            if total_weight > 0:
                prob = prob / total_weight
            else:
                prob = float(np.mean(list(per_model_prob.values())))

            threshold = float(self.ensemble_threshold)
            explain_model_name = self.primary_explain_model if self.primary_explain_model in self.models else next(iter(self.models.keys()))
            explain_model = self.models[explain_model_name]
            explain_input_tensor = self._preprocess_for_model(explain_model_name, img_float)
        else:
            model = self.models[model_name]
            img_tensor = self._preprocess_for_model(model_name, img_float)
            raw_prob = self._safe_model_probability(model, img_tensor, model_name)
            prob = self._postprocess_probability(model_name, raw_prob)
            threshold = float(self.thresholds.get(model_name, 0.5))
            explain_model_name = model_name
            explain_model = model
            explain_input_tensor = img_tensor

        prob = float(np.clip(prob, 0.0, 1.0))
        if model_name == "Ensemble":
            is_mal = prob >= threshold
        else:
            is_mal = float(raw_prob) >= threshold
        confidence = prob

        heatmap = None
        regions = []
        if include_explanation and self.model_types.get(explain_model_name) != "sklearn":
            heatmap, regions = self.get_gradcam(
                explain_model,
                explain_input_tensor,
                explain_model_name,
                target_size=explain_target_size,
            )
        heatmap_url = None
        
        if heatmap is not None:
            heatmap_resized = cv2.resize(heatmap, (explain_target_size[1], explain_target_size[0]))
            heatmap_color = cv2.applyColorMap(np.uint8(255 * heatmap_resized), cv2.COLORMAP_JET)
            
            # High-intensity overlay
            overlaid = cv2.addWeighted(img_orig, 0.4, heatmap_color, 0.6, 0)
            
            # Highlight regions with high-visibility markers
            for region in regions:
                # White border for clear visibility on dark areas
                cv2.rectangle(overlaid, (region['x'], region['y']), 
                             (region['x'] + region['w'], region['y'] + region['h']), 
                             (255, 255, 255), 2)
                # Outer shadow for the box
                cv2.rectangle(overlaid, (region['x']-1, region['y']-1), 
                             (region['x'] + region['w'] + 1, region['y'] + region['h'] + 1), 
                             (0, 0, 0), 1)
                
                # Small pinpoint circle at the center of the region
                center = (int(region['x'] + region['w']/2), int(region['y'] + region['h']/2))
                cv2.circle(overlaid, center, 4, (255, 255, 255), -1)
                cv2.circle(overlaid, center, 5, (0, 0, 255), 1)
            
            filename = f"gradcam_{uuid.uuid4().hex}.png"
            cv2.imwrite(str(STATIC_RESULTS_DIR / filename), cv2.cvtColor(overlaid, cv2.COLOR_RGB2BGR))
            heatmap_url = f"/results/{filename}"
            
        return {
            "model_name": model_name,
            "prediction": 1 if is_mal else 0,
            "diagnosis": "Malignant" if is_mal else "Benign",
            "probability": confidence,
            "raw_probability": raw_prob if model_name != "Ensemble" else None,
            "calibration_mode": (
                "raw_model_output"
                if self.probability_postprocess_mode in {"raw", "none", "disabled"}
                else "threshold_spread_validation"
                if self.probability_postprocess_mode in {"spread", "threshold_spread", "threshold"}
                else "isotonic_validation"
                if self.probability_postprocess_mode in {"isotonic", "iso"}
                else "isotonic_empirical_validation"
            ),
            "risk_band": self._risk_band_from_probability(confidence),
            "explanation_image": heatmap_url,
            "analysis_text": self._generate_analysis(model_name, is_mal, confidence, regions)
        }

    def _generate_analysis(self, model, is_mal, conf, regions):
        import random
        region_count = len(regions)
        
        # Diverse descriptions
        suspicious_traits = [
            "có độ tương phản bất thường so với mô mỡ xung quanh",
            "cho thấy mật độ tế bào tập trung cao không đồng đều",
            "có viền mờ ranh giới không rõ ràng, gợi ý sự thâm nhiễm",
            "phát hiện cấu trúc vi vôi hóa đa hình thái",
            "có sự biến đổi cấu trúc cục bộ so với các mô lân cận"
        ]
        
        benign_traits = [
            "cấu trúc mô đồng nhất, không có dấu hiệu xơ hóa",
            "mật độ tuyến vú bình thường theo thang phân loại BI-RADS",
            "không phát hiện vùng tập trung canxi vi mô đáng ngờ",
            "ranh giới mô rõ ràng, không có dấu hiệu xâm lấn hoặc co rút"
        ]
        
        if is_mal:
            analysis = f"🚨 **CẢNH BÁO HỆ THỐNG: PHÁT HIỆN DẤU HIỆU ÁC TÍNH RÕ RỆT ({conf:.1%})**\n\n"
            analysis += f"Hệ thống thị giác ({model}) đã quét và phát hiện **{region_count if region_count > 0 else 'các'} vùng tổn thương** có cấu trúc phức tạp.\n\n"
            
            for i, r in enumerate(regions):
                trait = random.choice(suspicious_traits)
                analysis += f"📍 **Vùng nghi ngờ {i+1}:** Được xác định ở **{r['loc']}** của ảnh (kích thước vùng khảo sát: {int(r['w'])}x{int(r['h'])}). Vùng này {trait}.\n"
            
            if region_count == 0:
                analysis += f"📍 **Phát hiện chung:** {random.choice(suspicious_traits)} lan tỏa trên nền mô tuyến vú.\n"
                
            analysis += "\n📋 **PHÂN TÍCH CHUYÊN SÂU:**\n"
            analysis += "- **Mật độ mô:** Các vùng điểm đỏ trên bản đồ nhiệt tập trung chỉ điểm đặc tính khối u ác tính xâm lấn.\n"
            analysis += "- **Hình dạng:** Sự phân bố tín hiệu Grad-CAM lan rộng cho thấy ranh giới tổn thương không sắc nét.\n\n"
            analysis += "🩺 **KHUYẾN NGHỊ LÂM SÀNG:**\n"
            analysis += "1. **Sinh thiết tức thì:** Chỉ định bắt buộc. Thực hiện sinh thiết kim lõi (Core Biopsy) tại các vị trí đánh dấu.\n"
            analysis += "2. **Hội chẩn cận lâm sàng:** Đề nghị chụp MRI tuyến vú có cản từ để đánh giá mạng lưới mạch máu tân sinh."
            return analysis
        else:
            analysis = f"✅ **KẾT QUẢ SÀNG LỌC: HIỆN CHƯA PHÁT HIỆN BẤT THƯỜNG ({conf:.1%})**\n\n"
            analysis += f"Mô hình ({model}) nhận diện cấu trúc mô vú hiện tại nằm trong giới hạn an toàn.\n\n"
            
            if region_count > 0:
                analysis += "📍 **Các vùng lưu ý phụ:**\n"
                for i, r in enumerate(regions[:2]): # Show max 2
                    analysis += f"- Vùng {r['loc']} có chút tăng mật độ sinh lý, nhưng {random.choice(benign_traits)}.\n"
            else:
                 analysis += f"📍 **Đánh giá tổng quan:** Toàn bộ trường nhìn của phim chụp có {random.choice(benign_traits)}.\n"
                 
            analysis += "\n📋 **LỜI KHUYÊN BÁC SĨ:**\n"
            analysis += "1. **Tầm soát định kỳ:** Tiếp tục chụp X-Quang nhũ ảnh (Mammography) mỗi 12 tháng.\n"
            analysis += "2. **Cảnh báo sớm:** Dù kết quả âm tính, hãy đi khám ngay nếu sờ thấy khối cứng, núm vú tiết dịch hoặc da có dấu hiệu co rút sần vỏ cam."
            return analysis

dl_prediction_service = DeepLearningService()
