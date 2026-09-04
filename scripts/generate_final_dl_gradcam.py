#!/usr/bin/env python3
"""Generate reproducible Grad-CAM examples for the frozen final DL candidate.

This script is analysis-only: it verifies the saved model checksum, reads the
fixed test order from the manifest, and never changes model weights or the
pre-specified operating threshold.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
from collections import Counter
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")

import matplotlib.pyplot as plt
import numpy as np
import tensorflow as tf
from PIL import Image
from sklearn.linear_model import LogisticRegression

from dl_manifest import load_manifest_records, split_records

ROOT = Path(__file__).resolve().parent.parent
FINAL = ROOT / "experiments" / "final"
RUN = FINAL / "runs" / "efficientnet_b0_full"
MANIFEST = ROOT / "manifests" / "cbis_group_split_seed42.csv"
OUTPUT = FINAL / "gradcam"
FIGURE = FINAL / "figures" / "efficientnet_gradcam_examples.png"


def load_prediction_rows(name: str) -> list[dict[str, str]]:
    with (RUN / f"{name}_predictions.csv").open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def verify_model() -> tuple[Path, dict]:
    metadata = json.loads((RUN / "model_metadata.json").read_text(encoding="utf-8"))
    model_path = Path(metadata["model_file"])
    if not model_path.is_file():
        raise FileNotFoundError(f"Frozen model is unavailable: {model_path}")
    digest = hashlib.sha256(model_path.read_bytes()).hexdigest()
    if digest != metadata["sha256"]:
        raise RuntimeError("Model SHA-256 does not match the frozen model metadata.")
    return model_path, metadata


def calibrated_test_probabilities() -> np.ndarray:
    """Fit the already-selected Platt transform on validation predictions only."""
    validation = load_prediction_rows("validation")
    test = load_prediction_rows("test")
    x_val = np.asarray([float(row["malignant_probability"]) for row in validation])
    y_val = np.asarray([int(row["label"]) for row in validation])
    x_test = np.asarray([float(row["malignant_probability"]) for row in test])
    model = LogisticRegression(C=1e6, solver="lbfgs").fit(x_val.reshape(-1, 1), y_val)
    return model.predict_proba(x_test.reshape(-1, 1))[:, 1]


def classify(label: int, prediction: int) -> str:
    if label == 1 and prediction == 1:
        return "TP"
    if label == 0 and prediction == 0:
        return "TN"
    if label == 0:
        return "FP"
    return "FN"


def select_examples(rows: list[dict]) -> list[dict]:
    """Choose a median- and high-confidence test record for each outcome."""
    selected: list[dict] = []
    for outcome in ("TP", "TN", "FP", "FN"):
        candidates = sorted((row for row in rows if row["outcome_type"] == outcome), key=lambda row: row["test_index"])
        if len(candidates) < 2:
            raise RuntimeError(f"Need at least two {outcome} cases, found {len(candidates)}.")
        distances = np.asarray([row["distance_from_threshold"] for row in candidates])
        median_distance = float(np.median(distances))
        median_case = min(candidates, key=lambda row: (abs(row["distance_from_threshold"] - median_distance), row["test_index"]))
        remaining = [row for row in candidates if row["test_index"] != median_case["test_index"]]
        high_case = max(remaining, key=lambda row: (row["distance_from_threshold"], -row["test_index"]))
        median_case = dict(median_case, selection_reason="median confidence: nearest median absolute distance from frozen threshold")
        high_case = dict(high_case, selection_reason="high confidence: greatest absolute distance from frozen threshold")
        selected.extend((median_case, high_case))
    return selected


def find_final_conv_layer(model: tf.keras.Model) -> tuple[tf.keras.Model, tf.keras.layers.Layer]:
    """Return the last spatial Conv2D layer actually present in this saved model."""
    candidates: list[tuple[tf.keras.Model, tf.keras.layers.Layer]] = []

    def visit(container: tf.keras.Model) -> None:
        for layer in getattr(container, "layers", []):
            if isinstance(layer, tf.keras.layers.Conv2D):
                candidates.append((container, layer))
            if isinstance(layer, tf.keras.Model):
                visit(layer)

    visit(model)
    if not candidates:
        raise RuntimeError("No Conv2D layer was found for Grad-CAM.")
    return candidates[-1]


def build_grad_model(model: tf.keras.Model, backbone: tf.keras.Model, conv_layer: tf.keras.layers.Layer) -> tuple[tf.keras.Model, tf.keras.Model]:
    """Expose backbone activations and rebuild the saved classification head."""
    try:
        backbone_grad_model = tf.keras.Model(backbone.inputs, [conv_layer.output, backbone.output])
        backbone_index = model.layers.index(backbone)
        features = tf.keras.Input(shape=backbone.output.shape[1:], name="gradcam_backbone_features")
        output = features
        for layer in model.layers[backbone_index + 1:]:
            output = layer(output, training=False)
        classifier_head = tf.keras.Model(features, output, name="gradcam_classifier_head")
        return backbone_grad_model, classifier_head
    except ValueError as exc:
        raise RuntimeError(f"Could not connect Grad-CAM layer {conv_layer.name} to model output.") from exc


def load_image(path: Path, image_size: int) -> tuple[np.ndarray, tuple[int, int]]:
    with Image.open(path) as image:
        source_size = image.size
    # Match _dataset_from_records in the frozen trainer exactly.
    decoded = tf.io.decode_image(tf.io.read_file(str(path)), channels=3, expand_animations=False)
    resized = tf.image.resize(tf.cast(decoded, tf.float32), (image_size, image_size))
    return resized.numpy(), source_size


def gradcam(backbone_grad_model: tf.keras.Model, classifier_head: tf.keras.Model, image: np.ndarray) -> tuple[float, np.ndarray]:
    input_tensor = tf.convert_to_tensor(image[None, ...], dtype=tf.float32)
    with tf.GradientTape() as tape:
        conv_output, features = backbone_grad_model(input_tensor, training=False)
        prediction = classifier_head(features, training=False)
        score = prediction[:, 0]
    gradients = tape.gradient(score, conv_output)
    if gradients is None:
        raise RuntimeError("Grad-CAM gradients are unavailable for the chosen layer.")
    weights = tf.reduce_mean(gradients, axis=(0, 1, 2))
    heatmap = tf.reduce_sum(conv_output[0] * weights, axis=-1)
    heatmap = tf.maximum(heatmap, 0)
    maximum = float(tf.reduce_max(heatmap).numpy())
    if maximum > 0:
        heatmap = heatmap / maximum
    heatmap = tf.image.resize(heatmap[..., None], image.shape[:2]).numpy()[..., 0]
    if not np.isfinite(heatmap).all():
        raise RuntimeError("Grad-CAM heatmap contains non-finite values.")
    return float(prediction[0, 0].numpy()), np.clip(heatmap, 0, 1)


def write_case(case: dict, image: np.ndarray, heatmap: np.ndarray) -> dict:
    category = case["outcome_type"].lower()
    case_dir = OUTPUT / category
    case_dir.mkdir(parents=True, exist_ok=True)
    stem = f"test_{case['test_index']:03d}_{case['selection_reason'].split(':', 1)[0].replace(' ', '_')}"
    original_path = case_dir / f"{stem}_original.png"
    heatmap_path = case_dir / f"{stem}_heatmap.png"
    overlay_path = case_dir / f"{stem}_overlay.png"
    original = np.asarray(np.clip(image, 0, 255), dtype=np.uint8)
    colored = np.asarray(plt.colormaps["jet"](heatmap)[..., :3] * 255, dtype=np.uint8)
    overlay = np.asarray(0.58 * original + 0.42 * colored, dtype=np.uint8)
    Image.fromarray(original).save(original_path)
    Image.fromarray(colored).save(heatmap_path)
    Image.fromarray(overlay).save(overlay_path)
    return {
        **case,
        "original_image": str(original_path.relative_to(ROOT)),
        "heatmap_image": str(heatmap_path.relative_to(ROOT)),
        "overlay_image": str(overlay_path.relative_to(ROOT)),
    }


def write_composite(cases: list[dict]) -> None:
    figure, axes = plt.subplots(2, 4, figsize=(16, 8))
    for axis, case in zip(axes.flat, cases):
        axis.imshow(Image.open(ROOT / case["overlay_image"]))
        label = "malignant" if case["true_label"] else "benign"
        predicted = "malignant" if case["predicted_label"] else "benign"
        axis.set_title(
            f"{case['outcome_type']} | {case['selection_reason'].split(':', 1)[0]}\n"
            f"GT {label}; Pred {predicted}; raw p={case['raw_probability']:.3f}\n"
            f"Platt p={case['calibrated_probability']:.3f}; Grad-CAM activation",
            fontsize=9,
        )
        axis.axis("off")
    figure.tight_layout()
    FIGURE.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(FIGURE, dpi=180)
    plt.close(figure)


def main() -> None:
    config = json.loads((RUN / "config.json").read_text(encoding="utf-8"))
    if config["image_set"] != "images" or int(config["image_size"]) != 224:
        raise RuntimeError("Frozen candidate configuration is not the expected full-image 224px model.")
    model_path, model_metadata = verify_model()
    threshold = float(json.loads((RUN / "threshold.json").read_text(encoding="utf-8"))["threshold"])
    predictions = load_prediction_rows("test")
    records = split_records(load_manifest_records(MANIFEST, image_set="images"))["test"]
    if len(predictions) != len(records):
        raise RuntimeError(f"Prediction/manifest test count mismatch: {len(predictions)} != {len(records)}")
    calibrated = calibrated_test_probabilities()
    rows: list[dict] = []
    for index, (prediction, record, calibrated_probability) in enumerate(zip(predictions, records, calibrated)):
        label = int(prediction["label"])
        if label != record.label or int(prediction["index"]) != index:
            raise RuntimeError(f"Test prediction ordering mismatch at index {index}.")
        probability = float(prediction["malignant_probability"])
        predicted_label = int(probability >= threshold)
        if predicted_label != int(prediction["prediction"]):
            raise RuntimeError(f"Frozen prediction mismatch at index {index}.")
        rows.append({
            "test_index": index, "sample_id": f"test_index_{index}", "group_id": record.group_id,
            "relative_path": record.relative_path, "true_label": label, "raw_probability": probability,
            "calibrated_probability": float(calibrated_probability), "threshold": threshold,
            "predicted_label": predicted_label, "outcome_type": classify(label, predicted_label),
            "distance_from_threshold": abs(probability - threshold), "image_set": "images",
            "calibration_note": "Platt transform fitted on frozen validation predictions only; not used for Grad-CAM or selection.",
            "model_sha256": model_metadata["sha256"],
        })

    selected = select_examples(rows)
    model = tf.keras.models.load_model(model_path, compile=False)
    backbone, conv_layer = find_final_conv_layer(model)
    backbone_grad_model, classifier_head = build_grad_model(model, backbone, conv_layer)
    rendered: list[dict] = []
    for case in selected:
        image_path = ROOT / case["relative_path"]
        image, source_size = load_image(image_path, int(config["image_size"]))
        model_probability, heatmap = gradcam(backbone_grad_model, classifier_head, image)
        if not np.isclose(model_probability, case["raw_probability"], atol=1e-5):
            raise RuntimeError(f"Model probability mismatch for frozen test index {case['test_index']}.")
        rendered.append(write_case({**case, "source_dimensions": list(source_size), "render_dimensions": [224, 224], "gradcam_layer": conv_layer.name}, image, heatmap))

    OUTPUT.mkdir(parents=True, exist_ok=True)
    selection = {
        "analysis": "Grad-CAM for frozen EfficientNet-B0 full-image candidate",
        "model_path": str(model_path), "model_sha256": model_metadata["sha256"],
        "manifest": str(MANIFEST.relative_to(ROOT)), "image_set": "images", "threshold": threshold,
        "gradcam_layer": conv_layer.name,
        "selection_rule": "Within each TP/TN/FP/FN outcome, choose one case nearest the median absolute distance from the frozen threshold and one remaining case with the greatest distance.",
        "selection_counts": dict(Counter(row["outcome_type"] for row in rows)), "selected_cases": rendered,
    }
    for path in (OUTPUT / "selection.json", FINAL / "gradcam_selection.json"):
        path.write_text(json.dumps(selection, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    fieldnames = list(rendered[0])
    with (OUTPUT / "metadata.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader(); writer.writerows(rendered)
    write_composite(rendered)
    print(json.dumps({"gradcam_layer": conv_layer.name, "selected": len(rendered), "outcome_counts": selection["selection_counts"], "figure": str(FIGURE)}, indent=2))


if __name__ == "__main__":
    main()
