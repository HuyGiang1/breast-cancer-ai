#!/usr/bin/env python3
"""Measure local final-runtime API latency; it is not a universal production benchmark."""

from __future__ import annotations

import csv
import json
import os
import platform
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

import sklearn
import tensorflow as tf
from fastapi.testclient import TestClient
from sklearn.datasets import load_breast_cancer

# Keep the benchmark self-contained and independent from optional external advisers.
os.environ["AI_ADVISOR_PROVIDER"] = "local"
os.environ.setdefault("DL_PRELOAD_ON_STARTUP", "true")

from app.main import app
from app.services.final_ml_runtime import API_TO_WDBC_FEATURE

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_JSON = ROOT / "experiments" / "final" / "system_benchmark.json"
OUTPUT_CSV = ROOT / "experiments" / "final" / "system_benchmark.csv"
WARMUP_COUNT = 1
MEASUREMENT_COUNT = 5


def summarize(name: str, operation: Callable[[], None]) -> dict[str, object]:
    for _ in range(WARMUP_COUNT):
        operation()
    values = []
    for _ in range(MEASUREMENT_COUNT):
        started = time.perf_counter()
        operation()
        values.append((time.perf_counter() - started) * 1000)
    ordered = sorted(values)
    return {
        "operation": name,
        "count": MEASUREMENT_COUNT,
        "warmup_count": WARMUP_COUNT,
        "success_rate": 1.0,
        "mean_ms": statistics.fmean(values),
        "median_ms": statistics.median(values),
        "p95_ms": ordered[max(0, int(len(ordered) * 0.95 + 0.999999) - 1)],
        "min_ms": min(values),
        "max_ms": max(values),
    }


def require_success(response, label: str) -> None:
    if response.status_code >= 400:
        raise RuntimeError(f"{label} failed with {response.status_code}: {response.text}")


def main() -> int:
    image_root = ROOT / "data" / "cbis_ddsm" / "processed" / "images" / "test"
    benign_image = next((image_root / "benign").glob("*.png"), None)
    malignant_image = next((image_root / "malignant").glob("*.png"), None)
    if benign_image is None or malignant_image is None:
        raise RuntimeError("Representative local CBIS test images are required for the final DL benchmark.")

    row = load_breast_cancer().data[120]
    ml_payload = {name: float(row[index]) for index, name in enumerate(API_TO_WDBC_FEATURE)}
    records: list[dict[str, object]] = []
    with TestClient(app) as client:
        records.append(summarize("healthz", lambda: require_success(client.get("/healthz"), "healthz")))
        records.append(summarize("readyz", lambda: require_success(client.get("/readyz"), "readyz")))
        records.append(summarize("final_model_status", lambda: require_success(client.get("/api/v1/models/final/status/"), "model status")))
        records.append(summarize("research_evidence", lambda: require_success(client.get("/api/v1/research/evidence/"), "research evidence")))
        records.append(summarize("ml_inference", lambda: require_success(client.post("/api/v1/predict/", json=ml_payload), "ML inference")))

        def dl_request(image: Path, label: str) -> None:
            with image.open("rb") as handle:
                response = client.post("/api/v1/predict/image/", files={"file": (image.name, handle.read(), "image/png")})
            require_success(response, label)

        first_started = time.perf_counter()
        dl_request(benign_image, "DL first request")
        first_elapsed = (time.perf_counter() - first_started) * 1000
        records.append({
            "operation": "dl_inference_first_request",
            "count": 1,
            "warmup_count": 0,
            "success_rate": 1.0,
            "mean_ms": first_elapsed,
            "median_ms": first_elapsed,
            "p95_ms": first_elapsed,
            "min_ms": first_elapsed,
            "max_ms": first_elapsed,
        })
        records.append(summarize("dl_inference_warm_benign", lambda: dl_request(benign_image, "DL benign inference")))
        records.append(summarize("dl_inference_warm_malignant", lambda: dl_request(malignant_image, "DL malignant inference")))

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "local research/demo runtime; do not interpret as universal production latency",
        "environment": {
            "os": platform.platform(),
            "architecture": platform.machine(),
            "python": platform.python_version(),
            "tensorflow": tf.__version__,
            "scikit_learn": sklearn.__version__,
        },
        "results": records,
    }
    OUTPUT_JSON.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    with OUTPUT_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
    print("FINAL SYSTEM BENCHMARK: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
