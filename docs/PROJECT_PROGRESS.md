# Breast Cancer AI - Project Progress

Last updated: 2026-09-07

## Current stage

**Phase 4R — Feature Parity Restoration**

- Current branch: `feat/product-experience-v4`
- Baseline commits: `5b6c72c` (legacy rich functional baseline) and `8eba137` (committed V3 baseline)
- Parity matrix: `docs/v4/LEGACY_FEATURE_PARITY_MATRIX.md` (52 features cataloged, sum reconciled: 52)
- Current work: **Batch E (Doctor Workspace, Patient Registry, Patient Detail, Activity, Reports & Account Separation) COMPLETED (PASS)**
  - Implemented server-side role gating & invite code verification (`DOCTOR_REGISTRATION_MODE=invite`, `DOCTOR_INVITE_CODE`) with constant-time check (`hmac.compare_digest`), ignoring client-submitted roles.
  - Rebuilt `register.html` with Personal vs Doctor account cards and revealable doctor invite code field.
  - Rebuilt Doctor Workspace (`/pages/patients.html`) with summary metrics strip (Total Patients, Analyses Logged, ML, DL, Fusion), search/sort toolbar, accessible Add/Edit modal, and safety-explicit Delete Confirmation modal (preserving historical prediction records).
  - Implemented single-patient endpoint `GET /patients/{id}/` with doctor role and ownership isolation.
  - Rebuilt Patient Detail (`/pages/patient-detail.html`) with 3-modality quick launch buttons (`ml-analysis.html`, `dl-analysis.html`, `multimodal.html`), clinical research notes, and chronological patient analysis timeline.
  - Protected Doctor pages with Access Restricted notices when opened by Personal accounts.
  - Rebuilt Activity (`/pages/history.html`): "My Activity" (Personal) vs "Analysis Activity" (Doctor with patient selector).
  - Rebuilt Reports (`/pages/reports.html`): modality/patient filters, View Full Report, and browser-native Print / Save PDF.
  - Profile (`/pages/profile.html`): Account type breakdown, non-licensure disclaimer, and "Sign out all devices" confirmation modal calling `POST /auth/logout-all/`.
  - All automated test suites (backend security 11/11, frontend contract 11/11, static verification, broken link crawler 0 defects, Batch B/C/D regressions 100%) passed with 17 new screenshots captured.
- Next step: Batch F — await explicit user prompt. Do NOT start Batch F prematurely.

## Completed major milestones

- [x] Dataset audit and leakage-controlled CBIS-DDSM inferred-group split
- [x] WDBC ML study, calibration, bootstrap, error analysis, and SHAP
- [x] CBIS-DDSM DL baselines, validation-first ROI ablation, calibration, bootstrap, error analysis, and Grad-CAM
- [x] Frozen Logistic Regression and EfficientNet-B0 research/demo runtimes
- [x] Unified final model status and central research evidence adapter
- [x] SQLite backup/restore rehearsal, local benchmark, operational safety review, and readiness validator
- [x] Docker build/up verification, read-only model mounts, checksums, persistence, Nginx, and local smoke
- [x] Frontend Architecture V2, legacy cutover, and 84/84 cross-device route QA
- [x] Final public README and optimized eight-image screenshot set
- [x] Official 29-page Vietnamese research report in source Markdown, DOCX, and PDF
- [x] Scientific consistency/legacy wording audit and final report validator
- [x] Proposed `v1.0.0-research-demo` release notes
- [x] Server production deployment handoff

## Frozen state

- Research: **FROZEN**
- Runtime: **FROZEN**
- Frontend: **FROZEN FOR RELEASE**
- Final documentation: **COMPLETE**

## Current blockers / pending inputs

- A server is available, but access and target configuration details have not been supplied in this repository.
- Domain, DNS, HTTPS certificate configuration, and public production smoke remain pending.
- The project remains a research/educational prototype with `clinical_use=false`.

## Remaining roadmap

### Research and application

- [x] Final research evidence and candidates frozen
- [x] Final ML/DL runtimes integrated and verified
- [x] Frontend V2 frozen after full QA
- [x] Final research report and public documentation

### Server production

- [ ] Create `deploy/server-production` from `docs/final-documentation`
- [ ] Confirm SSH access, architecture, OS, CPU/RAM/disk, firewall, and Docker/Compose
- [ ] Transfer frozen model artifacts outside Git and verify SHA-256
- [ ] Configure server-only `.env`, read-only model mount, and SQLite backup
- [ ] Build/start and run local-on-server health/readiness/workflow smoke
- [ ] Configure domain, DNS, Nginx TLS, HTTPS CORS, and certificate renewal
- [ ] Run external public smoke, restart persistence, monitoring, and rollback rehearsal
- [ ] Prepare release/tag only after deployment evidence is complete

## Document roles

- `docs/PROJECT_PROGRESS.md`: simple overall roadmap and progress.
- `docs/PROJECT_STATUS.md`: detailed phase/evidence status.
- `docs/AGENT_HANDOFF.md`: exact continuation instructions for the next session.

Update this tracker before the final commit of every future phase.
