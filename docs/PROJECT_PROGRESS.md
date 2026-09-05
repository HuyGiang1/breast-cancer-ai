# Breast Cancer AI - Project Progress

Last updated: 2026-09-05

## Current stage

**Final Model Runtime Integration**

- Current branch: `research/freeze-dl-calibration-artifact`
- Base branch: `feat/final-model-runtime-integration`
- Next branch: `feat/final-dl-runtime-integration`

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

- [ ] Integrate the frozen EfficientNet-B0 full-image candidate into the research/demo runtime.
- [ ] Keep classification in raw probability space at threshold `0.515`.
- [ ] Use the frozen Platt transform only for calibrated display/reliability probability.
- [ ] Expose unified final ML/DL model status without promoting clinical use.

## Blockers

- DL runtime integration has not yet been implemented; it must not reuse legacy Custom CNN calibration or refit Platt.
- Public deployment still requires VPS, domain, and HTTPS access from the project owner.
- The project remains a research/educational prototype, not a clinical diagnostic system.

## Remaining roadmap

### Application

- [x] FastAPI base system, authentication, patient management, and prediction history
- [x] Final ML runtime
- [ ] Final DL runtime
- [ ] Unified model status
- [ ] Final research dashboard
- [ ] Frontend polish

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
