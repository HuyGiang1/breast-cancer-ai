# Pre-Deployment Hardening Blocker Status Matrix

**Phase**: Phase G1 — Pre-Deploy Hardening  
**Target Status**: `READY FOR LIVE INTEGRATION`  
**Current Baseline**: `feat/product-experience-v4` (Batch F + Hardening)

---

## 1. Blocker Classification Matrix

This matrix distinguishes items that can and must be resolved by engineering without live production secrets (**RESOLVED**) versus items that strictly require external infrastructure, DNS records, or operator credentials (**WAITING_FOR_OPERATOR**).

| ID | Item / Subsystem | Category | Resolution Status | Technical Implementation / Operator Requirement |
| :--- | :--- | :--- | :--- | :--- |
| **B-01** | **TCIA / CBIS-DDSM Provenance & License** | Legal & Attribution | **RESOLVED** | Exact SHA-256 verified against CBIS-DDSM test set; CC BY 3.0 citations in `docs/legal/CBIS_DDSM_DATA_AND_DEMO_ATTRIBUTION.md`; card in `pages/research.html`. |
| **B-02** | **Password Storage Hardening** | Security | **RESOLVED** | Versioned `pbkdf2_sha256$600000$<salt>$<digest>` (OWASP compliant, ~129ms per hash). Backward-compatible verification for legacy hashes with transparent on-login rehash upgrade. |
| **B-03** | **CORS Fail-Closed Policy** | Security | **RESOLVED** | API raises `RuntimeError` in production if `APP_CORS_ORIGINS` is missing, `*`, contains `localhost`, or uses non-HTTPS scheme. Explicit method/header whitelists. |
| **B-04** | **API Documentation Exposure** | Security | **RESOLVED** | Swagger UI (`/docs`), ReDoc (`/redoc`), and OpenAPI spec (`/openapi.json`) are disabled when `APP_ENABLE_API_DOCS=false` (default in production). |
| **B-05** | **Health & Readiness Probes** | Operational | **RESOLVED** | `/healthz` provides liveness; `/readyz` probes live SQLite database and ML/DL model availability, returning HTTP 503 if degraded. |
| **B-06** | **SQLite WAL & Concurrency** | Database | **RESOLVED** | WAL mode (`PRAGMA journal_mode = WAL`), `synchronous = NORMAL`, `busy_timeout = 5000`, and 30s connection timeout eliminate database lock exceptions. |
| **B-07** | **Zero-Downtime Backup & Restore** | Database | **RESOLVED** | `scripts/backup_database.py` (online hot backup API with SHA-256 and integrity check); `scripts/verify_database_restore.py` (non-destructive test drill). |
| **B-08** | **Production Nginx & Security Headers** | Infrastructure | **RESOLVED** | `deploy/nginx.production.conf.template` with HSTS, CSP, X-Frame-Options, X-Content-Type-Options, Permissions-Policy, rate limiting, and hidden file blocks. |
| **B-09** | **Docker Production Isolation** | Infrastructure | **RESOLVED** | `docker-compose.production.yml` isolates API port 8000 to internal network; read-only mounts for model artifacts; persistent volumes for data/backups. |
| **B-10** | **Privacy & Patient Data Notice** | Compliance & Legal | **RESOLVED** | Factual disclosure at `frontend/pages/privacy.html`, linked from index footer and shell top-sheet navigation. |
| **B-11** | **Google OAuth GIS Client ID** | Live Secret | **WAITING_FOR_OPERATOR** | Requires operator to create Web OAuth Client ID in Google Cloud Console with authorized production origin (`https://bcai.example.com`). Architecture verified. |
| **B-12** | **Production SMTP Relay Credentials** | Live Secret | **WAITING_FOR_OPERATOR** | Requires live operator credentials (`SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`) from SendGrid/SES/Postmark. Diagnostic utility verified. |
| **B-13** | **Production DNS & TLS Certificate** | Infrastructure | **WAITING_FOR_OPERATOR** | Requires operator to point DNS A/AAAA records to production host and issue Let's Encrypt certificates via Certbot runbook. |
| **B-14** | **Doctor Registration Secret Key** | Live Secret | **WAITING_FOR_OPERATOR** | Operator must generate a random high-entropy secret for `DOCTOR_INVITE_CODE` prior to public registration. |

---

## 2. Summary of Hardening Status

- **Total Engineering Blockers**: 10
- **Total Engineering Blockers Resolved**: 10 (100%)
- **Items Awaiting Operator Actions**: 4 (DNS, TLS Cert, SMTP Credentials, Google Client ID)
- **Repository Cleanliness**: Zero production secrets committed; zero unverified assets.
- **Current Classification**: **READY FOR LIVE INTEGRATION**
