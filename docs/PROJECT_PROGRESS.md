# Breast Cancer AI - Project Progress

Last updated: 2026-09-05

## Current stage

**Production Readiness - Docker verification blocked locally**

- Current branch: `ops/production-readiness`
- Base branch: `feat/system-finalization`
- Next branch: not authorized until the Docker gate is verified; then `docs/final-documentation`

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

## Current work

- [ ] Start Docker Desktop/daemon and execute actual `docker compose build`, `up`, health, mounted-artifact, snapshot, prediction-smoke, restart, and `down` gates.

## Blockers

- Docker daemon is unavailable on the current machine, so containerized verification has not run.
- VPS, domain, and HTTPS credentials have not been provided.
- The project remains a research/educational prototype, not a clinical diagnostic system.

## Remaining roadmap

### Application

- [x] FastAPI base system, authentication, patient management, and prediction history
- [x] Final ML/DL runtimes, unified status, dashboard, and frontend polish

### Production

- [x] End-to-end local benchmark
- [ ] Docker final verification (blocked: Docker daemon unavailable)
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
