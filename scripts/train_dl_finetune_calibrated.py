#!/usr/bin/env python3

"""Fine-tune DL model with class weights + focal loss + TTA + threshold export.

Example:
  source venv/bin/activate
  PYTHONPATH=backend python scripts/train_dl_finetune_calibrated.py \
    --architecture custom_cnn \
    --epochs 25 \
    --batch-size 16
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Tuple

import numpy as np
import tensorflow as tf
from sklearn.metrics import accuracy_score, balanced_accuracy_score, roc_auc_score

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_ROOT = PROJECT_ROOT / "data" / "cbis_ddsm" / "processed" / "images"
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
    parser.add_argument("--tta-rounds", type=int, default=6)
    parser.add_argument("--patience", type=int, default=5)
    parser.add_argument("--reduce-lr-patience", type=int, default=2)
    parser.add_argument("--cache-dataset", action="store_true")
    parser.add_argument("--output-stem", type=str, default="")
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def _count_images(path: Path) -> int:
    return len(list(path.glob("*.png"))) + len(list(path.glob("*.jpg"))) + len(list(path.glob("*.jpeg")))


def load_datasets(image_size: int, batch_size: int, seed: int, cache_dataset: bool) -> DatasetBundle:
    train_dir = DATA_ROOT / "train"
    val_dir = DATA_ROOT / "val"
    test_dir = DATA_ROOT / "test"

    if not train_dir.exists() or not val_dir.exists() or not test_dir.exists():
        raise FileNotFoundError(f"Missing dataset folders under {DATA_ROOT}")

    common = dict(
        image_size=(image_size, image_size),
        batch_size=batch_size,
        label_mode="binary",
        color_mode="rgb",
        seed=seed,
    )

    train_ds = tf.keras.utils.image_dataset_from_directory(train_dir, shuffle=True, **common)
    val_ds = tf.keras.utils.image_dataset_from_directory(val_dir, shuffle=False, **common)
    test_ds = tf.keras.utils.image_dataset_from_directory(test_dir, shuffle=False, **common)

    autotune = tf.data.AUTOTUNE
    if cache_dataset:
        train_ds = train_ds.cache()
        val_ds = val_ds.cache()
        test_ds = test_ds.cache()
    train_ds = train_ds.prefetch(autotune)
    val_ds = val_ds.prefetch(autotune)
    test_ds = test_ds.prefetch(autotune)

    train_count = _count_images(train_dir / "benign") + _count_images(train_dir / "malignant")
    val_count = _count_images(val_dir / "benign") + _count_images(val_dir / "malignant")
    test_count = _count_images(test_dir / "benign") + _count_images(test_dir / "malignant")

    return DatasetBundle(train_ds, val_ds, test_ds, train_count, val_count, test_count)


def get_class_weights() -> Dict[int, float]:
    benign = _count_images(DATA_ROOT / "train" / "benign")
    malignant = _count_images(DATA_ROOT / "train" / "malignant")
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


def random_tta(images: tf.Tensor) -> tf.Tensor:
    x = tf.image.random_flip_left_right(images)
    x = tf.image.random_flip_up_down(x)
    x = tf.image.random_brightness(x, max_delta=0.08)
    x = tf.image.random_contrast(x, lower=0.9, upper=1.1)
    return tf.clip_by_value(x, 0.0, 255.0)


def collect_predictions_with_tta(model: tf.keras.Model, dataset: tf.data.Dataset, rounds: int) -> Tuple[np.ndarray, np.ndarray]:
    y_true, y_prob = [], []
    for x, y in dataset:
        probs = []
        for _ in range(max(rounds, 1)):
            x_aug = random_tta(x)
            probs.append(model.predict(x_aug, verbose=0).ravel())
        p = np.mean(np.stack(probs, axis=0), axis=0)
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

    data = load_datasets(args.image_size, args.batch_size, args.seed, args.cache_dataset)
    print(f"Dataset loaded: train={data.train_count}, val={data.val_count}, test={data.test_count}")

    model = build_model(args.architecture, args.image_size, args.learning_rate)
    class_weight = get_class_weights()
    print(f"Class weights: {class_weight}")

    model_name = architecture_to_service_name(args.architecture)
    output_stem = args.output_stem.strip() or f"{args.architecture}_finetuned_calibrated"
    out_model = MODEL_DIR / f"{output_stem}.keras"

    callbacks = [
        tf.keras.callbacks.EarlyStopping(monitor="val_auc", patience=args.patience, mode="max", restore_best_weights=True),
        tf.keras.callbacks.ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=args.reduce_lr_patience, min_lr=1e-6),
        tf.keras.callbacks.ModelCheckpoint(str(out_model), monitor="val_auc", mode="max", save_best_only=True),
    ]

    model.fit(
        data.train,
        validation_data=data.val,
        epochs=args.epochs,
        class_weight=class_weight,
        callbacks=callbacks,
        verbose=1,
    )

    val_y, val_prob = collect_predictions(model, data.val)
    threshold, val_bacc = best_threshold(val_y, val_prob)
    val_auc = float(roc_auc_score(val_y, val_prob)) if len(np.unique(val_y)) > 1 else 0.0
    val_acc = float(accuracy_score(val_y, (val_prob >= threshold).astype(np.int32)))

    test_y, test_prob_tta = collect_predictions_with_tta(model, data.test, rounds=args.tta_rounds)
    test_auc = float(roc_auc_score(test_y, test_prob_tta)) if len(np.unique(test_y)) > 1 else 0.0
    test_acc = float(accuracy_score(test_y, (test_prob_tta >= threshold).astype(np.int32)))

    std_prob = float(np.std(val_prob))
    spread_factor = float(np.clip(0.20 / max(std_prob, 1e-6), 0.5, 4.0))
    reference_threshold = float(np.clip(threshold, 0.15, 0.85))
    centering_gain = float(np.clip(0.28 / max(std_prob, 1e-3), 4.0, 14.0))

    update_profile(
        args.architecture,
        val_acc=val_acc,
        val_auc=val_auc,
        threshold=threshold,
        spread_factor=spread_factor,
        reference_threshold=reference_threshold,
        centering_gain=centering_gain,
        std_prob=std_prob,
    )

    summary = {
        "model_name": model_name,
        "model_path": str(out_model),
        "calibration_profile": str(CALIB_PATH),
        "epochs": args.epochs,
        "batch_size": args.batch_size,
        "image_size": args.image_size,
        "learning_rate": args.learning_rate,
        "tta_rounds": args.tta_rounds,
        "cache_dataset": args.cache_dataset,
        "threshold": threshold,
        "val_balanced_accuracy": val_bacc,
        "val_accuracy": val_acc,
        "val_auc": val_auc,
        "test_tta_accuracy": test_acc,
        "test_tta_auc": test_auc,
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
    print(f"Saved summary to {summary_path}")


if __name__ == "__main__":
    main()
