# Project Status

Last updated: 2026-09-07

| Phase | Status | Evidence |
| --- | --- | --- |
| Dataset and research protocol | FROZEN | Final manifest, overlap checks, ML/DL studies, ROI decision, calibration, error analysis, CI, XAI, and paper artifacts under `experiments/final/`. |
| Final model selection | FROZEN | WDBC Logistic Regression raw threshold `0.36`; CBIS EfficientNet-B0 full image raw threshold `0.515`; frozen Platt display only. |
| Final runtime integration | FROZEN | Checksum-verified fail-closed services, runtime parity, final status, and application smoke. |
| Production readiness | DONE | CI, backup/restore rehearsal, local benchmark, safety review, validator, Docker mounts/checksums/persistence, Nginx, and controlled-error smoke passed. |
| Frontend Architecture V2 | FROZEN FOR RELEASE | 21 canonical routes, modular ES Modules, legacy bundle retirement, and 84/84 route/viewport QA. |
| Frontend Redesign V3 | READY FOR UAT | 21 canonical routes, top navigation mega-menus, glassmorphic design system, and full regression verification (`8eba137`). |
| Phase 4R Batch A (Overview/Learn/Research) | RESTORED (PASS) | Canonical authenticated/guest Overview on `index.html`, `#research` storytelling, `#learn` hub, dashboard compatibility redirect, 7 screenshots verified, 0 defects. |
| Phase 4R Batch B (Structured ML Workstation) | RESTORED (PASS) | Professional workstation on `/pages/ml-analysis.html`, WDBC development reference (N=455), samples, clear, CSV import/template, OCR preview, outlier safeguard, exact LR contributions ($\Delta < 10^{-12}$), advice/wellbeing, report link, AI handoff, doctor patient selector, 10 screenshots verified, 0 defects. |
| Final README and screenshots | DONE | Final public entry point and eight optimized, disposable-data screenshots. |
| Official report | DONE | `docs/report/FINAL_RESEARCH_REPORT_VI.md` generated into matching 29-page DOCX/PDF with final paper artifacts and platform screenshots. |
| Report validation | DONE | `scripts/validate_final_report.py` plus `docs/FINAL_REPORT_VALIDATION.md`; scientific facts, structure, page completeness, and wording gates pass. |
| Release notes | DONE | Proposed `v1.0.0-research-demo` notes; no release/tag created. |
| Server deployment | READY | Server availability confirmed. Access/configuration, target preflight, model transfer, domain/DNS/HTTPS, and external smoke remain pending. |

## Scientific and safety boundaries

- WDBC ML and CBIS-DDSM DL are separate studies; there is no cross-dataset ranking.
- The 5,118 CBIS manifest rows are not independent mammograms or patients.
- CBIS grouping is inferred study-like grouping, not verified patient-level grouping.
- ML classification uses raw `>= 0.36`; DL classification uses raw `>= 0.515`; Platt is display/reliability only.
- Multimodal weighting is `experimental_only` and has no paired-data validation.
- SHAP is non-causal; Grad-CAM is qualitative coarse attention.
- All final APIs are research/demo only with `clinical_use=false`.
- Raw data, runtime model binaries, SQLite application data, backups, and `.env` are not committed.
