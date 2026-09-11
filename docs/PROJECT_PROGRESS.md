# Breast Cancer AI - Project Progress

Last updated: 2026-09-07

## Current stage

**Phase 4R — Feature Parity Restoration**

- Current branch: `feat/product-experience-v4`
- Baseline commits: `5b6c72c` (legacy rich functional baseline) and `8eba137` (committed V3 baseline)
- Parity matrix: `docs/v4/LEGACY_FEATURE_PARITY_MATRIX.md` (52 features cataloged, sum reconciled: 52)
- Current work: **Batch D (Experimental Fusion Restoration & Scientific Contract Alignment) COMPLETED (PASS)**
  - Corrected multimodal probability bug: fusion formula strictly uses $0.4 \times p_{\text{ml,raw}} + 0.6 \times p_{\text{dl,raw}}$, strictly eliminating Platt-calibrated DL display probability from the weighted combination formula.
  - Rebuilt `/pages/multimodal.html` into a dual-branch workstation: full Structured ML branch (30 features, development references, presets, CSV, OCR, outlier safeguards) and Mammography DL branch (dropzone, presets, metadata, Grad-CAM viewer).
  - Converging execution hub with mathematical formula visualizer and unvalidated 0.50 software decision midpoint disclaimer.
  - Prominent **Branch Disagreement** panel rendered *before* the combined score whenever model classifications conflict, with explicit educational explanation of unpaired dataset limitations (WDBC vs CBIS-DDSM).
  - Transparent Branch Agreement banner when independent classifications match.
  - Enabled Grad-CAM runtime in multimodal flow (`include_explanation=true`) with fail-safe fallback if Grad-CAM fails.
  - SQLite bloat safeguard: stripped `explanation_image` base64 data URLs before `db.save_prediction()`.
  - Restored unified doctor patient linkage context, authenticated printable report link, and contextual AI Guide handoff (`analysis_type: 'fusion'`).
  - All regression suites (Batches B, C, D, link crawler, pytest 61/61) passed with 0 defects (12 screenshots captured).
- Next step: Batch E (Doctor Workspace, Patient Registry, Patient Detail, History, Reports, Account-Type Registration) — await explicit user prompt. Do NOT start Batch E prematurely.

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
