#!/usr/bin/env python3

from sklearn.datasets import load_breast_cancer
import numpy as np
from app.services.prediction import prediction_service


def main() -> None:
    data = load_breast_cancer()
    X = data.data
    y = data.target  # sklearn: 0=malignant, 1=benign

    scaler = prediction_service.scaler
    if scaler is not None:
        Xs = scaler.transform(X)
    else:
        Xs = X

    print("dataset:", X.shape, "targets:", {0: int(np.sum(y == 0)), 1: int(np.sum(y == 1))})

    for name, model in prediction_service.models.items():
        probs = model.predict_proba(Xs)
        classes = getattr(model, "classes_", None)
        classes_list = list(classes) if classes is not None else [0, 1]

        # Mean predicted proba for each class by true class group
        row = [f"model={name}", f"classes={classes_list}"]
        for cls_idx, cls_label in enumerate(classes_list):
            mean_on_true_mal = float(np.mean(probs[y == 0, cls_idx]))
            mean_on_true_ben = float(np.mean(probs[y == 1, cls_idx]))
            row.append(
                f"P(class={cls_label}) mean true_mal={mean_on_true_mal:.4f}, true_ben={mean_on_true_ben:.4f}"
            )

        pred = model.predict(Xs)
        acc = float(np.mean(pred == y))
        row.append(f"acc={acc:.4f}")
        print(" | ".join(row))


if __name__ == "__main__":
    main()
