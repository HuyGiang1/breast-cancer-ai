#!/usr/bin/env python3

import numpy as np
from pathlib import Path
from PIL import Image
import tensorflow as tf
from sklearn.metrics import roc_auc_score


def main():
    root = Path("models/deep_learning")
    files = sorted(root.glob("*.keras"))

    x = []
    y = []
    for lbl, cls in [(0, "benign"), (1, "malignant")]:
        for p in sorted((Path("data/cbis_ddsm/processed/images/val") / cls).glob("*.png"))[:220]:
            arr = np.asarray(Image.open(p).convert("RGB").resize((224, 224)), dtype=np.float32)
            x.append(arr)
            y.append(lbl)

    x = np.stack(x)
    y = np.asarray(y)
    print("samples", x.shape)

    best_name = None
    best_score = -1.0

    for f in files:
        try:
            m = tf.keras.models.load_model(f)

            p_norm = m.predict(x / 255.0, verbose=0).reshape(-1)
            p_resnet = m.predict(tf.keras.applications.resnet50.preprocess_input(x.copy()), verbose=0).reshape(-1)

            def eval_prob(p):
                p = np.clip(p, 1e-6, 1 - 1e-6)
                auc_raw = float(roc_auc_score(y, p))
                auc_inv = float(roc_auc_score(y, 1.0 - p))
                auc = max(auc_raw, auc_inv)
                std = float(np.std(p))
                return std, auc

            s_norm = eval_prob(p_norm)
            s_res = eval_prob(p_resnet)
            pick = "norm" if s_norm[1] >= s_res[1] else "resnet"
            chosen = s_norm if pick == "norm" else s_res
            score = chosen[1] * (0.4 + chosen[0])

            print(f"{f.name:42} pick={pick:7} std={chosen[0]:.4f} auc={chosen[1]:.4f} score={score:.4f}")

            if score > best_score:
                best_score = score
                best_name = f.name
        except Exception as e:
            print(f"{f.name} ERROR {e}")

    print("BEST", best_name, best_score)


if __name__ == "__main__":
    main()
