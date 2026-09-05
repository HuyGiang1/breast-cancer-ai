# Deployment Runbook

Status on 2026-09-05: local container verification passed with Docker Desktop 28.5.1 aarch64, Compose v2.40.3, and the Python 3.11-slim API image. VPS provisioning, domain, and HTTPS are blocked because no server or DNS credentials have been provided. This research/educational prototype is not for clinical diagnosis.

## Prerequisites

On an Ubuntu 22.04/24.04 host, install Docker Engine and the Docker Compose plugin. For the final DL runtime, use at least 2 CPU cores, 8 GB RAM preferred, and disk space for images, `runtime_models`, SQLite data, and off-host backups.

```bash
docker --version
docker compose version
git clone https://github.com/HuyGiang1/breast-cancer-ai.git
cd breast-cancer-ai
```

## Configure Runtime Secrets and Artifacts

Create the server-only environment file. Do not commit it.

```bash
cp .env.example .env
mkdir -p runtime_models
```

For a public deployment set `APP_ENV=production`, an HTTPS frontend URL/CORS origin once a domain exists, `APP_MAIL_MODE=smtp`, SMTP values, and `AI_ADVISOR_PROVIDER=local` unless an approved provider key is configured. Keep `DL_PRELOAD_ON_STARTUP=true` for readiness to prove the model is loadable.

Copy the frozen artifacts into exactly these untracked paths:

```text
runtime_models/logistic_regression_final_seed42.joblib
runtime_models/efficientnetb0_final_seed42.keras
```

Verify their byte-level contracts before starting:

```bash
shasum -a 256 runtime_models/logistic_regression_final_seed42.joblib
# 15a67b8580ba8729eebce9dd1330413905e7caa6ad2a022214769698e8b84755
shasum -a 256 runtime_models/efficientnetb0_final_seed42.keras
# dce9a5230afe1f1e4a8c0e908cd8467ae1b6526f3667e555c3a7db3c5f2f168b
git ls-files runtime_models
# Expected: no output
```

## Build and Start

```bash
docker compose config
docker compose build
docker compose up -d
docker compose ps
curl -fsS http://127.0.0.1/healthz
curl -fsS http://127.0.0.1/readyz
curl -fsS http://127.0.0.1/api/v1/models/final/status/
curl -fsS http://127.0.0.1/api/v1/research/evidence/
```

The final status must show ML and DL `research_demo`, `artifact_verified: true`, `clinical_use: false`, and `multimodal_status: experimental_only`. The API container mounts only `./runtime_models` read-only at `/app/runtime_models`; it does not mount `experiments/`.

For smoke predictions, use the authenticated UI with synthetic/demo data. Confirm ML classification uses raw `predict_proba` class-1 value and threshold `0.36`; confirm DL returns `raw_probability`, a Platt-calibrated display probability, and classification from raw `>= 0.515`. Submit one malformed image and one invalid ML payload to confirm controlled `400`/`422` responses without traceback.

## Operations

Inspect logs without placing patient data in tickets:

```bash
docker compose logs --tail=200 api
docker compose logs --tail=200 web
```

Create a database backup and test restores only on a temporary database as described in [DATABASE_BACKUP.md](DATABASE_BACKUP.md):

```bash
python3 scripts/backup_database.py --database backend/data/app.db --output-dir backups
```

For an application update, back up first, then use only fast-forward Git updates:

```bash
git pull --ff-only
docker compose build
docker compose up -d
docker compose ps
```

To roll back application code, select a known-good commit, rebuild, and start again. Restore SQLite only when the backup and schema are known compatible:

```bash
git log --oneline -10
git checkout <known-good-commit>
docker compose build
docker compose up -d
```

To shut down services without deleting persisted host data or model artifacts:

```bash
docker compose down
```

## Network Status

`deploy/nginx.conf` serves the frontend, proxies `/api/`, `/results/`, `/healthz`, and `/readyz`, forwards standard proxy headers, caps uploads at 20 MB, and allows 180 seconds for DL inference. It intentionally contains no TLS certificate configuration and does not expose host paths.

- VPS: **BLOCKED** - not yet provisioned.
- Domain: **BLOCKED** - no DNS record or domain supplied.
- HTTPS: **BLOCKED** - configure a certificate only after VPS/domain provisioning, then update `APP_FRONTEND_URL` and `APP_CORS_ORIGINS` to the HTTPS origin.
