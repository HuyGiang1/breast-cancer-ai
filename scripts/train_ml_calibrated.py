#!/usr/bin/env python3

from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
from sklearn.calibration import CalibratedClassifierCV
from sklearn.datasets import load_breast_cancer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODEL_DIR = PROJECT_ROOT / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)


def build_models(random_state: int = 42):
    lr_base = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            (
                "lr",
                LogisticRegression(
                    max_iter=5000,
                    solver="liblinear",
                    random_state=random_state,
                    class_weight="balanced",
                ),
            ),
        ]
    )

    rf_base = RandomForestClassifier(
        n_estimators=600,
        max_depth=None,
        min_samples_leaf=2,
        class_weight="balanced_subsample",
        random_state=random_state,
        n_jobs=-1,
    )

    models = {
        "Logistic Regression": CalibratedClassifierCV(lr_base, method="sigmoid", cv=5),
        "Random Forest": CalibratedClassifierCV(rf_base, method="sigmoid", cv=5),
    }
    return models


def main() -> None:
    x, y = load_breast_cancer(return_X_y=True)
    # Convert to project convention: 1 = malignant, 0 = benign
    y_malignant = (y == 0).astype(int)

    x_train, x_test, y_train, y_test = train_test_split(
        x,
        y_malignant,
        test_size=0.2,
        random_state=42,
        stratify=y_malignant,
    )

    models = build_models(random_state=42)
    report = {}

    for name, model in models.items():
        model.fit(x_train, y_train)
        probs = model.predict_proba(x_test)[:, 1]
        auc = float(roc_auc_score(y_test, probs))
        q = np.quantile(probs, [0.01, 0.1, 0.25, 0.5, 0.75, 0.9, 0.99])

        file_name = (
            "wisconsin_logistic_regression_20260404_retrained.pkl"
            if name == "Logistic Regression"
            else "wisconsin_random_forest_20260404_retrained.pkl"
        )
        joblib.dump(model, MODEL_DIR / file_name)

        report[name] = {
            "roc_auc": auc,
            "probability_quantiles": [float(v) for v in q],
            "saved_model": file_name,
        }

    report_path = MODEL_DIR / "ml_retrain_report_20260404.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("ML retraining complete")
    for name, info in report.items():
        print(name, "AUC=", round(info["roc_auc"], 4), "model=", info["saved_model"])
        print(" quantiles=", [round(v, 4) for v in info["probability_quantiles"]])


if __name__ == "__main__":
    main()
