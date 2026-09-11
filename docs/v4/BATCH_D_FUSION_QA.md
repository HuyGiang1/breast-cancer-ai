# Phase 4R — Batch D: Experimental Fusion QA & Validation Report

**Branch**: `feat/product-experience-v4`  
**Date**: September 12, 2026  
**Status**: PASS  
**Test Suite**: `tests/test_final_multimodal_fusion.py`, `scripts/test_fusion_frontend_contract.js`, `scripts/qa_batch_d_e2e.js`

---

## 1. Feature Restoration Matrix (Before vs Current Pre-Batch-D vs After)

| Feature | Before (Legacy `5b6c72c`) | Current Pre-Batch-D (`cfc5dc4`) | After (Batch D Restored) | Regression Check |
| :--- | :--- | :--- | :--- | :--- |
| **Probability Space Formulation** | Mixed raw ML ($p_{\text{ml,raw}}$) with Platt-calibrated DL ($p_{\text{dl,calibrated}}$). | Mixed raw ML with Platt-calibrated DL in $0.4/0.6$ heuristic. | Strictly uses raw model probabilities: $0.4 \times p_{\text{ml,raw}} + 0.6 \times p_{\text{dl,raw}}$. Excludes calibrated DL from formula. | `test_final_multimodal_fusion.py::test_fusion_formula_uses_raw_probabilities` (PASS) |
| **Combined Score Semantics** | Claimed "Độ tin cậy của kết luận tổng hợp" and "Nguy cơ tổng hợp". | Displayed ambiguous `combined_confidence`. | Labeled as "Experimental Combined Score" (`combined_malignant_score`), $0.50$ software decision midpoint disclaimer, no clinical risk band. (Note: legacy `combined_confidence` is preserved in backend payload as predicted-side confidence for backward compatibility, but marked DEPRECATED for V4 UI). | `test_fusion_frontend_contract.js` (PASS) |
| **Branch Disagreement Handling** | Ignored; silently averaged conflicting classifications. | Brief uncertainty string buried in payload; combined score overruled branch outputs. | Prominent, high-priority **BRANCH DISAGREEMENT** panel displayed BEFORE combined score; explains unvalidated nature of combination. | `qa_batch_d_e2e.js` (PASS, screenshots captured) |
| **Branch Agreement Handling** | Treated as clinical validation. | Generic card rendering. | **BRANCH AGREEMENT** banner explicitly stating agreement does not validate combination due to unpaired data. | `qa_batch_d_e2e.js` (PASS) |
| **Formula Visualizer** | Omitted; only showed combined percentage. | Single percentage number. | Live interactive visualizer detailing actual raw numbers: $p_{\text{ml}} \times 0.40 + p_{\text{dl}} \times 0.60 = \text{Combined Score}$. | `qa_batch_d_e2e.js` (PASS) |
| **Structured ML Inputs** | No 30 inputs on fusion tab; only CSV/OCR into background state. | 30 plain numeric inputs without reference ranges or units. | Full 30-feature workstation matching Batch B: WDBC descriptions, reference ranges, live status, outlier safeguards, research presets. | `qa_batch_d_e2e.js` (PASS) |
| **Mammography DL Upload** | Basic thumbnail preview. | Minimal file dropzone. | Full medical imaging dropzone matching Batch C: JPEG/PNG validation, dimensions, size, thumbnail, Replace/Remove, research presets. | `qa_batch_d_e2e.js` (PASS) |
| **Grad-CAM Attention in Fusion** | Sent `include_explanation=true`, but old CNN model was retired. | Hardcoded `include_explanation=false`; no Grad-CAM in fusion. | Enabled `include_explanation=true`; Grad-CAM on `top_conv` returned in DL branch with Side-by-Side viewer. | `qa_batch_d_e2e.js` (PASS) |
| **Database Persistence Bloat** | Stored full payload into SQLite without stripping base64 images. | No base64 image generated. | Base64 `explanation_image` strictly stripped from `dl_result` before `db.save_prediction`. Metadata retained. | `test_final_multimodal_fusion.py::test_database_persistence_strips_base64` (PASS) |
| **Doctor Shared Patient Context** | Dropdown existed, but patient assignment was decoupled across models. | Missing on fusion page. | Uniform patient context bar near top; one shared patient ID applied to both branches with strict RBAC. | `qa_batch_d_e2e.js` (PASS) |
| **AI Guide Handoff** | Generic link to chat without context. | Missing. | "Ask AI Guide About This Fusion Result" passing structured fusion context (ML raw, DL raw, agreement, formula) via `sessionStorage`. | `qa_batch_d_e2e.js` (PASS) |
| **Analysis Report** | Broken or basic summary. | Omitted. | "View Analysis Report" linking to `/api/v1/predictions/{id}/report/` with dedicated multimodal report template. | `qa_batch_d_e2e.js` (PASS) |
| **Reset Workflow** | Incomplete reset leaving DOM artifacts. | Incomplete. | "Reset Fusion" clearing 30 fields, CSV, OCR, image, preview, Grad-CAM, results, preserving session. | `qa_batch_d_e2e.js` (PASS) |

