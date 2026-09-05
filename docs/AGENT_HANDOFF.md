# Agent Handoff

## Current state

- Repository: `https://github.com/HuyGiang1/breast-cancer-ai`
- Current branch: `ops/production-readiness`
- Base branch: `feat/system-finalization`
- Do not create a new branch.
- Research is frozen. Do not retrain, recalibrate, change split/model/threshold, or promote clinical use.

## Completed on this branch

- CI import-path and SHAP dependency boundaries were fixed. GitHub Actions run `33945050609` is green for `dfc264d`.
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

## Docker blocker and exact next steps

`runtime_models/` exists locally, is Git-ignored, and contains checksum-verified copies of the frozen ML/DL artifacts. Docker compose config passes. `docker compose build` cannot run because Docker Desktop daemon is not running.

When Docker is available, remain on this branch and run exactly:

```bash
docker compose config
docker compose build
docker compose up -d
docker compose ps
curl -fsS http://127.0.0.1/healthz
curl -fsS http://127.0.0.1/readyz
curl -fsS http://127.0.0.1/api/v1/models/final/status/
curl -fsS http://127.0.0.1/api/v1/research/evidence/
docker compose restart
docker compose ps
docker compose down
```

Also run benign/malignant ML and DL container requests plus invalid ML/corrupt image requests. Confirm read-only `/app/runtime_models` mount, both artifact checksums, frozen Platt checksum, ML raw `0.36`, DL raw `0.515`, `clinical_use: false`, and `multimodal_status: experimental_only`.

After Docker passes, push the branch, wait for GitHub Actions success on the latest commit, update trackers, and only then report `docs/final-documentation` as the next branch. Do not create that branch automatically.
