# Breast Cancer AI - Project Progress

Last updated: 2026-09-07

## Current stage

**Phase 4R — Feature Parity Restoration**

- Current branch: `feat/product-experience-v4`
- Baseline commits: `5b6c72c` (legacy rich functional baseline) and `8eba137` (committed V3 baseline)
- Parity matrix: `docs/v4/LEGACY_FEATURE_PARITY_MATRIX.md` (52 features cataloged, sum reconciled: 52/52)
- Current work: **Batch F (Final Web Product Polish, AI Guide, Scientific Copy & Feature Freeze) COMPLETED (PASS)**
  - Strict account type contract enforced on registration (`Literal["personal", "doctor"]`, rejects `admin` or invalid values with HTTP 422).
  - Transient context privacy guaranteed (`auth.clearTransientContext()`) clearing `bcai_advisor_context`, `bcai_active_analysis`, and `bcai_patient_context` across logout and login.
  - Centralized authenticated report open/print service (`reportService.fetchBlob`, `open`, `print`) across all pages.
  - Canonical prediction semantics enforced across Structured ML, Mammography DL, and Fusion.
  - AI Guide rebuilt with safe DOM markdown rendering (`renderSafeContent` with zero unsafe `innerHTML`), multimodal context grounding (40/60 weighting, 0.5 midpoint, unpaired disclaimer), progressive disclosure, and English safety guardrails.
  - Sourced screening schedules visibly separating ACS (Oeffinger et al.) vs USPSTF (2024 update) guidelines with authoritative citations.
  - Accessible modals with Tab focus trap, Escape key listener, return focus to trigger, and body scroll locking (`bindModalAccessibility`).
  - Corrected Batch E false-pass items (doctor patient filtering across full history, Date Range filters, active count badges).
  - Web feature freeze declared in `docs/v4/WEB_FEATURE_FREEZE_V1.md` with documented Pre-Deploy Blocker regarding demo mammogram TCIA attribution.
  - Full regression suite passing 100% across all batches (A–F, 73 Pytest, 0 broken links, 24 representative screenshots).
- Next step: Pre-deployment staging configuration and external infrastructure setup. Do NOT modify frozen web application code without explicit unfreeze approval.

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
