#!/usr/bin/env python3
"""Verify the versioned local production contract without starting containers."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "models" / "model_registry.example.json"
SOURCE_SNAPSHOT = ROOT / "experiments" / "final" / "FINAL_RESULTS_SNAPSHOT.json"
PACKAGED_SNAPSHOT = ROOT / "backend" / "app" / "static" / "final_results_snapshot.json"
CALIBRATION = ROOT / "models" / "calibration" / "efficientnet_b0_platt_final_seed42.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tracked(pattern: str) -> list[str]:
    output = subprocess.run(["git", "ls-files", pattern], cwd=ROOT, check=True, capture_output=True, text=True).stdout
    return [line for line in output.splitlines() if line]


def main() -> int:
    failures: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            failures.append(message)

    require(SOURCE_SNAPSHOT.is_file() and PACKAGED_SNAPSHOT.is_file(), "Final research snapshot is missing.")
    if SOURCE_SNAPSHOT.is_file() and PACKAGED_SNAPSHOT.is_file():
        require(sha256(SOURCE_SNAPSHOT) == sha256(PACKAGED_SNAPSHOT), "Packaged research snapshot differs from frozen source.")

    try:
        registry = {entry["id"]: entry for entry in json.loads(REGISTRY.read_text(encoding="utf-8"))["models"]}
        ml = registry["wdbc-logistic-regression-v1"]
        dl = registry["cbis-efficientnetb0-full-v1"]
        calibration = json.loads(CALIBRATION.read_text(encoding="utf-8"))
        require(ml["sha256"] == "15a67b8580ba8729eebce9dd1330413905e7caa6ad2a022214769698e8b84755", "ML SHA-256 contract mismatch.")
        require(dl["sha256"] == "dce9a5230afe1f1e4a8c0e908cd8467ae1b6526f3667e555c3a7db3c5f2f168b", "DL SHA-256 contract mismatch.")
        require(float(ml["decision"]["threshold"]) == 0.36 and ml["decision"]["threshold_probability_space"] == "raw", "ML raw threshold contract mismatch.")
        require(float(dl["decision"]["threshold"]) == 0.515 and dl["decision"]["threshold_probability_space"] == "raw", "DL raw threshold contract mismatch.")
        require(calibration["method"] == "platt_logistic_regression" and calibration["decision_probability_space"] == "raw", "Frozen Platt calibration contract mismatch.")
        require(sha256(CALIBRATION) == dl["calibration"]["sha256"], "Frozen Platt calibration SHA mismatch.")
    except (OSError, KeyError, ValueError, json.JSONDecodeError) as exc:
        failures.append(f"Registry/calibration validation failed: {exc}")

    ignore = subprocess.run(["git", "check-ignore", "runtime_models/sentinel"], cwd=ROOT, capture_output=True, text=True)
    require(ignore.returncode == 0, "runtime_models is not ignored by Git.")
    for pattern, label in (("*.keras", ".keras"), ("*.joblib", ".joblib"), (".env", ".env"), ("*.db", "SQLite DB")):
        require(not tracked(pattern), f"Tracked {label} file(s): {tracked(pattern)}")
    require(not tracked("data/cbis_ddsm/**"), "Raw CBIS dataset files are tracked.")

    dockerfile = ROOT / "backend" / "Dockerfile"
    compose = ROOT / "docker-compose.yml"
    require(dockerfile.is_file() and compose.is_file(), "Docker packaging files are missing.")
    if compose.is_file():
        compose_text = compose.read_text(encoding="utf-8")
        require("healthcheck:" in compose_text and "runtime_models:/app/runtime_models:ro" in compose_text, "Compose healthcheck or read-only runtime model mount is missing.")
    compose_check = subprocess.run(["docker", "compose", "config"], cwd=ROOT, capture_output=True, text=True)
    require(compose_check.returncode == 0, f"docker compose config failed: {compose_check.stderr.strip() or compose_check.stdout.strip()}")

    final_dl_source = (ROOT / "backend" / "app" / "services" / "final_dl_runtime.py").read_text(encoding="utf-8")
    endpoints_source = (ROOT / "backend" / "app" / "api" / "endpoints.py").read_text(encoding="utf-8")
    require("classify_final_dl_raw_probability(raw_probability)" in final_dl_source, "DL classification is not explicitly based on raw probability.")
    require('"clinical_use": False' in endpoints_source and '"multimodal_status": "experimental_only"' in endpoints_source, "Research-only API status contract is missing.")
    import_check = subprocess.run(
        [sys.executable, "-c", "import sys; from app.main import app; assert 'app.services.prediction' not in sys.modules; assert 'app.services.prediction_dl' not in sys.modules"],
        cwd=ROOT,
        env={**os.environ, "PYTHONPATH": ".:backend", "DL_PRELOAD_ON_STARTUP": "false", "AI_ADVISOR_PROVIDER": "local"},
        capture_output=True,
        text=True,
    )
    require(import_check.returncode == 0, f"Production import boundary failed: {import_check.stderr.strip()}")

    if failures:
        print("PRODUCTION READINESS: FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("PRODUCTION READINESS: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
