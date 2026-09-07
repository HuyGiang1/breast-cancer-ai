# Production Server Deployment Runbook

Status: the user has a server. Production deployment has not yet been executed. Server access/configuration details, domain, DNS, and HTTPS configuration remain pending until supplied. External production smoke has not been completed.

This runbook is for a research/educational prototype with `clinical_use=false`. Never store an SSH private key, server password, `.env`, database backup, patient-entered data, or model weight in Git.

## 1. Server preflight

Connect through the operator-approved account and record the result outside public logs:

```bash
uname -m
uname -a
cat /etc/os-release
getconf _NPROCESSORS_ONLN
free -h
df -h
```

Confirm whether the host is `amd64`/`x86_64` or `arm64`/`aarch64`. The Python and Nginx base images support both common architectures, but the complete image and TensorFlow import must be tested on the actual target. Recommended minimum for the current CPU DL runtime is 2 CPU cores, 8 GB RAM, and at least 20 GB free disk beyond OS usage, model artifacts, Docker layers, SQLite state, and backups.

Confirm time synchronization and firewall policy. Expose SSH only from approved sources where practical; expose ports 80 and 443 publicly only when the reverse proxy is ready. Do not expose FastAPI port 8000 directly.

## 2. Docker and Compose

Install Docker Engine and the Compose plugin from the distribution/vendor instructions, then verify:

```bash
docker --version
docker compose version
docker info
docker compose config
```

Treat Docker-group membership as privileged access.

## 3. Checkout and configuration

Use the release-approved commit or tag after the documentation branch is merged:

```bash
git clone https://github.com/HuyGiang1/breast-cancer-ai.git
cd breast-cancer-ai
git status
git rev-parse HEAD
cp .env.example .env
mkdir -p backend/data frontend/results runtime_models backups
```

Edit `.env` only on the server. Use `APP_ENV=production`, exact HTTPS origins after the domain is active, `APP_MAIL_MODE=smtp`, strong provider credentials where approved, and `DL_PRELOAD_ON_STARTUP=true`. Keep `AI_ADVISOR_PROVIDER=local` unless an external provider and its data-handling terms are approved.

```bash
chmod 600 .env
```

## 4. Frozen model artifacts

Transfer model artifacts through an approved release/artifact channel, never normal Git:

```text
runtime_models/logistic_regression_final_seed42.joblib
runtime_models/efficientnetb0_final_seed42.keras
```

Verify exact SHA-256 before startup:

```bash
sha256sum runtime_models/logistic_regression_final_seed42.joblib
# 15a67b8580ba8729eebce9dd1330413905e7caa6ad2a022214769698e8b84755

sha256sum runtime_models/efficientnetb0_final_seed42.keras
# dce9a5230afe1f1e4a8c0e908cd8467ae1b6526f3667e555c3a7db3c5f2f168b

git ls-files runtime_models
# Expected: no output
```

Compose mounts `./runtime_models` at `/app/runtime_models:ro`. Confirm the effective mount is read-only with `docker inspect` after startup.

## 5. Backup before change

If a prior SQLite database exists, stop writes and back it up before upgrade:

```bash
python3 scripts/backup_database.py --database backend/data/app.db --output-dir backups
```

Copy encrypted backups off-host according to the operator's retention policy. See [DATABASE_BACKUP.md](DATABASE_BACKUP.md). Restore rehearsals must target a temporary database before any live restore.

## 6. Build and start

```bash
docker compose config
docker compose build
docker compose up -d
docker compose ps
docker compose logs --tail=200 api
docker compose logs --tail=200 web
```

Readiness must remain false until the frozen ML/DL artifacts can load and pass checksum checks.

## 7. Local server smoke

Before DNS cutover, run on the host:

```bash
curl -fsS http://127.0.0.1/healthz
curl -fsS http://127.0.0.1/readyz
curl -fsS http://127.0.0.1/api/v1/models/final/status/
curl -fsS http://127.0.0.1/api/v1/research/evidence/
```

The final status must report ML and DL as `research_demo`, `artifact_verified: true`, `clinical_use: false`, and multimodal as `experimental_only`. With disposable data, verify benign/malignant ML and DL requests, corrupt DL input, invalid ML input, authentication/role behavior, history, report, and restart persistence.

Classification contracts:

- WDBC ML: raw malignant probability `>= 0.36`.
- CBIS-DDSM DL: raw malignant probability `>= 0.515`.
- Frozen Platt output: display/reliability only.

## 8. Nginx, domain, DNS, and HTTPS

`deploy/nginx.conf` currently serves the static frontend and proxies `/api/`, `/results/`, `/healthz`, and `/readyz`. It contains no public TLS certificate configuration.

When the operator supplies the domain:

1. Point the required A/AAAA record to the server.
2. Confirm DNS propagation from an external resolver.
3. Set `APP_FRONTEND_URL` and `APP_CORS_ORIGINS` to the exact HTTPS origin.
4. Obtain and auto-renew a certificate using the chosen host-level Nginx/ACME arrangement.
5. Redirect HTTP to HTTPS and retain only required proxy headers/routes.
6. Re-run public smoke from a network outside the server.

Do not invent or commit the server IP, domain, SSH username, private key, password, or certificate material.

## 9. Restart and persistence

Compose services use `restart: unless-stopped`. Verify recovery after both a Compose restart and an approved host reboot window:

```bash
docker compose restart
docker compose ps
curl -fsS http://127.0.0.1/readyz
```

Confirm SQLite records persist, model checksums remain verified, and `runtime_models` remains read-only.

## 10. Public production smoke

After DNS/HTTPS is active, verify through the public origin:

- landing and all canonical static routes return expected status;
- `/healthz`, `/readyz`, final status, and research evidence traverse Nginx;
- no mixed content, certificate, module-import, console, or unexpected network errors;
- auth, ML/DL, controlled invalid input, patient/history/report, and logout work using disposable data;
- security headers, upload limit, logs, disk growth, and backup location are reviewed.

External production smoke is not complete until these checks have been run against the real URL.

## 11. Update and rollback

Back up first. Update only to an approved commit with a fast-forward pull, then rebuild and smoke-test:

```bash
git pull --ff-only
docker compose build
docker compose up -d
docker compose ps
```

For rollback, retain the prior known-good code SHA, container image, `.env` backup, model checksums, and schema-compatible SQLite backup. Check out the approved prior SHA without rewriting shared history, rebuild/start it, and restore SQLite only when data/schema compatibility requires it.

## 12. Safe shutdown

```bash
docker compose down
```

Never use `docker compose down -v` during normal operations because persistent state must be preserved.
