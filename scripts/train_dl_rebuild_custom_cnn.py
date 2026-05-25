#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import tensorflow as tf
from sklearn.metrics import accuracy_score, balanced_accuracy_score, roc_auc_score

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_ROOT = PROJECT_ROOT / "data" / "cbis_ddsm" / "processed" / "images"
MODEL_DIR = PROJECT_ROOT / "models" / "deep_learning"
MODEL_DIR.mkdir(parents=True, exist_ok=True)
CALIB_PATH = MODEL_DIR / "calibration_profile.json"


def parse_args():
    parser = argparse.ArgumentParser(description="Rebuild custom CNN for breast cancer image prediction")
    parser.add_argument("--epochs", type=int, default=18)
    parser.add_argument("--batch-size", type=int, default=24)
    parser.add_argument("--image-size", type=int, default=224)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def count_images(path: Path) -> int:
    return len(list(path.glob("*.png"))) + len(list(path.glob("*.jpg"))) + len(list(path.glob("*.jpeg")))


def load_datasets(image_size=224, batch_size=24, seed=42):
    common = dict(
        image_size=(image_size, image_size),
        batch_size=batch_size,
        label_mode="binary",
        color_mode="rgb",
        seed=seed,
    )

    train_dir = DATA_ROOT / "train"
    val_dir = DATA_ROOT / "val"
    test_dir = DATA_ROOT / "test"

    train_ds = tf.keras.utils.image_dataset_from_directory(train_dir, shuffle=True, **common)
    val_ds = tf.keras.utils.image_dataset_from_directory(val_dir, shuffle=False, **common)
    test_ds = tf.keras.utils.image_dataset_from_directory(test_dir, shuffle=False, **common)

    autotune = tf.data.AUTOTUNE
    train_ds = train_ds.prefetch(autotune)
    val_ds = val_ds.prefetch(autotune)
    test_ds = test_ds.prefetch(autotune)

    train_b = count_images(train_dir / "benign")
    train_m = count_images(train_dir / "malignant")
    return train_ds, val_ds, test_ds, train_b, train_m


def build_model(image_size=224):
    inp = tf.keras.Input(shape=(image_size, image_size, 3), name="image")

    aug = tf.keras.Sequential(
        [
            tf.keras.layers.RandomFlip("horizontal"),
            tf.keras.layers.RandomRotation(0.03),
            tf.keras.layers.RandomZoom(0.08),
            tf.keras.layers.RandomContrast(0.08),
        ],
        name="augment",
    )

    x = aug(inp)
    x = tf.keras.layers.Rescaling(1.0 / 255.0)(x)

    for filters in [32, 64, 128, 192]:
        x = tf.keras.layers.Conv2D(filters, 3, padding="same", use_bias=False)(x)
        x = tf.keras.layers.BatchNormalization()(x)
        x = tf.keras.layers.ReLU()(x)
        x = tf.keras.layers.Conv2D(filters, 3, padding="same", use_bias=False)(x)
        x = tf.keras.layers.BatchNormalization()(x)
        x = tf.keras.layers.ReLU()(x)
        x = tf.keras.layers.MaxPooling2D()(x)
        x = tf.keras.layers.Dropout(0.12)(x)

    x = tf.keras.layers.GlobalAveragePooling2D()(x)
    x = tf.keras.layers.Dense(192, activation="relu")(x)
    x = tf.keras.layers.Dropout(0.35)(x)
    x = tf.keras.layers.Dense(64, activation="relu")(x)
    x = tf.keras.layers.Dropout(0.20)(x)
    out = tf.keras.layers.Dense(1, activation="sigmoid", name="malignant_probability")(x)

    model = tf.keras.Model(inp, out, name="custom_cnn_rebuild")
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
        loss=tf.keras.losses.BinaryCrossentropy(label_smoothing=0.02),
        metrics=[
            tf.keras.metrics.BinaryAccuracy(name="accuracy"),
            tf.keras.metrics.AUC(name="auc"),
            tf.keras.metrics.Precision(name="precision"),
            tf.keras.metrics.Recall(name="recall"),
        ],
    )
    return model


def collect_probs(model, ds):
    ys, ps = [], []
    for x, y in ds:
        p = model.predict(x, verbose=0).reshape(-1)
        ys.extend(y.numpy().reshape(-1).tolist())
        ps.extend(p.tolist())
    return np.asarray(ys, dtype=np.int32), np.asarray(ps, dtype=np.float32)


