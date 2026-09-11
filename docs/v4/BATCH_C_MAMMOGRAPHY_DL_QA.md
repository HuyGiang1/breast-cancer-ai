# Batch C — Mammography DL Restoration & Final EfficientNet-B0 Grad-CAM QA Report

**Document Version**: 1.0.0  
**Date**: 2026-09-11  
**Branch**: `feat/product-experience-v4`  
**Evaluation Target**: Mammography Research Analysis Workstation (`/pages/dl-analysis.html`) & Runtime Grad-CAM Engine  
**Scientific Contract Baseline**:
- Model Architecture: `EfficientNet-B0` (CBIS-DDSM Full Processed Image)
- Model Identifier: `cbis-efficientnetb0-full-v1`
- Input Dimension: `224 × 224 × 3`
- Decision Cutoff: `raw_probability >= 0.515` (strictly drives model classification)
- Post-Hoc Calibration: Frozen Platt scaling (isolated strictly to display reliability)
- XAI Convolutional Target: `top_conv` (inside nested EfficientNet-B0 backbone)
- XAI Method: Gradient-weighted Class Activation Mapping (`Grad-CAM`) with zero-dependency `JET_LUT` colormap

---

## 1. Executive Summary & Gate Status

| Verification Gate | Required Standard | Observed Result | Status |
| :--- | :--- | :--- | :---: |
| **Model Immutability** | Frozen weights, no retraining, no parameter modifications | Exact candidate loaded from `models/final/` | **PASS** |
| **Scientific Decoupling** | Raw threshold $\ge 0.515$ strictly drives classification; Platt display isolated | Exact parity verified in automated tests | **PASS** |
| **Target Layer Fidelity** | Target convolutional layer is `top_conv` inside backbone | Resolved via `model.get_layer('efficientnetb0').get_layer('top_conv')` | **PASS** |
| **Colormap Portability** | Zero-dependency overlay generation without external matplotlib library | Precomputed 256-level RGB `JET_LUT` array | **PASS** |
| **Numerical Parity Hard Gate** | `raw_probability` identical with vs without explanation ($\Delta \le 10^{-7}$) | $\Delta = 0.0$ (exact IEEE 754 float identity) | **PASS** |
| **Fail-Safe Fallback** | Grad-CAM failure does not abort inference or raise HTTP 500 | Prediction returned with `explanation_status="unavailable"` | **PASS** |
| **Database Bloat Prevention** | Base64 explanation overlay stripped before SQLite persistence | Only metadata (`method`, `layer`, `status`) stored | **PASS** |
| **Automated E2E Suite** | 12 browser screenshots, doctor & normal user workflows | All 12 screenshots captured, 0 failures | **PASS** |

---

## 2. Restored Feature Breakdown (Before / Pre-Batch-C / After)

### 1. DL Image Upload & Inspection Canvas (Feature #22)
- **Before (`5b6c72c`)**: Generic file input with small static preview thumbnail.
- **Pre-Batch-C State (`8eba137`)**: Tiny upload button with raw text metadata.
- **After (Batch C)**: Professional medical imaging canvas featuring a dark high-contrast backdrop, drag-and-drop zone with visual feedback, instant natural dimension inspection ($224 \times 224$), file size, MIME verification, replace/remove buttons, and memory-safe `URL.revokeObjectURL` cleanup.
- **Regression Check**: Tested with empty (0-byte), corrupt, oversized (>15MB), and valid PNG/JPEG images. Graceful non-alarmist error messages displayed without Python traceback leakage.

### 2. Canonical Demo Research Examples (Feature #23)
- **Before (`5b6c72c`)**: Commited demo buttons loading CBIS-DDSM sample mammograms.
- **Pre-Batch-C State (`8eba137`)**: Completely omitted; users had to provide their own images.
- **After (Batch C)**: Restored two canonical research presets (`demo-benign-mammogram.png` with raw prob $\approx 0.425 < 0.515 \to$ Benign; `demo-malignant-mammogram.png` with raw prob $\approx 0.614 \ge 0.515 \to$ Malignant). Previews immediately on canvas without auto-submitting.
- **Regression Check**: Verified in `test_dl_frontend_contract.js` and `qa_batch_c_e2e.js`.

