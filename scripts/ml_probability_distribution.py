#!/usr/bin/env python3

from sklearn.datasets import load_breast_cancer
import numpy as np
from app.services.prediction import prediction_service


def main() -> None:
    X, y = load_breast_cancer(return_X_y=True)
    scaler = prediction_service.scaler
    Xs = scaler.transform(X) if scaler is not None else X

    print("y distribution (0=malignant, 1=benign):", {0: int((y == 0).sum()), 1: int((y == 1).sum())})

    for name, model in prediction_service.models.items():
        probs = model.predict_proba(Xs)
        classes = [int(c) for c in model.classes_]
        mal_idx = classes.index(0) if 0 in classes else 0

        p = probs[:, mal_idx]
        q = np.quantile(p, [0.01, 0.1, 0.25, 0.5, 0.75, 0.9, 0.99])

        print("\n", name)
        print(" classes=", classes)
        print(" malignant_prob_quantiles=", [round(float(v), 4) for v in q])
        print(" mid-range(0.2-0.8)=", int(((p >= 0.2) & (p <= 0.8)).sum()), "/", len(p))
        print(" very_low(<0.1)=", int((p < 0.1).sum()), " very_high(>0.9)=", int((p > 0.9).sum()))


if __name__ == "__main__":
    main()
