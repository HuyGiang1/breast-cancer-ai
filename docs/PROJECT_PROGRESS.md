# Breast Cancer AI - Project Progress

Last updated: 2026-09-07

## Current stage

**Frontend Architecture V2 - Batch 7 complete**

- Current branch: `feat/frontend-architecture-v2`
- Base branch: `feat/frontend-premium-redesign`
- Current work: Batch 8 full route and cross-device QA
- Next stage after Batch 8: `docs/final-documentation` (do not create automatically)

## Completed major milestones

- [x] Dataset audit and leakage-safe CBIS-DDSM split
- [x] Final DL baselines, validation-first ROI ablation, calibration, error analysis, bootstrap CI, and Grad-CAM
- [x] Final WDBC ML study, SHAP analysis, paper artifacts, and research synthesis
- [x] Frozen Logistic Regression and EfficientNet-B0 research/demo runtimes
- [x] Unified final model status and research dashboard
- [x] CI release validation for production-readiness (`33945903158`, commit `8fce90d`)
- [x] SQLite backup and safe temporary-database restore rehearsal
- [x] Final local runtime benchmark and production-readiness validator
- [x] Operational safety review and deployment runbook
- [x] Docker final verification: build, healthy compose stack, mounted model checksums, ML/DL smoke, snapshot provenance, restart persistence, Nginx assets, and safe shutdown
- [x] Premium responsive frontend redesign with evidence-first research dashboard, grouped ML inputs, DL upload UX, and threshold-aware result display
- [x] Frontend V2 canonical route migration and Batch 7 legacy monolith/style cutover
- [ ] Batch 8 full route and cross-device frontend QA

## Blockers

- VPS, domain, and HTTPS credentials have not been provided.
- The project remains a research/educational prototype, not a clinical diagnostic system.

## Remaining roadmap

### Application

- [x] FastAPI base system, authentication, patient management, and prediction history
- [x] Final ML/DL runtimes, unified status, and premium frontend redesign
- [x] Frontend V2 canonical migration and legacy cutover through Batch 7
- [ ] Batch 8 full route and cross-device frontend QA

### Production

- [x] End-to-end local benchmark
- [x] Docker final verification
- [x] Safety review
- [x] CI validation for the production-readiness commit set
- [ ] Deployment (blocked: VPS not provisioned)
- [ ] HTTPS (blocked: domain/VPS not provisioned)

### Documentation

- [x] Final research results, paper tables, figures, update notes, deployment runbook, safety review, and backup/restore procedure
- [ ] Update final Word report
- [ ] Update final PDF
- [ ] Final README
- [ ] Release notes

## Document roles

- `docs/PROJECT_PROGRESS.md`: human-readable overall roadmap and progress.
- `docs/PROJECT_STATUS.md`: detailed phase status and verification evidence.
- `docs/AGENT_HANDOFF.md`: exact continuation instructions for the next agent session.

Update this tracker before the final commit of every future phase.
