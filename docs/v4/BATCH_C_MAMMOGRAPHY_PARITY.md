# Phase 4R — Batch C: Mammography DL Feature Parity Audit

**Branch**: `feat/product-experience-v4`  
**Date**: September 11, 2026  
**Reference Legacy Commit**: `5b6c72c5ae1d4cb4e16bb9989dd6adfb49a5d99a`  
**Current Product State**: Modular V4 (`8be3ed5`)  
**Scientific Contract**: Study B (CBIS-DDSM Full Processed Image, EfficientNet-B0, $224 \times 224 \times 3$, frozen raw malignant cutoff $\ge 0.515$, Platt calibration display-only).

---

## 1. Feature Parity Audit Table

| Legacy Feature | Legacy Behavior (`5b6c72c`) | Current V4 Pre-Batch-C State | Scientific Compatibility | Batch C Action |
| :--- | :--- | :--- | :--- | :--- |
| **`predictDl` Workflow** | Form submitted `file`, `model_name`, `patient_id`, `include_explanation=true` to `/api/v1/predict/image/`. | `predictionService.dl` in `frontend/js/pages/dl-analysis.js` submitted `includeExplanation: false` by default. | Fully compatible with frozen EfficientNet-B0. | **RESTORE & IMPROVE**: Ensure frontend always sends `include_explanation=true`, handle real staged progress, and render rich workstation. |
| **`setSelectedDlImage` & Preview** | Set `state.selectedDlImageFile`, created blob URL, showed thumbnail in upload shell, displayed filename and KB. | Basic dropzone rendered thumbnail, but lacked dimensions, MIME, and large workstation view. | Fully compatible. | **IMPROVE**: Render large high-resolution inspection canvas with metadata pill (dimensions, size, MIME type, preprocessing pipeline). |
| **`loadDemoDlImage` (Demo Presets)** | Loaded `assets/demo-images/demo-benign-mammogram.png` and `demo-malignant-mammogram.png` via fetch into file. | Assets were deleted during legacy monolith retirement (`c6ecccf`). | Pre-existing committed research assets in `5b6c72c` (224x224 RGB PNGs); verified safe provenance. | **RESTORE**: Restore canonical benign and malignant demo presets into `frontend/assets/demo-images/` without auto-running prediction. |
| **`include_explanation` Parameter** | Passed `include_explanation=true` in query URL. | Parameter was hardcoded to `false` in V3 frontend. | Required for runtime XAI. | **RESTORE**: Ensure frontend always requests `include_explanation=true`. Add unit test to prevent regression. |
| **Grad-CAM Attention Display** | Displayed single heatmap image returned from legacy CNN backend. | Backend returned `explanation_image: null`; no Grad-CAM displayed. | Incompatible with legacy CNN; must target `top_conv` on frozen EfficientNet-B0. | **SCIENTIFICALLY INCOMPATIBLE → REIMPLEMENT AGAINST FINAL MODEL**: Implement real GradientTape Grad-CAM on `top_conv` of frozen EfficientNet-B0. |
| **Heatmap Overlay & Visualization Modes** | Displayed single overlay image in a small figure container. | Omitted from result card. | Fully compatible. | **IMPROVE**: Medical workstation inspection modes: Side-by-Side (default desktop), Original Only, and Grad-CAM Overlay with interactive switcher. |
| **Drag & Drop Upload Zone** | File dropzone with dragover class and file input trigger. | Basic dropzone present in V3. | Fully compatible. | **IMPROVE**: Premium large medical dropzone with keyboard accessibility, clear visual state, and Replace/Remove buttons. |
| **Patient Linkage (`patient_id`)** | Doctor could attach prediction to selected patient via dropdown. | Query param supported by backend, but UI lacked patient selector dropdown. | Fully compatible. | **RESTORE**: Add doctor-only patient selector bar (mirrors Batch B) with strict RBAC enforcement. |
| **AI Clinical Advice Display** | Dedicated advice card displaying advice narrative and provider/model badge. | Dropped by V3 frontend result card despite backend returning payload. | Fully compatible. | **RESTORE**: Re-render "AI Educational Guidance" with provider and model badges and safe educational disclaimers. |
| **Printable Report Link** | Button to download/open persisted prediction report `/api/v1/predictions/{id}/report/`. | Missing on analysis result page. | Fully compatible. | **RESTORE**: Add prominent "View Analysis Report" action linking directly to persisted HTML report. |
| **History Persistence** | Automatically persisted prediction and loaded recent history table. | Persisted in SQLite, but lacked direct link back to workstation view. | Fully compatible. | **PRESERVED & IMPROVED**: Ensure prediction ID and metadata are returned and history records attach cleanly without bloating SQLite. |
| **Decision Threshold & Calibration Display** | Mixed raw threshold and Platt calibrated probability in the same card with confusing risk labels. | Displayed raw cutoff 0.515 and Platt calibrated prob, but risk bands were ambiguous. | Platt is display-only; decision is strictly raw $\ge 0.515$. | **IMPROVE**: Strictly decouple into two distinct panels: Model Classification (Raw $\ge 0.515$) and Calibrated Display Probability (Platt display only). |
| **Reset / Remove Image Action** | Reset input and cleared preview via `clearSelectedDlImage()`. | Clear action was missing after prediction. | Fully compatible. | **RESTORE**: Add "Analyze Another Image" and "Remove Image" actions with clean `URL.revokeObjectURL` memory cleanup. |
| **AI Advisor Contextual Handoff** | Generic button linking to chat assistant. | Omitted in V3. | Fully compatible. | **RESTORE & IMPROVE**: Add "Ask AI Guide About This Result" passing structured context via `sessionStorage` (`bcai_advisor_context`) without URL leakage. |

---

## 2. Key Architectural Decisions

1. **Model & Layer Invariance**:
   - The frozen model is `cbis-efficientnetb0-full-v1` ($224 \times 224 \times 3$).
   - The target convolutional layer is confirmed as `top_conv` in the EfficientNet backbone.
   - Output scalar represents raw malignant probability.
   - Classification is governed strictly by $\text{raw\_probability} \ge 0.515$.
2. **Tensor Identity**:
   - The exact same preprocessed tensor ($224 \times 224 \times 3$, float32) must be used for both inference and Grad-CAM.
   - No alternative normalization or resizing paths.
3. **Fail-Closed Fallback**:
   - If Grad-CAM fails for any reason during runtime, inference must still return successfully with `explanation_status: "unavailable"` and `explanation_image: null`.
4. **Database Hygiene**:
   - Base64 explanation overlay strings must not be written to `predictions.response_payload` in SQLite to prevent database bloat.
