#!/usr/bin/env python3

import csv
import glob
import json
import os
import urllib.parse
import urllib.request
from pathlib import Path

API = "http://127.0.0.1:8000/api/v1"


def post_json(url: str, payload: dict) -> dict:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=180) as resp:
        return json.loads(resp.read().decode())


def post_image(url: str, image_path: str) -> dict:
    boundary = "----spreadcheck"
    img = Path(image_path)
    data = img.read_bytes()
    body = (
        f"--{boundary}\r\n"
        f"Content-Disposition: form-data; name=\"file\"; filename=\"{img.name}\"\r\n"
        "Content-Type: image/png\r\n\r\n"
    ).encode() + data + b"\r\n" + f"--{boundary}--\r\n".encode()

    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    with urllib.request.urlopen(req, timeout=180) as resp:
        return json.loads(resp.read().decode())


def eval_ml(model_name: str):
    probs = []
    print(f"\nML {model_name}")
    for path in sorted(glob.glob("data/test_samples/*.csv")):
        with open(path, newline="") as f:
            row = next(csv.DictReader(f))
        payload = {k: float(v) for k, v in row.items()}
        out = post_json(f"{API}/predict/?model_name={urllib.parse.quote(model_name)}", payload)
        p = float(out["probability"])
        probs.append(p)
        print(f"{os.path.basename(path):35} {out['diagnosis']:10} {p:.4f}")
    print("range", round(min(probs), 4), round(max(probs), 4), "avg", round(sum(probs)/len(probs), 4))


def eval_dl(model_name: str):
    probs = []
    benign = sorted(glob.glob("data/cbis_ddsm/processed/images/test/benign/*.png"))[:8]
    malignant = sorted(glob.glob("data/cbis_ddsm/processed/images/test/malignant/*.png"))[:8]
    print(f"\nDL {model_name}")
    for path in benign + malignant:
        out = post_image(f"{API}/predict/image/?model_name={urllib.parse.quote(model_name)}", path)
        p = float(out["probability"])
        probs.append(p)
        print(f"{os.path.basename(path)[:30]:30} {out['diagnosis']:10} {p:.4f}")
    print("range", round(min(probs), 4), round(max(probs), 4), "avg", round(sum(probs)/len(probs), 4))


if __name__ == "__main__":
    eval_ml("Logistic Regression")
    eval_ml("Random Forest")
    eval_dl("Custom CNN")
    eval_dl("ResNet50")
    eval_dl("Ensemble")
