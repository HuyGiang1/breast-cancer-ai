import numpy as np
import tensorflow as tf
from pathlib import Path
from PIL import Image
from sklearn.metrics import roc_auc_score

files = [
    "custom_cnn_retrained_balanced.keras",
    "custom_cnn_finetuned_calibrated.keras",
    "custom_cnn_v2_finetuned_roi.keras",
    "custom_cnn_best.keras",
]

x = []
y = []
for lbl, cls in [(0, "benign"), (1, "malignant")]:
    folder = Path("data/cbis_ddsm/processed/images/val") / cls
    for f in sorted(folder.glob("*.png"))[:180]:
        arr = np.asarray(Image.open(f).convert("RGB").resize((224, 224)), dtype=np.float32) / 255.0
        x.append(arr)
        y.append(lbl)

x = np.stack(x)
y = np.asarray(y)
print("samples", x.shape)

for fn in files:
    p = Path("models/deep_learning") / fn
    if not p.exists():
        print(fn, "MISSING")
        continue

    m = tf.keras.models.load_model(p)
    pred = np.clip(m.predict(x, verbose=0).reshape(-1), 1e-6, 1 - 1e-6)
    auc = max(float(roc_auc_score(y, pred)), float(roc_auc_score(y, 1 - pred)))
    print(
        fn,
        "std",
        round(float(np.std(pred)), 6),
        "auc",
        round(auc, 4),
        "min",
        round(float(pred.min()), 4),
        "max",
        round(float(pred.max()), 4),
    )
