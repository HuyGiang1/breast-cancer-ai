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
| Phase 4R Batch C (Mammography DL Workstation) | RESTORED (PASS) | Medical imaging workstation on `/pages/dl-analysis.html`, runtime Grad-CAM on `top_conv` of frozen EfficientNet-B0 (`cbis-efficientnetb0-full-v1`), zero-dependency JET colormap, dual raw/Platt metric split, samples, advice, report link, AI handoff, doctor selector, 12 screenshots verified, 0 defects. |
| Phase 4R Batch D (Experimental Fusion Restoration) | RESTORED (PASS) | Dual-branch research workstation on `/pages/multimodal.html`, corrected $0.4 \times p_{\text{ml,raw}} + 0.6 \times p_{\text{dl,raw}}$ formula, prominent branch disagreement panel before combined score, unvalidated 0.50 software decision midpoint disclaimer, Grad-CAM enabled with fallback, SQLite bloat protection, shared doctor patient context, 12 screenshots verified, 0 defects. |
| Phase 4R Batch E (Doctor Workspace & Personal Separation) | RESTORED (PASS) | Server-side role gating & invite code verification (`DOCTOR_REGISTRATION_MODE`, `DOCTOR_INVITE_CODE`), Doctor Workspace with metrics strip, search/sort toolbar, safe delete dialog, single-patient API `GET /patients/{id}/`, patient detail with 3 quick launches & timeline, "My Activity" vs "Analysis Activity", printable reports with Print/Save PDF, profile capabilities breakdown, "Sign out all devices", 17 screenshots verified, 0 defects. |
| Phase 4R Batch F (Final Web Polish, AI Guide & Freeze) | RESTORED (PASS) | Strict account type contract (`Literal["personal", "doctor"]`, 422 on escalation), transient context privacy wipe on logout/login, centralized reportService, canonical prediction semantics & software midpoint disclaimers, safe DOM markdown rendering in AI Guide with multimodal grounding, separated ACS vs USPSTF screening schedules, modal accessibility, 24 screenshots verified, 0 defects. |
| Web Feature Freeze V1 | FROZEN (RC-1) | Web product feature-frozen in `docs/v4/WEB_FEATURE_FREEZE_V1.md`. Documented P0 pre-deploy blocker regarding demo mammogram TCIA attribution. Legacy feature parity: 52/52 accounted for (50 operational, 2 deferred, 0 lost). |
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