---

## 2. Demo Asset Provenance Analysis (CBIS-DDSM Demos)

As restored in Batch C and reused in Batch D:
- `frontend/assets/demo-images/demo-benign-mammogram.png` ($224 \times 224$ RGB PNG, 80.4 KB)
- `frontend/assets/demo-images/demo-malignant-mammogram.png` ($224 \times 224$ RGB PNG, 80.8 KB)

### Provenance Audit:
1. **Origin**: Sourced from the historical repository commit `5b6c72c5ae1d4cb4e16bb9989dd6adfb49a5d99a` where they were committed under `frontend/assets/demo-images/`.
2. **Dataset Basis**: These images are derived from the public CBIS-DDSM (Curated Breast Imaging Subset of Digital Database for Screening Mammography) dataset hosted on TCIA (The Cancer Imaging Archive).
3. **Redistribution Basis**: CBIS-DDSM is distributed under the Creative Commons Attribution 3.0 Unported License (CC BY 3.0), requiring attribution to the CBIS-DDSM authors and TCIA.
4. **Pre-Deploy Safety Status**:
   - For internal development and research prototype evaluation: **SAFE**.
   - For commercial or external production deployment: **PRE-DEPLOY BLOCKER**. Before public production release, explicit TCIA citation attribution must be embedded in public legal disclaimers, or synthetic mammogram assets must be substituted.

---

## 3. Measured Performance Profile (Descriptive Only — Not an SLA Claim)

| Component | Measured Execution Time | Measurement Context |
| :--- | :--- | :--- |
| **Model Forward Pass Time** | ~112.28 ms | EfficientNet-B0 forward pass ($1 \times 224 \times 224 \times 3$) on CPU (10-run mean). |
| **Grad-CAM Math / Postprocessing** | ~239.77 ms | Gradient computation on `top_conv`, channel weighting, colormap application, base64 encoding (10-run mean). |
| **Full Backend API Request Time** | ~450–750 ms | Combined ML inference + DL inference + Grad-CAM + rule combination + SQLite persistence + AI advice. |
| **Browser-Observed Request Time** | ~600–900 ms | Total network turnaround observed in headless Chrome browser suite. |

---

## 4. Visual Evidence Verification (12 Screenshots)

1. `v4-d-fusion-empty-1440.png`: Desktop empty workstation showing dual branches, unpaired banner, 0/30 features, and empty dropzone.
2. `v4-d-fusion-ready-1440.png`: Workstation ready state with 30/30 features complete and mammogram image loaded.
3. `v4-d-fusion-running-1440.png`: Live execution tracking card showing pipeline stages.
4. `v4-d-fusion-agreement-1440.png`: Branch Agreement banner when both branches classify as Benign.
5. `v4-d-fusion-disagreement-1440.png`: High-visibility **BRANCH DISAGREEMENT** panel displayed prominently before combined score.
6. `v4-d-fusion-formula-1440.png`: Transparent mathematical visualizer showing exact raw numbers and weights ($0.40$ / $0.60$).
7. `v4-d-fusion-gradcam-1440.png`: Grad-CAM interactive viewer in DL branch with Side-by-Side comparison.
8. `v4-d-fusion-ai-guidance-1440.png`: AI Educational Guidance section detailing non-diagnostic recommendations.
9. `v4-d-fusion-doctor-patient-1440.png`: Shared doctor patient context bar binding both branches to a single patient.
10. `v4-d-fusion-empty-390.png`: Mobile empty workstation at 390px showing responsive stacking without horizontal scroll.
11. `v4-d-fusion-result-390.png`: Mobile results view at 390px showing stacked formula and combined score.
12. `v4-d-fusion-disagreement-390.png`: Mobile disagreement warning box at 390px.
