# Breast Cancer AI - Project Progress

Last updated: 2026-09-12

## Current stage

**Phase G1 — Pre-Deploy Hardening (Security + Data Safety + TCIA Attribution + Infrastructure Readiness)**

- **Current branch**: `feat/product-experience-v4`
- **Starting HEAD**: `28841b9`
- **Web Feature Freeze**: RC-1 strictly observed (no mobile apps, no new features, no UI redesigns, no model retraining, no threshold changes).
- **Current Artifact Status**: **READY FOR LIVE INTEGRATION** (Staging-ready artifact; NOT publicly deployed, zero secrets committed).
- **Key Deliverables & Hardening Completed**:
  - **TCIA / CBIS-DDSM Provenance (P0 Blocker Resolved)**: Traced byte-for-byte identical SHA-256 hashes against CBIS-DDSM test set; documented under CC BY 3.0 in `docs/legal/CBIS_DDSM_DATA_AND_DEMO_ATTRIBUTION.md`; authoritative attribution card in `frontend/js/pages/research.js`.
  - **Password Storage Hardening**: Implemented versioned PBKDF2-HMAC-SHA256 with 600,000 rounds (~129ms per hash), backward-compatible legacy 120k verification, and transparent on-login rehash upgrade.
  - **API Security & Fail-Closed Policy**: `APP_ENV=production` fails closed if `APP_CORS_ORIGINS` is missing, `*`, non-HTTPS, or contains `localhost`. Suppressed `/docs`, `/redoc`, and `/openapi.json` via `APP_ENABLE_API_DOCS=false`. Generic user-facing error messages on OAuth/reset-password endpoints without internal exception leakage.
  - **Database Production Reliability**: SQLite configured with `PRAGMA journal_mode = WAL`, `synchronous = NORMAL`, `busy_timeout = 5000`, and 30s timeout. Created `scripts/backup_database.py` (online hot backup with SHA-256 and integrity checks), `scripts/verify_database_restore.py` (non-destructive restore drill), and `docs/deploy/BACKUP_AND_RESTORE.md`.
  - **Environment Templates & Validator**: Clean development defaults in `.env.example`; production template in `.env.production.example`; validator in `scripts/verify_deploy_environment.py`; operator diagnostic utility in `scripts/test_smtp_delivery.py`.
  - **Production Infrastructure Packaging**: `deploy/nginx.production.conf.template` with HSTS, CSP, X-Frame-Options, X-Content-Type-Options, Permissions-Policy, rate limits, and hidden file blocks; `docker-compose.production.yml` with read-only model mount and isolated internal network for port 8000.
  - **Privacy & Patient Data Minimization**: Factual notice in `frontend/pages/privacy.html` and `frontend/js/pages/privacy.js`; footer links updated in `frontend/index.html` and `frontend/js/components/shell.js`.
  - **Deployment Runbooks**: Authored `docs/deploy/PREDEPLOY_BLOCKERS.md`, `docs/deploy/LIVE_SECRET_CHECKLIST.md`, `docs/deploy/DOMAIN_HTTPS_RUNBOOK.md`, `docs/deploy/DEPLOYMENT_RUNBOOK.md`, and `docs/deploy/SECURITY_HARDENING_G1.md`.
  - **Validation & Test Suite**: 86/86 Pytest tests PASS; 0 broken links; static frontend validation PASS; production readiness PASS; Batch F browser E2E PASS.

## Completed major milestones

- [x] Dataset audit and leakage-controlled CBIS-DDSM inferred-group split
- [x] WDBC ML study, calibration, bootstrap, error analysis, and SHAP
- [x] CBIS-DDSM DL baselines, validation-first ROI ablation, calibration, bootstrap, error analysis, and Grad-CAM
- [x] Frozen Logistic Regression and EfficientNet-B0 research/demo runtimes
- [x] Unified final model status and central research evidence adapter
- [x] Frontend Architecture V2 and 84/84 cross-device route QA
- [x] Batches A–F Feature Parity Restoration and Web Feature Freeze (RC-1)
- [x] TCIA / CBIS-DDSM demo mammogram provenance audit & attribution (CC BY 3.0)
- [x] Phase G1 Pre-Deploy Hardening: Security, Database WAL, Backups, Nginx, Compose, Privacy
- [x] Deployment Runbooks, Secrets Checklist, and Domain HTTPS Guides

## Frozen state

- Research: **FROZEN**
- Runtime Models: **FROZEN**
- Frontend Web Product: **FROZEN (RC-1)**
- Pre-Deploy Engineering Hardening: **COMPLETE**

## Pending External Operator Inputs (Waiting for Operator)

1. **Production Domain & DNS Cutover**: Point domain A/AAAA records to target server IP.
2. **TLS Certificate Issuance**: Run Certbot standalone/webroot on live host per `DOMAIN_HTTPS_RUNBOOK.md`.
3. **Live SMTP Relay Credentials**: Populate `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD` from SendGrid/SES/Postmark.
4. **Google Cloud Console OAuth Client ID**: Create Web Client ID with authorized HTTPS domain origin.

## Document roles

- `docs/PROJECT_PROGRESS.md`: simple overall roadmap and progress.
- `docs/PROJECT_STATUS.md`: detailed phase/evidence status.
- `docs/AGENT_HANDOFF.md`: exact continuation instructions for the next session.
