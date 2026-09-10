# Breast Cancer AI - Project Progress

Last updated: 2026-09-07

## Current stage

**Phase 4R — Feature Parity Restoration**

- Current branch: `feat/product-experience-v4`
- Baseline commits: `5b6c72c` (legacy rich functional baseline) and `8eba137` (committed V3 baseline)
- Parity matrix: `docs/v4/LEGACY_FEATURE_PARITY_MATRIX.md` (52 features cataloged, sum reconciled: 52)
- Current work: **Batch B (Structured ML Parity & Workstation Rebuild) COMPLETED (PASS)**
  - Fully rebuilt `/pages/ml-analysis.html` into a professional data-lab analysis workstation.
  - Reproducible WDBC development reference artifact (`scripts/build_wdbc_feature_reference.py`, N=455, test excluded).
  - Restored canonical Benign and Malignant research presets without auto-prediction.
  - Restored Clear All action with confirmation safeguard.
  - Restored robust multi-format CSV import with multi-row interactive preview and CSV template download.
  - Restored lab report image OCR feature extraction review modal.
  - Added live 4-tier development reference validation and outlier safeguard confirmation modal.
  - Implemented exact closed-form frozen Logistic Regression log-odds contributions ($z_i = w_i \cdot \frac{x_i - \mu_i}{\sigma_i}$) matching `predict_proba` with $\Delta < 10^{-12}$.
  - Restored educational AI advice display with provider badges and added general wellbeing guidance.
  - Restored authenticated printable report link and contextual AI advisor handoff via `sessionStorage`.
  - Restored doctor-only patient linkage selector with strict ownership RBAC.
  - All automated tests, crawlers, and browser E2E suites passing with 0 defects.
- Next step: Batch C (Mammography DL + Frozen Grad-CAM Restoration) — await explicit user prompt.

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