### 3. Runtime Grad-CAM Attention Map (Feature #24)
- **Before (`5b6c72c`)**: Legacy CNN / ResNet Grad-CAM with fake thresholded lesion bounding boxes.
- **Pre-Batch-C State (`8eba137`)**: Completely disabled; backend returned `None`, frontend omitted XAI controls.
- **After (Batch C)**: Real-time Grad-CAM implemented via TensorFlow `GradientTape` targeting `top_conv` on frozen `EfficientNet-B0`. Generates a smooth, normalized Jet colormap overlay. Multi-view canvas allows switching between Side-by-Side (default), Original Mammogram, and Grad-CAM Attention Overlay.
- **Regression Check**: Verified in `tests/test_final_dl_gradcam.py`. Strict safety language enforces that Grad-CAM indicates coarse model attention and NOT tumor localization, detected lesions, or surgical margins.

### 4. Decision Threshold & Platt Calibration Decoupling (Feature #25)
- **Before (`5b6c72c`)**: Confused probability presentation mixing calibrated risk bands with decision thresholds.
- **Pre-Batch-C State (`8eba137`)**: Single generic card showing calibrated probability as dominant score.
- **After (Batch C)**: Dual metric split isolating Raw Malignant Probability ($\tau \ge 51.5\%$, with distance in percentage points) from Platt Calibrated Probability (display/reliability interpretation only). Explicit note clarifies that calibrated probability is not used to determine the model class.
- **Regression Check**: Verified in `tests/test_final_dl_gradcam.py` and `qa_batch_c_e2e.js`.

### 5. AI Educational Guidance Display (Feature #26)
- **Before (`5b6c72c`)**: AI advice box with provider attribution.
- **Pre-Batch-C State (`8eba137`)**: Dropped from user-facing result.
- **After (Batch C)**: Dedicated AI Educational Guidance card displaying live advice from active provider (`Gemini`, `OpenAI`, or `local_fallback`) with model badge and non-diagnostic research disclaimer.
- **Regression Check**: Verified in `qa_batch_c_e2e.js` screenshot `v4-c-dl-ai-guidance-1440.png`.

### 6. Printable Report & AI Guide Contextual Handoff (Features #27 & #46)
- **Before (`5b6c72c`)**: Basic report link and ungrounded chatbot navigation.
- **Pre-Batch-C State (`8eba137`)**: Action buttons removed from DL result card.
- **After (Batch C)**:
  - "View Analysis Report": Links directly to authenticated server-rendered HTML report (`/pages/reports.html?id=...`).
  - "Ask AI Guide About This Result": Hands off structured context (`analysis_type: 'dl'`, `model: 'EfficientNet-B0'`, `classification`, `raw_probability`, `threshold: 0.515`, `gradcam_status`, `prediction_id`) via `sessionStorage`. Displays "Discussing Mammography Analysis #..." banner with specialized mammography query prompts.
  - "Analyze Another Image": Cleanly resets preview, file, Grad-CAM overlay, and result workspace while revoking object URLs to prevent browser memory leaks.
- **Regression Check**: Verified in `qa_batch_c_e2e.js`.

### 7. Doctor Patient Linkage & Security (Feature #28)
- **Before (`5b6c72c`)**: Single dropdown in legacy monolithic page.
- **Pre-Batch-C State (`8eba137`)**: Read `?patient_id` from URL but provided no UI selector.
- **After (Batch C)**: Doctor patient selector bar displayed exclusively for `role === 'doctor'`. Shows active patient name, "View Patient" link, and interactive patient dropdown. Unauthorized patient IDs rejected server-side with HTTP 403.
- **Regression Check**: Verified in `qa_batch_c_e2e.js` screenshot `v4-c-dl-doctor-patient-1440.png` and `tests/test_patient_prediction_security.py`.

---

## 3. Visual Verification & Screenshot Catalog

All 12 required screenshots captured and inspected:

