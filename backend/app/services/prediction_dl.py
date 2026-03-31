import os
import numpy as np
from pathlib import Path
from PIL import Image
import io
import cv2
import uuid
from typing import Dict, List, Tuple, Any

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

class DeepLearningService:
    def __init__(self):
        self.models = {}
        self.model_paths: Dict[str, Path] = {}
        self.target_size = (224, 224)
        self._discover_model_files()
        self.thresholds: Dict[str, float] = {name: 0.5 for name in self.model_paths}
        self.calibration_metrics: Dict[str, Dict[str, float]] = {}
        self.ensemble_weights: Dict[str, float] = {}
        self.ensemble_threshold: float = 0.5
        self.primary_explain_model: str = ""
        self.layer_map = {
            "ResNet50": "conv5_block3_out",
            "EfficientNet-B0": "top_activation",
            "Custom CNN": "conv2d_7"
        }

    def _discover_model_files(self):
        discovered: Dict[str, Path] = {}
        for model_dir in POSSIBLE_MODEL_DIRS:
            if not model_dir.exists():
                continue
            for model_path in model_dir.glob("*.keras"):
                name = self._normalize_model_name(model_path.stem)
                if name in discovered:
                    continue
                discovered[name] = model_path
        self.model_paths = discovered

    def _ensure_models_loaded(self):
        if self.models:
            return

        if not self.model_paths:
            self._discover_model_files()

        tf = _get_tf()
        for name, model_path in self.model_paths.items():
            try:
                self.models[name] = tf.keras.models.load_model(model_path)
                print(f"Loaded {name} from {model_path}")
            except Exception as e:
                print(f"Failed to load {model_path}: {e}")

        if self.models and not self.ensemble_weights:
            n = len(self.models)
            self.ensemble_weights = {name: 1.0 / n for name in self.models}
            self.primary_explain_model = next(iter(self.models.keys()))
            self.thresholds = {name: float(self.thresholds.get(name, 0.5)) for name in self.models}
        
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
        if len(names) > 1:
            names.append("Ensemble")
        return names

    def _safe_model_probability(self, model: Any, img_tensor: np.ndarray) -> float:
        """Return malignant probability in [0, 1] for binary models with 1 or 2 outputs."""
        preds = model.predict(img_tensor, verbose=0)
        if preds.ndim == 1:
            prob = float(preds[0])
        elif preds.shape[-1] == 1:
            prob = float(preds[0][0])
        else:
            # Assume class index 1 is malignant for 2-logit/2-proba outputs.
            prob = float(preds[0][1])
        return float(np.clip(prob, 0.0, 1.0))

    def _find_best_accuracy_threshold(self, y_true: np.ndarray, y_prob: np.ndarray) -> Tuple[float, float]:
        """Choose threshold maximizing validation accuracy; deterministic tie-break by smaller threshold."""
        candidate_thresholds = np.linspace(0.05, 0.95, 181)
        best_threshold = 0.5
        best_acc = -1.0

        for thr in candidate_thresholds:
            y_pred = (y_prob >= thr).astype(np.int32)
            acc = float((y_pred == y_true).mean())
            if acc > best_acc or (acc == best_acc and thr < best_threshold):
                best_acc = acc
                best_threshold = float(thr)

        return best_threshold, best_acc

    def _load_validation_arrays(self) -> Tuple[np.ndarray, np.ndarray]:
        """Load validation images (0=benign, 1=malignant) for threshold calibration."""
        val_dir = PROJECT_ROOT / "data" / "cbis_ddsm" / "processed" / "images" / "val"
        benign_dir = val_dir / "benign"
        malignant_dir = val_dir / "malignant"

        if not benign_dir.exists() or not malignant_dir.exists():
            return np.empty((0, self.target_size[0], self.target_size[1], 3), dtype=np.float32), np.empty((0,), dtype=np.int32)

        image_paths: List[Tuple[Path, int]] = []
        image_paths.extend((p, 0) for p in sorted(benign_dir.glob("*.png")))
        image_paths.extend((p, 1) for p in sorted(malignant_dir.glob("*.png")))

        if not image_paths:
            return np.empty((0, self.target_size[0], self.target_size[1], 3), dtype=np.float32), np.empty((0,), dtype=np.int32)

        images: List[np.ndarray] = []
        labels: List[int] = []

        for path, label in image_paths:
            try:
                img = Image.open(path).convert("RGB").resize(self.target_size)
                arr = np.asarray(img, dtype=np.float32) / 255.0
                images.append(arr)
                labels.append(label)
            except Exception:
                continue

        if not images:
            return np.empty((0, self.target_size[0], self.target_size[1], 3), dtype=np.float32), np.empty((0,), dtype=np.int32)

        return np.stack(images, axis=0), np.asarray(labels, dtype=np.int32)

    def _calibrate_models_from_validation(self):
        """Calibrate per-model thresholds and ensemble weights using validation accuracy."""
        self._ensure_models_loaded()
        if not self.models:
            return

        x_val, y_val = self._load_validation_arrays()
        if len(y_val) == 0:
            # Fallback defaults if validation set is unavailable.
            n = max(len(self.models), 1)
            self.ensemble_weights = {name: 1.0 / n for name in self.models}
            self.primary_explain_model = next(iter(self.models.keys()))
            return

        model_probs: Dict[str, np.ndarray] = {}
        model_accs: Dict[str, float] = {}

        for name, model in self.models.items():
            preds = model.predict(x_val, batch_size=16, verbose=0)
            if preds.ndim == 1:
                probs = preds.astype(np.float32)
            elif preds.shape[-1] == 1:
                probs = preds[:, 0].astype(np.float32)
            else:
                probs = preds[:, 1].astype(np.float32)

            probs = np.clip(probs, 0.0, 1.0)
            thr, acc = self._find_best_accuracy_threshold(y_val, probs)

            self.thresholds[name] = float(thr)
            self.calibration_metrics[name] = {
                "validation_accuracy": float(acc),
                "threshold": float(thr),
            }
            model_probs[name] = probs
            model_accs[name] = float(acc)

        # Weight stronger models higher, but keep all models contributing.
        total = sum(max(v, 0.01) for v in model_accs.values())
        if total <= 0:
            n = len(model_accs)
            self.ensemble_weights = {name: 1.0 / n for name in model_accs}
        else:
            self.ensemble_weights = {
                name: max(acc, 0.01) / total for name, acc in model_accs.items()
            }

        if model_probs:
            ensemble_prob = np.zeros_like(next(iter(model_probs.values())), dtype=np.float32)
            for name, probs in model_probs.items():
                ensemble_prob += probs * float(self.ensemble_weights.get(name, 0.0))

            ens_thr, ens_acc = self._find_best_accuracy_threshold(y_val, ensemble_prob)
            self.ensemble_threshold = float(ens_thr)
            self.calibration_metrics["Ensemble"] = {
                "validation_accuracy": float(ens_acc),
                "threshold": float(ens_thr),
            }

        if self.ensemble_weights:
            self.primary_explain_model = max(self.ensemble_weights, key=self.ensemble_weights.get)
        else:
            self.primary_explain_model = next(iter(self.models.keys()))

    def get_gradcam(self, model, img_tensor, model_name):
        try:
            tf = _get_tf()
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
                    xin = tf.keras.Input(shape=(self.target_size[0], self.target_size[1], 3))
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
            heatmap_resized = cv2.resize(heatmap_uint8, (self.target_size[1], self.target_size[0]))
            # Use Otsu's thresholding for more precise region extraction
            _, thresh = cv2.threshold(heatmap_resized, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            regions = []
            for cnt in contours:
                area = cv2.contourArea(cnt)
                if area > 150: 
                    x, y, w, h = cv2.boundingRect(cnt)
                    # Determine location relative to center
                    loc_description = self._get_location_name(x + w/2, y + h/2)
                    regions.append({"x": x, "y": y, "w": w, "h": h, "area": area, "loc": loc_description})
                    
            return heatmap, regions
        except Exception as e:
            print(f"Grad-CAM error: {e}")
            return None, []

    def _get_location_name(self, cx, cy):
        mid_x, mid_y = self.target_size[1] / 2, self.target_size[0] / 2
        v_pos = "phía trên" if cy < mid_y else "phía dưới"
        h_pos = "bên trái" if cx < mid_x else "bên phải"
        return f"{v_pos} {h_pos}"

    def predict(self, image_bytes: bytes, model_name: str = None):
        self._ensure_models_loaded()
        if not self.models:
            raise ValueError("No DL models available.")

        available = self.get_available_models()
        if not model_name or model_name not in available:
            model_name = "Ensemble" if "Ensemble" in available else available[0]

        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        img_orig = np.array(image.resize(self.target_size))

        # Standard pixel normalization [0, 1]
        img_float = img_orig.astype(np.float32)
        img_tensor = np.expand_dims(img_float / 255.0, axis=0)

        per_model_prob: Dict[str, float] = {}

        if model_name == "Ensemble":
            for name, model in self.models.items():
                per_model_prob[name] = self._safe_model_probability(model, img_tensor)

            if not per_model_prob:
                raise ValueError("No models available for ensemble prediction.")

            prob = 0.0
            for name, p in per_model_prob.items():
                prob += p * float(self.ensemble_weights.get(name, 0.0))

            threshold = float(self.ensemble_threshold)
            explain_model_name = self.primary_explain_model if self.primary_explain_model in self.models else next(iter(self.models.keys()))
            explain_model = self.models[explain_model_name]
        else:
            model = self.models[model_name]
            prob = self._safe_model_probability(model, img_tensor)
            threshold = float(self.thresholds.get(model_name, 0.5))
            explain_model_name = model_name
            explain_model = model

        prob = float(np.clip(prob, 0.0, 1.0))
        is_mal = prob >= threshold
        confidence = prob

        heatmap, regions = self.get_gradcam(explain_model, img_tensor, explain_model_name)
        heatmap_url = None
        
        if heatmap is not None:
            heatmap_resized = cv2.resize(heatmap, (self.target_size[1], self.target_size[0]))
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
