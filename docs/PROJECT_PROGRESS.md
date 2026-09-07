# Breast Cancer AI - Project Progress

Last updated: 2026-09-07

## Current stage

**Final documentation complete**

- Current branch: `docs/final-documentation`
- Base branch: `feat/frontend-architecture-v2`
- Current work: final README, report, validation, release notes, and deployment handoff complete
- Next stage: `deploy/server-production` (do not create automatically)

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
