# Production Cutover Operational Checklist

**Target**: Public Production Cutover (Phase G3)  
**Status**: **DRAFT / READY FOR CUTOVER WINDOW — DO NOT EXECUTE YET**  
**Precondition**: Phase G2 Staging UAT Complete and Operator Sign-Off.

> [!WARNING]
> DO NOT EXECUTE THIS CUTOVER CHECKLIST DURING PHASE G2.
> This document is an operational runbook prepared for the subsequent production cutover phase.

---

## 1. Pre-Cutover Verification & Commit Lock

- [ ] **Release Commit Verified**:
  - Target Release Commit: `<STAGING_TESTED_COMMIT_SHA>`
  - Worktree clean, no untracked or modified files.
- [ ] **Frozen Model Integrity Checksums**:
  - Verify exact SHA-256 before container launch:
    - ML (`wdbc-logistic-regression-v1`): `15a67b8580ba8729eebce9dd1330413905e7caa6ad2a022214769698e8b84755` (threshold: 0.360 raw)
    - DL (`cbis-efficientnetb0-full-v1`): `dce9a5230afe1f1e4a8c0e908cd8467ae1b6526f3667e555c3a7db3c5f2f168b` (threshold: 0.515 raw)
    - Platt Calibration (`efficientnet_b0_platt_final_seed42.json`): `4d43ae671f649e3940176b6ec0f6c2436d4128f7d9385ef66699eb3c35df1782`
- [ ] **Pre-Deploy Database Hot Backup**:
  - Take backup of active production data (if migrating or upgrading):
    ```bash
    python3 scripts/backup_database.py --source backend/data/app.db --dest backend/backups/
    ```
  - Verify backup non-destructively:
    ```bash
    python3 scripts/verify_database_restore.py --backup-path backend/backups/<backup_file>.db
    ```

---

## 2. Server Environment Configuration (`.env`)

- [ ] **Create Production `.env` from Template**:
  ```bash
  cp .env.production.example .env
  chmod 600 .env
  ```
- [ ] **Configure Production Variables**:
  - `APP_ENV=production`
  - `APP_FRONTEND_URL=https://<PRODUCTION_FQDN>`
  - `APP_CORS_ORIGINS=https://<PRODUCTION_FQDN>`
  - `APP_ENABLE_API_DOCS=false`
  - `APP_MAIL_MODE=smtp`
  - `SMTP_HOST=<operator_smtp_host>`
  - `SMTP_PORT=587` (or `465`)
  - `SMTP_SECURITY=starttls` (or `ssl`)
  - `SMTP_USERNAME=<operator_smtp_user>`
  - `SMTP_PASSWORD=<operator_smtp_password>`
  - `SMTP_FROM_EMAIL=noreply@<PRODUCTION_FQDN>`
  - `SMTP_FROM_NAME=Breast Health Studio`
  - `GOOGLE_CLIENT_ID=<operator_google_client_id>.apps.googleusercontent.com`
  - `DOCTOR_REGISTRATION_MODE=disabled` (or `invite` with server-generated secret)
  - `AI_ADVISOR_PROVIDER=local`
- [ ] **Validate Configuration**:
  ```bash
  python3 scripts/verify_deploy_environment.py --env-file .env
  ```

---

## 3. DNS & TLS Certificate Issuance

- [ ] **DNS A/AAAA Cutover**:
  - Point `<PRODUCTION_FQDN>` DNS A/AAAA record to the production server public IP.
  - Verify propagation:
    ```bash
    dig +short <PRODUCTION_FQDN>
    ```
- [ ] **Google Identity Services Origin**:
  - Add `https://<PRODUCTION_FQDN>` to "Authorized JavaScript origins" in Google Cloud Console.
- [ ] **TLS Bootstrap (Port 80 ACME Challenge)**:
  - Render temporary bootstrap Nginx config:
    ```bash
    python3 scripts/render_nginx_config.py --server-name <PRODUCTION_FQDN> --mode bootstrap
    ```
  - Start bootstrap Nginx:
    ```bash
    docker compose -f docker-compose.production.yml up -d web
    ```
  - Issue Let's Encrypt certificate:
    ```bash
    certbot certonly --webroot -w ./certbot/www -d <PRODUCTION_FQDN> --non-interactive --agree-tos -m ops@<PRODUCTION_FQDN>
    ```
