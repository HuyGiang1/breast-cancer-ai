# Comprehensive Production Deployment Runbook

**Document Version**: 2.0.0  
**Phase**: Phase G1 — Pre-Deploy Hardening  
**Target Status**: `READY FOR LIVE INTEGRATION`  
**Application**: Breast Cancer AI Multimodal Diagnostic Prototype

---

## 1. Architectural Architecture & Preflight

### 1.1 Architecture & Topology
```
[ Internet / Browser ]
         │
         ▼ (Ports 80/443 with TLS termination & Security Headers)
┌────────────────────────────────────────────────────────┐
│ Nginx 1.27 Alpine Reverse Proxy (`web_prod`)          │
│ - Rate limiting (auth: 5r/s, api: 30r/s)              │
│ - CSP, HSTS, X-Frame-Options, No-Cache on HTML         │
│ - Static assets (/usr/share/nginx/html) [ro]           │
└────────────────────────────────────────────────────────┘
         │
         ▼ (Internal Docker Bridge Network: port 8000 only)
┌────────────────────────────────────────────────────────┐
│ FastAPI 1.0.0 Backend Runtime (`api_prod`)            │
│ - Fail-closed HTTPS CORS enforcement                   │
│ - PBKDF2-HMAC-SHA256 (600,000 rounds)                  │
│ - Frozen ML: Logistic Regression (WDBC, cut: 0.360)   │
│ - Frozen DL: EfficientNet-B0 (CBIS, cut: 0.515 raw)   │
│ - SQLite WAL Mode (`app.db`) [rw]                      │
└────────────────────────────────────────────────────────┘
```

### 1.2 Hardware & OS Recommendations
- **Architecture**: `x86_64` (amd64) or `arm64` (aarch64)
- **CPU**: 2+ vCPUs recommended
- **RAM**: Minimum 4 GB (8 GB recommended for concurrent inference & preloading)
- **Disk**: 20+ GB SSD (for Docker images, weights, database, and backups)
- **OS**: Ubuntu 22.04 LTS or 24.04 LTS / Debian 12

---

## 2. Server Setup & Repository Deployment

### Step 2.1: Clone and Prepare Directories
```bash
# Clone the repository
git clone https://github.com/HuyGiang1/breast-cancer-ai.git /opt/breast-cancer-ai
cd /opt/breast-cancer-ai

# Ensure required storage directories exist
mkdir -p backend/data backend/backups frontend/results runtime_models
chmod 700 backend/data backend/backups
```

### Step 2.2: Configure Environment
Copy `.env.production.example` to `.env`:
```bash
cp .env.production.example .env
chmod 600 .env
```
Edit `.env` with production values:
- `APP_ENV=production`
- `APP_FRONTEND_URL=https://bcai.example.com`
- `APP_CORS_ORIGINS=https://bcai.example.com`
- `APP_MAIL_MODE=smtp` + provider credentials
- `DOCTOR_REGISTRATION_MODE=invite` + random 32-char invite code
- `GOOGLE_CLIENT_ID` from Google Cloud Console

### Step 2.3: Verify Environment Prior to Launch
```bash
python3 scripts/verify_deploy_environment.py --env-file .env
```
Ensure all items pass.

---

## 3. Production Model Artifacts

Ensure the frozen runtime models exist in `runtime_models/`:
- `runtime_models/logistic_regression_final_seed42.joblib`
- `runtime_models/efficientnetb0_final_seed42.keras`

Verify SHA-256 hashes against the manifest:
```bash
python3 -c "import hashlib; print('ML:', hashlib.sha256(open('runtime_models/logistic_regression_final_seed42.joblib','rb').read()).hexdigest()[:12])"
python3 -c "import hashlib; print('DL:', hashlib.sha256(open('runtime_models/efficientnetb0_final_seed42.keras','rb').read()).hexdigest()[:12])"
```

---

## 4. HTTPS & Domain Setup

Follow [DOMAIN_HTTPS_RUNBOOK.md](file:///Users/GiangNguyenHuy/Documents/breast-cancer-ai/docs/deploy/DOMAIN_HTTPS_RUNBOOK.md) to:
1. Point DNS A/AAAA records to the server IP.
2. Issue Let's Encrypt certificates using Certbot.
3. Generate `deploy/nginx.production.conf` from `deploy/nginx.production.conf.template`.

---

## 5. Container Launch & Verification

### Step 5.1: Build and Launch via Production Compose
```bash
docker compose -f docker-compose.production.yml up -d --build
```

### Step 5.2: Verify Container Health & Probes
```bash
# Check container status
docker compose -f docker-compose.production.yml ps

# Check API readiness probe (database + ML + DL)
curl -s http://localhost:8000/readyz | jq .

# Expected output:
# {
#   "status": "ready",
#   "database": "ok",
#   "final_ml": "research_demo",
#   "final_dl": "research_demo"
# }
```

### Step 5.3: Verify HTTPS Public Endpoint
```bash
curl -I https://bcai.example.com/
curl -I https://bcai.example.com/readyz
```

---

## 6. Backup Automation & Monitoring

1. Set up daily hot backups per [BACKUP_AND_RESTORE.md](file:///Users/GiangNguyenHuy/Documents/breast-cancer-ai/docs/deploy/BACKUP_AND_RESTORE.md):
   ```cron
   0 2 * * * cd /opt/breast-cancer-ai && /usr/bin/python3 scripts/backup_database.py --keep 14 >> /var/log/bcai_backup.log 2>&1
   ```
2. Schedule automated restore drill weekly:
   ```cron
   0 4 * * 0 cd /opt/breast-cancer-ai && /usr/bin/python3 scripts/verify_database_restore.py >> /var/log/bcai_restore_drill.log 2>&1
   ```
3. Set up Let's Encrypt certificate renewal:
   ```cron
   0 3,15 * * * certbot renew --post-hook "docker compose -f /opt/breast-cancer-ai/docker-compose.production.yml exec -T web nginx -s reload" >> /var/log/certbot_renew.log 2>&1
   ```

---

## 7. Emergency Maintenance & Rollback

- **Restart Services**: `docker compose -f docker-compose.production.yml restart`
- **View Live Logs**: `docker compose -f docker-compose.production.yml logs -f --tail=100`
- **Disaster Recovery Database Restore**: See [BACKUP_AND_RESTORE.md](file:///Users/GiangNguyenHuy/Documents/breast-cancer-ai/docs/deploy/BACKUP_AND_RESTORE.md) Section 4.
