#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import joblib
import numpy as np
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, roc_auc_score

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_ROOT = PROJECT_ROOT / "data" / "cbis_ddsm" / "processed" / "images"
OUT_PATH = PROJECT_ROOT / "models" / "deep_learning" / "dl_image_rf_20260404.pkl"
SUMMARY_PATH = PROJECT_ROOT / "models" / "deep_learning" / "dl_image_rf_20260404_summary.json"
CACHE_DIR = PROJECT_ROOT / "models" / "deep_learning" / "feature_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def parse_args():
    parser = argparse.ArgumentParser(description="Train RF image baseline on handcrafted image features")
    parser.add_argument("--n-estimators", type=int, default=700)
    parser.add_argument("--cv", type=int, default=5)
    parser.add_argument("--max-train-per-class", type=int, default=0)
    parser.add_argument("--max-val-per-class", type=int, default=0)
    parser.add_argument("--max-test-per-class", type=int, default=0)
    parser.add_argument("--cache", action="store_true")
    return parser.parse_args()


def image_features(path: Path) -> np.ndarray:
    img = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise ValueError(f"cannot read image: {path}")
    img = cv2.resize(img, (224, 224), interpolation=cv2.INTER_AREA)
    arr = img.astype(np.float32)

    hist = cv2.calcHist([img], [0], None, [24], [0, 256]).reshape(-1)
    hist = hist / max(float(hist.sum()), 1.0)

    p = np.percentile(arr, [5, 25, 50, 75, 95]).astype(np.float32)
    lap_var = float(cv2.Laplacian(arr, cv2.CV_32F).var())
    gx = cv2.Sobel(arr, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(arr, cv2.CV_32F, 0, 1, ksize=3)
    grad_mag = np.sqrt(gx * gx + gy * gy)
    grad_mean = float(np.mean(grad_mag))

    probs = np.clip(hist, 1e-12, 1.0)
    entropy = float(-np.sum(probs * np.log(probs)))

    basics = np.array(
        [
            float(np.mean(arr)),
            float(np.std(arr)),
            float(np.min(arr)),
            float(np.max(arr)),
            lap_var,
            grad_mean,
            entropy,
        ],
        dtype=np.float32,
    )

    return np.concatenate([basics, p, hist.astype(np.float32)], axis=0)


def _cache_path(split: str, max_per_class: int) -> Path:
    suffix = f"{split}_{max_per_class if max_per_class > 0 else 'all'}.npz"
    return CACHE_DIR / suffix


def load_split(split: str, *, max_per_class: int = 0, use_cache: bool = False):
    cache_path = _cache_path(split, max_per_class)
    if use_cache and cache_path.exists():
        print(f"Loading cached features for {split} from {cache_path}")
        payload = np.load(cache_path)
        return payload["x"], payload["y"]

    x, y = [], []
    print(f"Extracting features for split={split}, max_per_class={max_per_class or 'all'}")
    for label, cls in [(0, "benign"), (1, "malignant")]:
        folder = DATA_ROOT / split / cls
        paths = sorted(folder.glob("*.png"))
        if max_per_class > 0:
            paths = paths[:max_per_class]
        for idx, p in enumerate(paths, start=1):
            try:
                x.append(image_features(p))
                y.append(label)
            except Exception:
                continue
            if idx % 25 == 0 or idx == len(paths):
                print(f"  {split}/{cls}: {idx}/{len(paths)}")
    x_arr = np.asarray(x, dtype=np.float32)
    y_arr = np.asarray(y, dtype=np.int32)
    if use_cache:
        np.savez_compressed(cache_path, x=x_arr, y=y_arr)
        print(f"Saved feature cache to {cache_path}")
    return x_arr, y_arr


def main():
    args = parse_args()
    x_train, y_train = load_split("train", max_per_class=args.max_train_per_class, use_cache=args.cache)
    x_val, y_val = load_split("val", max_per_class=args.max_val_per_class, use_cache=args.cache)
    x_test, y_test = load_split("test", max_per_class=args.max_test_per_class, use_cache=args.cache)

    print("train", x_train.shape, "val", x_val.shape, "test", x_test.shape)

    base = RandomForestClassifier(
        n_estimators=args.n_estimators,
        max_depth=None,
        min_samples_leaf=2,
        class_weight="balanced_subsample",
        random_state=42,
        n_jobs=-1,
    )
    model = CalibratedClassifierCV(base, method="sigmoid", cv=args.cv)
    model.fit(x_train, y_train)

    p_val = model.predict_proba(x_val)[:, 1]
    p_test = model.predict_proba(x_test)[:, 1]

    val_auc = float(roc_auc_score(y_val, p_val)) if len(np.unique(y_val)) > 1 else 0.0
    test_auc = float(roc_auc_score(y_test, p_test)) if len(np.unique(y_test)) > 1 else 0.0

    best_thr = 0.5
    best_acc = -1.0
    for t in np.linspace(0.05, 0.95, 181):
        acc = float(accuracy_score(y_val, (p_val >= t).astype(np.int32)))
        if acc > best_acc:
            best_acc = acc
            best_thr = float(t)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, OUT_PATH)

    summary = {
        "model": str(OUT_PATH),
        "n_estimators": args.n_estimators,
        "cv": args.cv,
        "max_train_per_class": args.max_train_per_class,
        "max_val_per_class": args.max_val_per_class,
        "max_test_per_class": args.max_test_per_class,
        "threshold": best_thr,
        "val_auc": val_auc,
        "test_auc": test_auc,
        "val_accuracy": best_acc,
        "val_prob_quantiles": [float(v) for v in np.quantile(p_val, [0.01, 0.1, 0.25, 0.5, 0.75, 0.9, 0.99])],
        "test_prob_quantiles": [float(v) for v in np.quantile(p_test, [0.01, 0.1, 0.25, 0.5, 0.75, 0.9, 0.99])],
    }
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, ensure_ascii=True), encoding="utf-8")

    print(json.dumps(summary, indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