| Screenshot Identifier | Description | Viewport | Path |
| :--- | :--- | :---: | :--- |
| `v4-c-dl-empty-1440.png` | Initial empty Mammography DL workstation with 3-column layout | $1440 \times 900$ | `docs/v4/screenshots/v4-c-dl-empty-1440.png` |
| `v4-c-dl-empty-390.png` | Initial empty Mammography DL workstation on mobile viewport | $390 \times 844$ | `docs/v4/screenshots/v4-c-dl-empty-390.png` |
| `v4-c-dl-image-loaded-1440.png` | Benign research preset loaded into inspection canvas with metadata bar | $1440 \times 900$ | `docs/v4/screenshots/v4-c-dl-image-loaded-1440.png` |
| `v4-c-dl-processing-1440.png` | Live execution tracker showing progressive staging steps | $1440 \times 900$ | `docs/v4/screenshots/v4-c-dl-processing-1440.png` |
| `v4-c-dl-result-1440.png` | Completed Benign analysis with dominant classification banner & dual metric split | $1440 \times 900$ | `docs/v4/screenshots/v4-c-dl-result-1440.png` |
| `v4-c-dl-gradcam-side-by-side-1440.png` | Side-by-side comparison of input mammogram vs Grad-CAM attention overlay | $1440 \times 900$ | `docs/v4/screenshots/v4-c-dl-gradcam-side-by-side-1440.png` |
| `v4-c-dl-gradcam-overlay-1440.png` | Single-view tab showing isolated Grad-CAM Jet colormap overlay | $1440 \times 900$ | `docs/v4/screenshots/v4-c-dl-gradcam-overlay-1440.png` |
| `v4-c-dl-ai-guidance-1440.png` | Educational guidance, non-diagnostic boundaries, and recommended next steps | $1440 \times 900$ | `docs/v4/screenshots/v4-c-dl-ai-guidance-1440.png` |
| `v4-c-dl-result-390.png` | Responsive mobile result view at 390px with vertically stacked metrics | $390 \times 844$ | `docs/v4/screenshots/v4-c-dl-result-390.png` |
| `v4-c-dl-gradcam-390.png` | Responsive mobile Grad-CAM visualization at 390px | $390 \times 844$ | `docs/v4/screenshots/v4-c-dl-gradcam-390.png` |
| `v4-c-dl-gradcam-unavailable-1440.png` | Graceful fallback banner when Grad-CAM is unavailable while inference passes | $1440 \times 900$ | `docs/v4/screenshots/v4-c-dl-gradcam-unavailable-1440.png` |
| `v4-c-dl-doctor-patient-1440.png` | Doctor workspace mode showing patient selector bar attached to Eleanor Vance | $1440 \times 900$ | `docs/v4/screenshots/v4-c-dl-doctor-patient-1440.png` |

---

## 4. Test Suite Execution Summary

- **Unit & Parity Tests**:
  `pytest tests/test_final_dl_gradcam.py` $\to$ **5 passed in 7.32s**
  - `test_gradcam_target_layer_resolution`: Verified `top_conv` is resolved inside nested `efficientnetb0`.
  - `test_gradcam_positive_class_direction`: Verified scalar represents `malignant_probability`.
  - `test_gradcam_overlay_properties`: Verified heatmap bounds $[0, 1]$, finite values, valid base64 PNG data URL.
  - `test_gradcam_numerical_parity_gate`: Verified identical raw/calibrated probabilities ($\Delta = 0.0$) with/without explanation.
  - `test_gradcam_failure_fallback`: Verified simulated exception does not crash inference and returns `explanation_status="unavailable"`.

- **Frontend Contract Test**:
  `node scripts/test_dl_frontend_contract.js` $\to$ **PASS**
  - Confirmed `predictionService.dl` defaults `includeExplanation: true`.
  - Confirmed `dl-analysis.js` passes `includeExplanation: true` and `patientId`.
  - Confirmed absence of legacy models, fake lesion contours, and forbidden risk terms.

- **End-to-End Browser Suite**:
  `node scripts/qa_batch_c_e2e.js` $\to$ **ALL CHECKS PASS**
  - Normal user analysis on benign preset: Benign ($42.5\%$ raw vs $51.5\%$ cutoff, $-9.0$ pp).
  - Doctor user analysis on malignant preset: Malignant ($61.4\%$ raw vs $51.5\%$ cutoff, $+9.9$ pp) attached to patient ID 23.
  - Database persistence: `prediction_type="dl"` saved with `user_id` and `patient_id` without bloating SQLite.
