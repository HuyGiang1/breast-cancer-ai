# Agent Handoff

## Current state

- **Repository**: `https://github.com/HuyGiang1/breast-cancer-ai`
- **Current branch**: `feat/product-experience-v4`
- **Base commit**: `28841b9` (Batch F Web Feature Freeze)
- **Phase**: **PHASE G1 — PRE-DEPLOY HARDENING COMPLETED**
- **Artifact Status**: **READY FOR LIVE INTEGRATION** (Staging-ready artifact; NOT publicly deployed, zero secrets committed)
- **Web Feature Freeze**: RC-1 strictly preserved.
- **TCIA Provenance & Attribution**: **RESOLVED** (100% byte-for-byte SHA-256 match documented under CC BY 3.0 in `docs/legal/CBIS_DDSM_DATA_AND_DEMO_ATTRIBUTION.md` and `frontend/js/pages/research.js`).
- **Cryptographic Storage**: Upgraded to versioned PBKDF2-HMAC-SHA256 (600,000 rounds) with backward-compatible 120k verification and on-login rehash.
- **API & Container Hardening**: Production fail-closed CORS, disabled `/docs` in production, deep `/readyz` probe, internal network isolation for port 8000.
- **SQLite Concurrency & Backups**: WAL mode, busy timeout 5000ms, 30s timeout, online hot backup script (`scripts/backup_database.py`), and non-destructive restore drill (`scripts/verify_database_restore.py`).
- **Privacy & Patient Notice**: Published at `frontend/pages/privacy.html` with links in footer and shell navigation.

---

## Deployment Documentation & Runbooks

- `docs/deploy/PREDEPLOY_BLOCKERS.md`: Complete status matrix classifying resolved items vs operator actions.
- `docs/deploy/LIVE_SECRET_CHECKLIST.md`: Step-by-step operator checklist for live secrets (SMTP, GIS Google OAuth, invite codes).
- `docs/deploy/DOMAIN_HTTPS_RUNBOOK.md`: DNS records, Let's Encrypt Certbot setup, automatic renewal cron, Nginx reverse proxy.
- `docs/deploy/DEPLOYMENT_RUNBOOK.md`: Comprehensive end-to-end production deployment manual.
- `docs/deploy/BACKUP_AND_RESTORE.md`: WAL mode, zero-downtime hot backups, disaster recovery, atomic restore.
- `docs/deploy/SECURITY_HARDENING_G1.md`: Technical audit of Phase G1 cryptographic and network controls.
- `docs/legal/CBIS_DDSM_DATA_AND_DEMO_ATTRIBUTION.md`: Formal CC BY 3.0 TCIA attribution and hash provenance.

---

## Pending Operator Tasks (Waiting for Operator)

1. **DNS Cutover**: Point domain A/AAAA records to target production host IP.
2. **TLS Certificate Issuance**: Issue Let's Encrypt certificate via Certbot standalone or webroot.
3. **Live SMTP Relay Credentials**: Supply `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD` from SendGrid/SES/Postmark in server `.env`.
4. **Google Cloud Console OAuth**: Configure Web Client ID with authorized HTTPS domain origin and set `GOOGLE_CLIENT_ID` in `.env` (no client secret needed for GIS).

---

## Regression & Verification Gates

All gates pass cleanly:
```bash
find frontend/js -name "*.js" -print0 | xargs -0 -n1 node --check
python3 scripts/verify_frontend_v2.py
node scripts/qa_broken_link_crawler.js
PYTHONPATH=.:backend ./venv/bin/python3 -m pytest -v
python3 scripts/verify_production_readiness.py
python3 scripts/verify_deploy_environment.py --env-file .env.production.example --staging-check
python3 scripts/backup_database.py && python3 scripts/verify_database_restore.py
git diff --check
```
