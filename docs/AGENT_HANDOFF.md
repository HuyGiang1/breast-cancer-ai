# Agent Handoff

## Current state

- Repository: `https://github.com/HuyGiang1/breast-cancer-ai`
- Current branch: `ops/production-readiness`
- Base branch: `feat/system-finalization`
- Do not create a new branch.
- Research is frozen. Do not retrain, recalibrate, change split/model/threshold, or promote clinical use.

## Completed on this branch

- CI import-path and SHAP dependency boundaries were fixed. GitHub Actions run `33945903158` is green for production-readiness commit `8fce90d`.
- Final application imports direct final ML/DL services, not legacy `prediction.py` or `prediction_dl.py`.
- Uncertainty messages use the actual frozen ML raw threshold `0.36` and DL raw threshold `0.515`; multimodal `0.5` is explicitly probability ambiguity only.
- Added `scripts/restore_database.py`, verified it on a temporary database, and documented it in `docs/DATABASE_BACKUP.md`.
- Added local final-system benchmark outputs and `scripts/verify_production_readiness.py`.
- Added safety review, deployment runbook, and Nginx DL proxy timeouts.

## Local verification already passed

```bash
PYTHONPATH=.:backend venv/bin/python -m pytest -q       # 24 passed
python3 -m compileall backend/app scripts tests
node --check frontend/app.js
PYTHONPATH=.:backend venv/bin/python scripts/validate_final_model_contract.py
PYTHONPATH=.:backend venv/bin/python scripts/validate_frozen_dl_calibration.py
PYTHONPATH=.:backend venv/bin/python scripts/verify_final_ml_runtime_parity.py
PYTHONPATH=.:backend venv/bin/python scripts/verify_final_dl_runtime_parity.py
PYTHONPATH=.:backend AI_ADVISOR_PROVIDER=local DL_PRELOAD_ON_STARTUP=false venv/bin/python scripts/verify_final_application.py
PYTHONPATH=.:backend AI_ADVISOR_PROVIDER=local DL_PRELOAD_ON_STARTUP=false venv/bin/python scripts/verify_production_readiness.py
```

The shell has no `python` alias; use `venv/bin/python` for Python commands that require the project environment.

## Docker verification and exact next steps

Docker verification is complete locally with Docker Desktop 28.5.1 aarch64, Compose v2.40.3, and the Python 3.11-slim API image. The earlier BuildKit I/O issue was host storage pressure and was resolved before the successful build.

- API became healthy and Nginx served port 80.
- `/healthz`, `/readyz`, final model status, and frozen research evidence passed through Nginx.
- `/app/runtime_models` was read-only. ML, DL, and frozen Platt SHA-256 values matched their contracts.
- ML and DL benign/malignant requests followed raw thresholds `0.36` and `0.515`; invalid ML returned `422` and corrupt DL upload returned `400`.
- Packaged snapshot matched frozen source SHA `81df4458274dd4f2fdea771fc1bd961e4007e2a683e108f4da0ba6cb8692ce13` without an `experiments` mount.
- After `docker compose restart`, database counts remained `users=3`, `predictions=14`, integrity was `ok`, and final models reloaded healthy. Stack was then stopped with `docker compose down`, without `-v`.

The next phase is `docs/final-documentation`; do not create it automatically. VPS/domain/HTTPS are still blocked external deployment tasks.
