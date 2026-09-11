# Agent Handoff

## Current state

- Repository: `https://github.com/HuyGiang1/breast-cancer-ai`
- Current branch: `feat/product-experience-v4`
- Base commit: `8eba137` (committed V3 baseline)
- Functional baseline commit: `5b6c72c` (legacy monolithic rich frontend)
- Research: **FROZEN**
- Runtime: **FROZEN**
- Frontend: **PHASE 4R BATCH E COMPLETED (PASS)**
- Parity matrix: `docs/v4/LEGACY_FEATURE_PARITY_MATRIX.md` (52 features cataloged, sum reconciled: 52)
- QA reports: `docs/v4/BATCH_A_HOME_RESEARCH_LEARN_QA.md`, `docs/v4/BATCH_B_STRUCTURED_ML_QA.md`, `docs/v4/BATCH_C_MAMMOGRAPHY_DL_QA.md`, `docs/v4/BATCH_D_FUSION_QA.md`, `docs/v4/BATCH_E_DOCTOR_PERSONAL_WORKSPACE_QA.md`
- Next phase: Batch F — await explicit user instruction. Do NOT start Batch F prematurely.

Do not retrain, change datasets/splits, tune on test, change thresholds/calibration/model selection, redesign the frontend, validate multimodal fusion, claim clinical use, merge main, tag, or create a release without explicit instruction.

## Final documentation evidence

- `README.md`: public research platform entry point.
- `docs/report/FINAL_RESEARCH_REPORT_VI.md`: official reproducible Vietnamese source.
- `docs/report/NGHIEN_CUU_CAC_MO_HINH_NHAN_DANG_PHAN_LOAI_KHOI_U_VU_AC_TINH.docx`: final DOCX.
- Matching `.pdf`: 29 pages, visually inspected page by page.
- `docs/FINAL_REPORT_VALIDATION.md`: scientific/content/visual QA evidence.
- `docs/RELEASE_NOTES.md`: proposed `v1.0.0-research-demo`; not tagged.
- `docs/DEPLOYMENT_RUNBOOK.md`: canonical server procedure.

## Scientific contract

- Study A: WDBC, 569 samples, 30 FNA-derived numerical features, 455 development, 114 held-out test, seed 42. Logistic Regression selected from development OOF; raw threshold `0.36`.
- Study B: CBIS-DDSM, 2,559 processed source images plus 2,559 ROI representations, 5,118 manifest rows, 2,354 inferred study-like groups, zero measured group overlap. Not verified patient-level. EfficientNet-B0 full image; raw threshold `0.515`.
- Frozen Platt: displayed/reliability probability only, never the class decision threshold input.
- SHAP: contribution to malignant log-odds, non-causal. Grad-CAM: coarse attention, not segmentation/localization/pathology evidence.
- WDBC and CBIS-DDSM are unpaired; 40/60 fusion is `experimental_only`.

## Next phase procedure

Create `deploy/server-production` from this branch only after this branch is pushed and CI is green. The user has a server. Ask only for the target connection/configuration facts needed at execution time; never request committing SSH keys or passwords.

Follow `docs/DEPLOYMENT_RUNBOOK.md`: architecture/OS/resource/firewall preflight, Docker/Compose, server-only `.env`, external model transfer and SHA-256, SQLite backup, read-only mount, build/start, health/readiness, local server workflow smoke, domain/DNS/HTTPS, restart persistence, external public smoke, and rollback evidence.

## Required regression gates

```bash
find frontend/js -name "*.js" -print0 | xargs -0 -n1 node --check
python3 scripts/verify_frontend_v2.py
git diff --check
PYTHONPATH=.:backend venv/bin/python -m pytest -q
python3 -m compileall backend/app scripts tests
PYTHONPATH=.:backend venv/bin/python scripts/verify_final_application.py
PYTHONPATH=.:backend venv/bin/python scripts/verify_production_readiness.py
venv/bin/python scripts/build_final_report.py
venv/bin/python scripts/validate_final_report.py
```

The pre-existing Pydantic V2 class-config warning may remain. Stop local Docker with `docker compose down`, never `down -v`.
