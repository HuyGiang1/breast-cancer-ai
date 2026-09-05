# Breast Cancer AI - Project Progress

Last updated: 2026-09-05

## Current stage

**Production / Release Hardening**

- Current branch: `feat/system-finalization`
- Base branch: `feat/final-dl-runtime-integration`
- Next branch: `ops/production-readiness`

## Completed major milestones

- [x] Dataset audit and leakage-safe CBIS-DDSM split
- [x] Final DL baselines and validation-first ROI ablation
- [x] DL calibration, error analysis, bootstrap CI, and Grad-CAM
- [x] Final WDBC ML study and SHAP analysis
- [x] Reproducible paper artifacts and final research synthesis
- [x] Logistic Regression frozen and integrated as a research/demo runtime
- [x] EfficientNet-B0 full-image candidate frozen
- [x] Final Platt calibration artifact frozen and metric-equivalent

## Current work

- [x] Integrate the frozen EfficientNet-B0 full-image candidate into the research/demo runtime.
- [x] Keep classification in raw probability space at threshold `0.515`.
- [x] Use the frozen Platt transform only for calibrated display/reliability probability.
- [x] Expose unified final ML/DL model status without promoting clinical use.
- [x] Final research dashboard and frontend final-runtime integration.
- [x] Research/demo safety and application verification.

## Blockers

- DL runtime is research/demo only; it must not reuse legacy Custom CNN calibration or refit Platt.
- Public deployment still requires VPS, domain, and HTTPS access from the project owner.
- The project remains a research/educational prototype, not a clinical diagnostic system.

## Remaining roadmap

### Application

- [x] FastAPI base system, authentication, patient management, and prediction history
- [x] Final ML runtime
- [x] Final DL runtime
- [x] Unified model status
- [x] Final research dashboard
- [x] Frontend polish

### Production

- [ ] End-to-end benchmark
- [ ] Docker final verification
- [ ] CI release validation
- [ ] Safety review
- [ ] Deployment
- [ ] HTTPS

### Documentation

- [x] Final research results, paper tables, paper figures, and report update notes
- [ ] Update final Word report
- [ ] Update final PDF
- [ ] Final README
- [ ] Release notes

## Document roles

- `docs/PROJECT_PROGRESS.md`: human-readable overall roadmap and progress.
- `docs/PROJECT_STATUS.md`: detailed phase status and evidence.
- `docs/AGENT_HANDOFF.md`: technical continuation instructions for the next agent session.

Update this tracker before the final commit of every future phase.
