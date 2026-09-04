# Deployment Guide

Target: Ubuntu VPS + Docker Compose + Nginx + HTTPS + domain.

## 1. Prepare Server

Use Ubuntu 22.04 or 24.04. Recommended minimum for DL inference:

- 2 CPU cores
- 4 GB RAM minimum, 8 GB preferred
- 20 GB disk plus space for model artifacts and SQLite backups

## 2. Install Docker

Follow Docker's official Ubuntu installation guide, then verify:

```bash
docker --version
docker compose version
```

## 3. Clone Repository

```bash
git clone https://github.com/giangnguyenhuy87/breast-cancer-ai.git
cd breast-cancer-ai
```

Do not clone or run from a directory that contains secrets committed to Git.

## 4. Configure Environment

```bash
cp .env.example .env
nano .env
```

Production recommendations:

```env
APP_ENV=production
APP_FRONTEND_URL=https://your-domain.example
APP_CORS_ORIGINS=https://your-domain.example
APP_MAIL_MODE=smtp
DL_PRELOAD_ON_STARTUP=false
AI_ADVISOR_PROVIDER=local
```

Add provider API keys only on the server `.env`, never in Git.

## 5. Place Model Artifacts

Heavy model files should not live in Git. Use one of these simple strategies:

- Recommended for student project: upload model artifacts to the server `models/` directory with `scp`.
- Alternative: publish model weights in a private GitHub Release and download them during deployment.
- Alternative: use Git LFS only if repository storage/bandwidth limits are acceptable.

Expected paths:

```text
models/
models/deep_learning/
```

After placement, verify:

```bash
find models -maxdepth 3 -type f
```

## 6. Build and Start

```bash
docker compose up -d --build
docker compose ps
docker compose logs -f api
```

The web service exposes port `80`.

## 7. Health Checks

From the server:

```bash
curl http://127.0.0.1/healthz
curl http://127.0.0.1/readyz
```

Through Nginx compose proxy, API paths are available under `/api/` for app calls and backend direct docs are inside the API container.

## 8. Domain

Create DNS `A` record:

```text
your-domain.example -> VPS_PUBLIC_IP
```

Update `.env`:

```env
APP_FRONTEND_URL=https://your-domain.example
APP_CORS_ORIGINS=https://your-domain.example
```

## 9. HTTPS

Simplest options:

- Use Cloudflare proxy with Full/Strict SSL if you manage DNS there.
- Or install host-level Nginx + Certbot and reverse proxy to the Docker web service.

Certbot example for host-level Nginx:

```bash
sudo apt install nginx certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.example
```

If using host-level Nginx, map Docker web to a local port such as `127.0.0.1:8080:80` instead of public `80:80`.

## 10. Logs

```bash
docker compose logs -f api
docker compose logs -f web
```

Avoid logging passwords, tokens, API keys, or unnecessary patient data.

## 11. SQLite Backup

For research/demo scale, SQLite is acceptable. Back up:

```bash
mkdir -p backups
cp backend/data/app.db "backups/app-$(date +%Y%m%d-%H%M%S).db"
```

Restore:

```bash
docker compose down
cp backups/app-YYYYMMDD-HHMMSS.db backend/data/app.db
docker compose up -d
```

If the app becomes a public multi-user service, plan PostgreSQL migration.

## 12. Update Deployment

```bash
git pull --ff-only
docker compose up -d --build
docker compose logs -f api
```

Run a smoke check:

```bash
curl http://127.0.0.1/api/v1/models/
curl http://127.0.0.1/healthz
```

## 13. Rollback

```bash
git log --oneline -5
git checkout <previous-good-commit>
docker compose up -d --build
```

Restore database only if schema/data changed and the current DB is not compatible.

## 14. Public Demo Privacy Rule

Do not invite users to upload real patient data. Use synthetic/demo records and show the research-only disclaimer clearly.
