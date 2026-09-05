#!/usr/bin/env python3
"""Offline lightweight verification of final application API flows."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient
from sklearn.datasets import load_breast_cancer

from app.main import app
from app.services.final_ml_runtime import API_TO_WDBC_FEATURE


ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    client = TestClient(app)
    assert client.get("/healthz").json()["status"] == "ok"
    ready = client.get("/readyz").json()
    assert ready["final_ml"] == "research_demo" and ready["final_dl"] == "research_demo"
    status = client.get("/api/v1/models/final/status/").json()
    assert status["clinical_use"] is False
    assert status["ml"]["artifact_verified"] and status["dl"]["artifact_verified"]
    assert client.get("/api/v1/research/evidence/").json()["ml_candidate"] == "Logistic Regression"

    row = load_breast_cancer().data[120]
    payload = {name: float(row[index]) for index, name in enumerate(API_TO_WDBC_FEATURE)}
    ml = client.post("/api/v1/predict/", json=payload)
    assert ml.status_code == 200 and ml.json()["decision_threshold"] == 0.36
    assert client.post("/api/v1/predict/", json={}).status_code == 422

    image = next((ROOT / "data" / "cbis_ddsm" / "processed" / "images" / "test" / "benign").glob("*.png"))
    dl = client.post("/api/v1/predict/image/", files={"file": (image.name, image.read_bytes(), "image/png")})
    body = dl.json()
    assert dl.status_code == 200 and body["decision_threshold"] == 0.515
    assert body["decision_probability_space"] == "raw" and body["calibration"] == "Platt"
    assert client.post("/api/v1/predict/image/", files={"file": ("broken.png", b"not-a-png", "image/png")}).status_code == 400
    print("FINAL APPLICATION VERIFICATION: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