- [ ] **Render Final Production Nginx Configuration**:
  ```bash
  python3 scripts/render_nginx_config.py --server-name <PRODUCTION_FQDN> --mode production
  ```
- [ ] **Restart Web Container with Full HTTPS**:
  ```bash
  docker compose -f docker-compose.production.yml restart web
  ```

---

## 4. Service Launch & Health Verification

- [ ] **Start Application Services**:
  ```bash
  docker compose -f docker-compose.production.yml up -d --build
  ```
- [ ] **Verify Container Privileges (Non-Root)**:
  ```bash
  docker compose -f docker-compose.production.yml exec api id
  # Expected: uid=10001(appuser) gid=10001(appgroup)
  ```
- [ ] **Check Health and Readiness Probes**:
  ```bash
  curl -fsS https://<PRODUCTION_FQDN>/healthz
  # Expected: {"status":"ok"}

  curl -fsS https://<PRODUCTION_FQDN>/readyz
  # Expected: {"status":"ready","database":"ok","final_ml":"operational","final_dl":"operational"}
  ```
- [ ] **Verify Security Headers**:
  ```bash
  curl -sI https://<PRODUCTION_FQDN> | grep -E "X-Frame-Options|X-Content-Type-Options|Referrer-Policy|Content-Security-Policy"
  ```
- [ ] **Verify Port 8000 Is Not Exposed Publicly**:
  ```bash
  curl -m 3 http://<PRODUCTION_SERVER_IP>:8000/readyz
  # Expected: Connection refused or timeout (blocked by firewall/Compose isolation)
  ```

---

## 5. Live Smoke & UAT Verification

- [ ] **Guest User Smoke**:
  - Visit `https://<PRODUCTION_FQDN>` in clean browser profile.
  - Verify static assets load, fonts render, zero CSP violations in browser console.
- [ ] **Google Sign-In Smoke**:
  - Log in with real test Google account -> Creates personal account (`role=user`).
- [ ] **Password Reset Smoke**:
  - Trigger Forgot Password -> Verify generic API response (no token disclosed).
  - Verify delivery of reset email -> Follow link -> Successfully set new password.
- [ ] **Structured ML Inference**:
  - Run benign sample and malignant sample -> Verify predicted probability and SHAP plot.
- [ ] **Mammography DL & Grad-CAM**:
  - Upload mammogram image -> Verify prediction and in-memory Grad-CAM data URL overlay.
- [ ] **Multimodal Fusion**:
  - Run fusion analysis -> Verify 40/60 weighted combination.
- [ ] **Doctor Workspace (if enabled)**:
  - Create synthetic patient profile -> Link analyses -> Verify timeline -> Export PDF report.
- [ ] **Privacy Gate Verification**:
  - Direct HTTP access to `/results/` returns 404:
    ```bash
    curl -I https://<PRODUCTION_FQDN>/results/test.png
    # Expected: HTTP 404
    ```

---

## 6. Rollback Procedure

If fatal issues occur during cutover (e.g. database corruption, container failure, TLS failure):

1. **Immediate Service Rollback**:
   ```bash
   docker compose -f docker-compose.production.yml down
   git checkout <PREVIOUS_STABLE_COMMIT>
   docker compose -f docker-compose.production.yml up -d --build
   ```
2. **Database Rollback** (if active DB was altered):
   ```bash
   python3 scripts/restore_database.py --backup <pre_cutover_backup_path> --target backend/data/app.db
   ```
3. **DNS Rollback**:
   - Revert DNS A/AAAA record to previous host if required.

---

## 7. Post-Cutover Validation & HSTS Staged Rollout

- [ ] **Continuous Monitoring**:
  - Monitor API error rates, memory usage, and Nginx logs for 24-48 hours.
- [ ] **HSTS Rollout Decision**:
  - Initial Production: `max-age=31536000` (already active in production template).
  - Extended Post-Validation: After 30 days of error-free HTTPS, subdomains, and redirects, operator may submit domain to HSTS preload list and add `includeSubDomains; preload` if desired.