def best_threshold(y_true, y_prob):
    best_t, best_bacc = 0.5, -1.0
    for t in np.linspace(0.05, 0.95, 181):
        pred = (y_prob >= t).astype(np.int32)
        bacc = balanced_accuracy_score(y_true, pred)
        if bacc > best_bacc:
            best_bacc = float(bacc)
            best_t = float(t)
    return best_t, best_bacc


def load_profile() -> dict:
    if CALIB_PATH.exists():
        try:
            return json.loads(CALIB_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"models": {}, "ensemble_weights": {}, "low_quality_models": []}


def save_profile(profile: dict):
    CALIB_PATH.write_text(json.dumps(profile, indent=2, ensure_ascii=True), encoding="utf-8")


def main():
    args = parse_args()
    tf.keras.utils.set_random_seed(args.seed)

    train_ds, val_ds, test_ds, train_b, train_m = load_datasets(
        image_size=args.image_size,
        batch_size=args.batch_size,
        seed=args.seed,
    )
    print(f"Train class counts benign={train_b} malignant={train_m}")

    total = max(train_b + train_m, 1)
    class_weight = {
        0: total / max(2 * train_b, 1),
        1: total / max(2 * train_m, 1),
    }

    model = build_model(image_size=args.image_size)

    model_path = MODEL_DIR / "custom_cnn_retrained_balanced.keras"
    callbacks = [
        tf.keras.callbacks.EarlyStopping(monitor="val_auc", mode="max", patience=5, restore_best_weights=True),
        tf.keras.callbacks.ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=2, min_lr=1e-6),
        tf.keras.callbacks.ModelCheckpoint(str(model_path), monitor="val_auc", mode="max", save_best_only=True),
    ]

    model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=args.epochs,
        class_weight=class_weight,
        callbacks=callbacks,
        verbose=1,
    )

    # Load best checkpoint
    model = tf.keras.models.load_model(model_path)

    yv, pv = collect_probs(model, val_ds)
    yt, pt = collect_probs(model, test_ds)

    thr, val_bacc = best_threshold(yv, pv)

    val_auc = float(roc_auc_score(yv, pv)) if len(np.unique(yv)) > 1 else 0.0
    test_auc = float(roc_auc_score(yt, pt)) if len(np.unique(yt)) > 1 else 0.0
    val_acc = float(accuracy_score(yv, (pv >= thr).astype(np.int32)))
    test_acc = float(accuracy_score(yt, (pt >= thr).astype(np.int32)))

    def q(a):
        return [float(v) for v in np.quantile(a, [0.01, 0.1, 0.25, 0.5, 0.75, 0.9, 0.99])]

    q_b = q(pt[yt == 0]) if np.any(yt == 0) else []
    q_m = q(pt[yt == 1]) if np.any(yt == 1) else []

    profile = load_profile()
    profile.setdefault("models", {})["Custom CNN"] = {
        "validation_accuracy": val_acc,
        "threshold": thr,
        "spread_factor": 1.0,
        "reference_threshold": thr,
        "centering_gain": 1.0,
        "std_probability": float(np.std(pv)),
    }

    # Weight by val AUC so ensemble prioritizes strongest model.
    scores = {}
    for name, cfg in profile["models"].items():
        scores[name] = float(cfg.get("validation_accuracy", 0.1))
    s = sum(scores.values())
    if s > 0:
        profile["ensemble_weights"] = {k: float(v / s) for k, v in scores.items()}
        profile["primary_explain_model"] = max(profile["ensemble_weights"], key=profile["ensemble_weights"].get)
    profile["ensemble_threshold"] = thr
    save_profile(profile)

    summary = {
        "model_path": str(model_path),
        "epochs": args.epochs,
        "batch_size": args.batch_size,
        "image_size": args.image_size,
        "threshold": thr,
        "val_auc": val_auc,
        "test_auc": test_auc,
        "val_bacc": val_bacc,
        "val_acc": val_acc,
        "test_acc": test_acc,
        "test_prob_quantiles_benign": q_b,
        "test_prob_quantiles_malignant": q_m,
    }

    out_summary = MODEL_DIR / "custom_cnn_retrained_balanced_summary.json"
    out_summary.write_text(json.dumps(summary, indent=2, ensure_ascii=True), encoding="utf-8")

    print("DL retraining complete")
    print(json.dumps(summary, indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
