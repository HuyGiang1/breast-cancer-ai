#!/usr/bin/env python3

"""Train a final DL model from the leakage-safe CBIS manifest.

Example:
  source venv/bin/activate
  PYTHONPATH=backend python scripts/train_dl_finetune_calibrated.py \
    --architecture custom_cnn \
    --epochs 25 \
    --batch-size 16
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Tuple

import numpy as np
import tensorflow as tf
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    balanced_accuracy_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

from dl_manifest import ManifestRecord, load_manifest_records, split_records

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = PROJECT_ROOT / "manifests" / "cbis_group_split_seed42.csv"
MODEL_DIR = PROJECT_ROOT / "models" / "deep_learning"
CALIB_PATH = MODEL_DIR / "calibration_profile.json"


@dataclass
class DatasetBundle:
    train: tf.data.Dataset
    val: tf.data.Dataset
    test: tf.data.Dataset
    train_count: int
    val_count: int
    test_count: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fine-tune DL model with calibration export")
    parser.add_argument("--architecture", choices=["custom_cnn", "resnet50", "efficientnetb0"], default="custom_cnn")
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--image-size", type=int, default=224)
    parser.add_argument("--learning-rate", type=float, default=1e-4)
    parser.add_argument("--image-set", choices=["images", "images_roi"], default="images")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    parser.add_argument("--run-dir", type=Path, default=None, help="Directory for final run config and outputs.")
    parser.add_argument("--patience", type=int, default=5)
    parser.add_argument("--reduce-lr-patience", type=int, default=2)
    parser.add_argument("--cache-dataset", action="store_true")
    parser.add_argument("--output-stem", type=str, default="")
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def _dataset_from_records(records: list[ManifestRecord], image_size: int, batch_size: int, training: bool, seed: int) -> tf.data.Dataset:
    paths = [str(PROJECT_ROOT / record.relative_path) for record in records]
    missing = [path for path in paths if not Path(path).is_file()]
    if missing:
        raise FileNotFoundError(f"Manifest references missing local images, first: {missing[0]}")
    labels = np.asarray([record.label for record in records], dtype=np.float32)
    dataset = tf.data.Dataset.from_tensor_slices((paths, labels))
    if training:
        dataset = dataset.shuffle(len(paths), seed=seed, reshuffle_each_iteration=True)

    def decode(path: tf.Tensor, label: tf.Tensor) -> tuple[tf.Tensor, tf.Tensor]:
        image = tf.io.decode_image(tf.io.read_file(path), channels=3, expand_animations=False)
        image.set_shape([None, None, 3])
        return tf.image.resize(tf.cast(image, tf.float32), (image_size, image_size)), label

    return dataset.map(decode, num_parallel_calls=tf.data.AUTOTUNE).batch(batch_size).prefetch(tf.data.AUTOTUNE)


def load_datasets(manifest: Path, image_set: str, image_size: int, batch_size: int, seed: int, cache_dataset: bool) -> DatasetBundle:
    records = split_records(load_manifest_records(manifest, image_set=image_set))
    train_ds = _dataset_from_records(records["train"], image_size, batch_size, training=True, seed=seed)
    val_ds = _dataset_from_records(records["val"], image_size, batch_size, training=False, seed=seed)
    test_ds = _dataset_from_records(records["test"], image_size, batch_size, training=False, seed=seed)

    autotune = tf.data.AUTOTUNE
    if cache_dataset:
        train_ds = train_ds.cache()
        val_ds = val_ds.cache()
        test_ds = test_ds.cache()
    train_ds = train_ds.prefetch(autotune)
    val_ds = val_ds.prefetch(autotune)
    test_ds = test_ds.prefetch(autotune)

    return DatasetBundle(train_ds, val_ds, test_ds, len(records["train"]), len(records["val"]), len(records["test"]))


def get_class_weights(records: list[ManifestRecord]) -> Dict[int, float]:
    benign = sum(record.label == 0 for record in records)
    malignant = sum(record.label == 1 for record in records)
    total = max(benign + malignant, 1)
    return {
        0: total / max(2 * benign, 1),
        1: total / max(2 * malignant, 1),
    }


def build_model(architecture: str, image_size: int, lr: float) -> tf.keras.Model:
    inp = tf.keras.Input(shape=(image_size, image_size, 3), name="input_image")

    if architecture == "resnet50":
        x = tf.keras.applications.resnet50.preprocess_input(inp)
        backbone = tf.keras.applications.ResNet50(include_top=False, weights="imagenet", pooling="avg")
        backbone.trainable = False
        x = backbone(x)
    elif architecture == "efficientnetb0":
        x = tf.keras.applications.efficientnet.preprocess_input(inp)
        backbone = tf.keras.applications.EfficientNetB0(include_top=False, weights="imagenet", pooling="avg")
        backbone.trainable = False
        x = backbone(x)
    else:
        x = tf.keras.layers.Rescaling(1.0 / 255.0)(inp)
        x = tf.keras.layers.Conv2D(32, 3, padding="same", activation="relu")(x)
        x = tf.keras.layers.MaxPool2D()(x)
        x = tf.keras.layers.Conv2D(64, 3, padding="same", activation="relu")(x)
        x = tf.keras.layers.MaxPool2D()(x)
        x = tf.keras.layers.Conv2D(128, 3, padding="same", activation="relu")(x)
        x = tf.keras.layers.GlobalAveragePooling2D()(x)

    x = tf.keras.layers.Dropout(0.3)(x)
    x = tf.keras.layers.Dense(128, activation="relu")(x)
    x = tf.keras.layers.Dropout(0.25)(x)
    out = tf.keras.layers.Dense(1, activation="sigmoid", name="malignant_probability")(x)

    model = tf.keras.Model(inp, out, name=f"{architecture}_finetuned")

    loss_fn = tf.keras.losses.BinaryFocalCrossentropy(gamma=2.0, alpha=0.25)
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=lr),
        loss=loss_fn,
        metrics=[
            tf.keras.metrics.BinaryAccuracy(name="accuracy"),
            tf.keras.metrics.AUC(name="auc"),
            tf.keras.metrics.Precision(name="precision"),
            tf.keras.metrics.Recall(name="recall"),
        ],
    )
    return model


def collect_predictions(model: tf.keras.Model, dataset: tf.data.Dataset) -> Tuple[np.ndarray, np.ndarray]:
    y_true, y_prob = [], []
    for x, y in dataset:
        p = model.predict(x, verbose=0).ravel()
        y_prob.extend(p.tolist())
        y_true.extend(y.numpy().ravel().tolist())
    return np.asarray(y_true, dtype=np.int32), np.asarray(y_prob, dtype=np.float32)


def best_threshold(y_true: np.ndarray, y_prob: np.ndarray) -> Tuple[float, float]:
    thresholds = np.linspace(0.05, 0.95, 181)
    best_t, best_bacc = 0.5, -1.0
    for t in thresholds:
        pred = (y_prob >= t).astype(np.int32)
        bacc = balanced_accuracy_score(y_true, pred)
        if bacc > best_bacc:
            best_bacc = float(bacc)
            best_t = float(t)
    return best_t, best_bacc


def evaluate(y_true: np.ndarray, y_prob: np.ndarray, threshold: float) -> dict:
    prediction = (y_prob >= threshold).astype(np.int32)
    tn, fp, fn, tp = confusion_matrix(y_true, prediction, labels=[0, 1]).ravel()
    return {
        "threshold": float(threshold),
        "accuracy": float(accuracy_score(y_true, prediction)),
        "precision": float(precision_score(y_true, prediction, zero_division=0)),
        "sensitivity": float(recall_score(y_true, prediction, zero_division=0)),
        "specificity": float(tn / (tn + fp)) if tn + fp else 0.0,
        "f1": float(f1_score(y_true, prediction, zero_division=0)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, prediction)),
        "roc_auc": float(roc_auc_score(y_true, y_prob)) if len(np.unique(y_true)) > 1 else 0.0,
        "pr_auc": float(average_precision_score(y_true, y_prob)) if len(np.unique(y_true)) > 1 else 0.0,
        "brier_score": float(brier_score_loss(y_true, y_prob)),
        "tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp),
    }


def write_predictions(path: Path, y_true: np.ndarray, y_prob: np.ndarray, threshold: float) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["index", "label", "malignant_probability", "prediction", "threshold"])
        writer.writeheader()
        for index, (label, probability) in enumerate(zip(y_true, y_prob)):
            writer.writerow({
                "index": index,
                "label": int(label),
                "malignant_probability": float(probability),
                "prediction": int(probability >= threshold),
                "threshold": float(threshold),
            })


def architecture_to_service_name(arch: str) -> str:
    if arch == "resnet50":
        return "ResNet50"
    if arch == "efficientnetb0":
        return "EfficientNet-B0"
    return "Custom CNN"


def load_profile() -> Dict:
    if CALIB_PATH.exists():
        try:
            with CALIB_PATH.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "models": {},
        "ensemble_weights": {},
        "low_quality_models": [],
        "probability_postprocess_mode": "empirical",
    }


def save_profile(profile: Dict):
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    with CALIB_PATH.open("w", encoding="utf-8") as f:
        json.dump(profile, f, ensure_ascii=True, indent=2)


def update_profile(
    arch: str,
    val_acc: float,
    val_auc: float,
    threshold: float,
    spread_factor: float,
    reference_threshold: float,
    centering_gain: float,
    std_prob: float,
):
    profile = load_profile()
    model_name = architecture_to_service_name(arch)

    profile.setdefault("models", {})[model_name] = {
        "validation_accuracy": float(val_acc),
        "validation_auc": float(val_auc),
        "threshold": float(threshold),
        "spread_factor": float(spread_factor),
        "reference_threshold": float(reference_threshold),
        "centering_gain": float(centering_gain),
        "std_probability": float(std_prob),
    }

    model_entries = profile["models"]
    scores = {}
    low_quality = []
    for name, cfg in model_entries.items():
        acc = float(cfg.get("validation_accuracy", 0.0))
        auc = float(cfg.get("validation_auc", 0.0))
        std = float(cfg.get("std_probability", 0.0))
        score = max(auc, max(acc, 0.01)) * max(std, 0.005)
        if auc < 0.58 or std < 0.01:
            score *= 0.05
            low_quality.append(name)
        scores[name] = score

    s = sum(scores.values())
    if s > 0:
        profile["ensemble_weights"] = {k: float(v / s) for k, v in scores.items()}
        profile["primary_explain_model"] = max(profile["ensemble_weights"], key=profile["ensemble_weights"].get)
    else:
        profile["ensemble_weights"] = {}

    profile["low_quality_models"] = sorted(low_quality)

    if profile["ensemble_weights"]:
        # conservative ensemble threshold around weighted average of model thresholds
        e_thr = 0.0
        for name, w in profile["ensemble_weights"].items():
            e_thr += w * float(model_entries[name].get("threshold", 0.5))
        profile["ensemble_threshold"] = float(np.clip(e_thr, 0.05, 0.95))

    profile["probability_postprocess_mode"] = "empirical"

    save_profile(profile)


def main():
    args = parse_args()
    tf.keras.utils.set_random_seed(args.seed)

    all_records = load_manifest_records(args.manifest, image_set=args.image_set)
    data = load_datasets(args.manifest, args.image_set, args.image_size, args.batch_size, args.seed, args.cache_dataset)
    print(f"Dataset loaded: train={data.train_count}, val={data.val_count}, test={data.test_count}")

    model = build_model(args.architecture, args.image_size, args.learning_rate)
    class_weight = get_class_weights(split_records(all_records)["train"])
    print(f"Class weights: {class_weight}")

    model_name = architecture_to_service_name(args.architecture)
    output_stem = args.output_stem.strip() or f"{args.architecture}_finetuned_calibrated"
    out_model = MODEL_DIR / f"{output_stem}.keras"
    run_dir = args.run_dir or PROJECT_ROOT / "experiments" / "final" / "runs" / f"{args.architecture}_full"
    run_dir.mkdir(parents=True, exist_ok=True)
    architecture_strategy = {
        "custom_cnn": {"preprocessing": "Rescaling(1/255)", "backbone": "custom", "backbone_weights": None, "backbone_trainable": True},
        "resnet50": {"preprocessing": "tf.keras.applications.resnet50.preprocess_input", "backbone": "ResNet50", "backbone_weights": "ImageNet", "backbone_trainable": False},
        "efficientnetb0": {"preprocessing": "tf.keras.applications.efficientnet.preprocess_input", "backbone": "EfficientNetB0", "backbone_weights": "ImageNet", "backbone_trainable": False},
    }[args.architecture]
    (run_dir / "config.json").write_text(
        json.dumps({
            "architecture": args.architecture,
            "manifest": str(args.manifest),
            "image_set": args.image_set,
            "seed": args.seed,
            "epochs": args.epochs,
            "batch_size": args.batch_size,
            "image_size": args.image_size,
            "learning_rate": args.learning_rate,
            "selection_split": "val",
            "threshold_selection_split": "val",
            "final_evaluation_split": "test",
            "test_time_augmentation": "none",
            "architecture_strategy": architecture_strategy,
        }, indent=2) + "\n", encoding="utf-8"
    )

    callbacks = [
        tf.keras.callbacks.EarlyStopping(monitor="val_auc", patience=args.patience, mode="max", restore_best_weights=True),
        tf.keras.callbacks.ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=args.reduce_lr_patience, min_lr=1e-6),
        tf.keras.callbacks.ModelCheckpoint(str(out_model), monitor="val_auc", mode="max", save_best_only=True),
    ]

    history = model.fit(
        data.train,
        validation_data=data.val,
        epochs=args.epochs,
        class_weight=class_weight,
        callbacks=callbacks,
        verbose=1,
    )

    val_y, val_prob = collect_predictions(model, data.val)
    threshold, val_bacc = best_threshold(val_y, val_prob)
    test_y, test_prob = collect_predictions(model, data.test)
    val_metrics = evaluate(val_y, val_prob, threshold)
    test_metrics = evaluate(test_y, test_prob, threshold)
    val_auc, val_acc = val_metrics["roc_auc"], val_metrics["accuracy"]

    std_prob = float(np.std(val_prob))
    spread_factor = float(np.clip(0.20 / max(std_prob, 1e-6), 0.5, 4.0))
    reference_threshold = float(np.clip(threshold, 0.15, 0.85))
    centering_gain = float(np.clip(0.28 / max(std_prob, 1e-3), 4.0, 14.0))

    # Promotion into the runtime calibration profile occurs only after final model selection.
    candidate_profile = {
        "model_name": model_name,
        "threshold": threshold,
        "validation_accuracy": val_acc,
        "validation_auc": val_auc,
        "spread_factor": spread_factor,
        "reference_threshold": reference_threshold,
        "centering_gain": centering_gain,
        "std_probability": std_prob,
    }
    (run_dir / "calibration_candidate.json").write_text(json.dumps(candidate_profile, indent=2) + "\n", encoding="utf-8")
    with (run_dir / "history.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        keys = list(history.history)
        writer.writerow(["epoch", *keys])
        for epoch, values in enumerate(zip(*(history.history[key] for key in keys)), start=1):
            writer.writerow([epoch, *values])
    write_predictions(run_dir / "validation_predictions.csv", val_y, val_prob, threshold)
    write_predictions(run_dir / "test_predictions.csv", test_y, test_prob, threshold)
    (run_dir / "threshold.json").write_text(json.dumps({"threshold": threshold, "selected_on": "validation", "objective": "balanced_accuracy", "validation_balanced_accuracy": val_bacc}, indent=2) + "\n", encoding="utf-8")
    (run_dir / "metrics.json").write_text(json.dumps({"validation": val_metrics, "test": test_metrics}, indent=2) + "\n", encoding="utf-8")

    summary = {
        "model_name": model_name,
        "model_path": str(out_model),
        "run_dir": str(run_dir),
        "epochs": args.epochs,
        "batch_size": args.batch_size,
        "image_size": args.image_size,
        "learning_rate": args.learning_rate,
        "manifest": str(args.manifest),
        "image_set": args.image_set,
        "cache_dataset": args.cache_dataset,
        "threshold": threshold,
        "val_balanced_accuracy": val_bacc,
        "val_accuracy": val_acc,
        "val_auc": val_auc,
        "test_accuracy": test_metrics["accuracy"],
        "test_auc": test_metrics["roc_auc"],
        "std_probability": std_prob,
        "spread_factor": spread_factor,
        "reference_threshold": reference_threshold,
        "centering_gain": centering_gain,
    }

    print("\n=== Training & Calibration Summary ===")
    for k, v in summary.items():
        print(f"{k}: {v}")

    summary_path = MODEL_DIR / f"{output_stem}_summary.json"
    with summary_path.open("w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=True, indent=2)
    (run_dir / "training.log").write_text(
        "\n".join([
            f"Final candidate run: {run_dir.name}",
            f"Architecture: {model_name}",
            f"Manifest: {args.manifest}",
            f"Image set: {args.image_set}",
            f"Seed: {args.seed}",
            f"Epoch limit: {args.epochs}",
            f"Batch size: {args.batch_size}",
            f"Input size: {args.image_size}",
            "Checkpoint selection: validation ROC-AUC",
            "Threshold selection: validation balanced accuracy",
            "Test-time augmentation: none",
            "Completion: successful; detailed epoch history is stored in history.csv.",
            "",
        ]), encoding="utf-8"
    )
    model_sha256 = hashlib.sha256(out_model.read_bytes()).hexdigest()
    (run_dir / "model_metadata.json").write_text(json.dumps({
        "version": "final-candidate",
        "architecture": args.architecture,
        "model_file": str(out_model),
        "sha256": model_sha256,
        "training_manifest": str(args.manifest),
        "seed": args.seed,
        "threshold": threshold,
        "metrics_file": str(run_dir / "metrics.json"),
    }, indent=2) + "\n", encoding="utf-8")
    print(f"Saved summary to {summary_path}")


if __name__ == "__main__":
    main()
