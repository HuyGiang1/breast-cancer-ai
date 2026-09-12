# Pre-Deployment Hardening Blocker Status Matrix

**Phase**: Phase G2 — Live Integrations & Staging Release Candidate<br>
**Target Status**: `WAITING_FOR_OPERATOR_INPUT` (Staging-Ready; Ready for Operator Staging Details)<br>
**Current Baseline**: `feat/product-experience-v4` (Batch F + G1 + G2 Hardening)

---

## 1. Blocker Classification Matrix

This matrix tracks both engineering resolution of technical controls and external infrastructure dependencies.

| ID | Item / Subsystem | Category | Resolution Status | Technical Implementation / Operator Requirement |
| :--- | :--- | :--- | :--- | :--- |
| **B-01** | **TCIA / CBIS-DDSM Provenance & License** | Legal & Attribution | **RESOLVED** | Exact SHA-256 verified against CBIS-DDSM test set; CC BY 3.0 citations in `docs/legal/CBIS_DDSM_DATA_AND_DEMO_ATTRIBUTION.md`; card in `pages/research.html`. |
| **B-02** | **Password Storage Hardening** | Security | **RESOLVED** | Versioned `pbkdf2_sha256$600000$<salt>$<digest>` (OWASP compliant, ~129ms per hash). Backward-compatible verification for legacy hashes with transparent on-login rehash upgrade. |
| **B-03** | **CORS Fail-Closed Policy** | Security | **RESOLVED** | API raises `RuntimeError` in production if `APP_CORS_ORIGINS` is missing, `*`, contains `localhost`, or uses non-HTTPS scheme. Explicit method/header whitelists. |
| **B-04** | **API Documentation Exposure** | Security | **RESOLVED** | Swagger UI (`/docs`), ReDoc (`/redoc`), and OpenAPI spec (`/openapi.json`) are disabled when `APP_ENABLE_API_DOCS=false` (default in production). |
| **B-05** | **Health & Readiness Probes** | Operational | **RESOLVED** | `/healthz` provides liveness; `/readyz` probes live SQLite database and ML/DL model availability, returning HTTP 503 if degraded. |
| **B-06** | **SQLite WAL & Concurrency** | Database | **RESOLVED** | WAL mode (`PRAGMA journal_mode = WAL`), `synchronous = NORMAL`, `busy_timeout = 5000`, and 30s connection timeout eliminate database lock exceptions. |
| **B-07** | **Zero-Downtime Backup & Restore** | Database | **RESOLVED** | `scripts/backup_database.py` (online hot backup API with SHA-256 and integrity check); `scripts/verify_database_restore.py` (non-destructive test drill). |
| **B-08** | **Nginx Rendering & Staged HSTS** | Infrastructure | **RESOLVED** | Dynamic Nginx rendering via `scripts/render_nginx_config.py`. Staging omits HSTS to prevent domain pinning. Obsolete `X-XSS-Protection` removed. |
| **B-09** | **Docker Isolation & Non-Root User** | Infrastructure | **RESOLVED** | `backend/Dockerfile` runs unprivileged `appuser` (UID 10001). API port 8000 isolated to internal bridge. Model mounts read-only. `/var/www/certbot` volume configured. |
| **B-10** | **Privacy & Patient Data Notice** | Compliance & Legal | **RESOLVED** | Factual disclosure at `frontend/pages/privacy.html`. In-memory ephemeral Grad-CAM data URLs; zero patient images written to `/results/`; direct HTTP access to `/results/` blocked by Nginx. |
| **B-11** | **TLS Bootstrap Architecture** | Infrastructure | **RESOLVED** | `deploy/nginx.bootstrap.conf.template` provides port 80 ACME webroot challenge resolver to break chicken-and-egg dependency before certificates exist. |
| **B-12** | **Google Identity Services (GIS)** | Authentication | **RESOLVED (Architecture)** | Frontend GIS flow verified. Backend signature & audience verification. Zero client secret required. Doctor role escalation explicitly prevented. |
| **B-13** | **SMTP Transport & Delivery Engine** | Notification | **RESOLVED (Architecture)** | Provider-neutral SMTP engine supporting STARTTLS (587) and SSL (465). Tested via `scripts/test_smtp_delivery.py`. Reset token disclosure suppressed in production. |
| **B-14** | **Staging TLS Certificate** | Staging Infra | **RESOLVED (Methodology)** | Automated webroot ACME process implemented via Certbot volume mount. Ready for execution once operator supplies staging FQDN and DNS. |
| **B-15** | **Staging UAT Automation** | Quality Assurance | **RESOLVED** | Full automated regression suite passed (92 pytest, readiness check, environment audit, frontend contract checks). |
| **B-16** | **Production DNS A/AAAA Records** | Production Infra | **WAITING_FOR_OPERATOR** | Requires operator to point production DNS records to production host IP. |
| **B-17** | **Production TLS Certificate** | Production Infra | **WAITING_FOR_CUTOVER** | Requires final Let's Encrypt issuance during production cutover window. |
| **B-18** | **Production HSTS Preload** | Security Policy | **WAITING_FOR_POST-HTTPS_VALIDATION** | Initial production uses `max-age=31536000` only. `includeSubDomains` and `preload` strictly deferred until post-cutover HTTPS stability is confirmed. |
| **B-19** | **Final Production Database Backup** | Operational | **WAITING_FOR_CUTOVER** | Requires fresh pre-cutover hot backup taken immediately prior to switching traffic. |
| **B-20** | **Session / Reset Token Hashing** | Security Architecture | **P1 PRE-PRODUCTION DECISION** | Documented threat model. Cryptographically secure 32-byte urlsafe tokens currently stored. Formal migration to SHA-256 token hashing tracked for explicit review before production cutover. |

---

## 2. Summary of Hardening Status

- **Engineering Blockers Resolved**: 15 / 15 (100%)
- **Items Awaiting Operator Input (Staging)**: 1 (Staging FQDN & Server Host/SSH)
- **Items Deferred to Production Cutover Window**: 4 (Production DNS, Production TLS, Post-HTTPS HSTS, Final Production Backup)
- **Pre-Production Security Decision**: 1 (P1 Token At-Rest Hashing)
- **Repository Cleanliness**: Zero production secrets committed; zero unverified assets.
- **Current Classification**: **WAITING_FOR_OPERATOR_INPUT**
