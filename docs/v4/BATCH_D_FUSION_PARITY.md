# Phase 4R — Batch D: Experimental Fusion Feature Parity Audit

**Branch**: `feat/product-experience-v4`  
**Date**: September 11, 2026  
**Reference Legacy Commit**: `5b6c72c5ae1d4cb4e16bb9989dd6adfb49a5d99a`  
**Current Product State**: Modular V4 (`cfc5dc4`)  
**Scientific Contract**:
- **Study A**: WDBC FNA 30 nuclear morphology features, StandardScaler → Logistic Regression, frozen decision raw malignant probability $\ge 0.36$.
- **Study B**: CBIS-DDSM Full Processed Image, EfficientNet-B0 ($224 \times 224 \times 3$), frozen decision raw malignant probability $\ge 0.515$, Platt calibration display-only.
- **Experimental Fusion Heuristic**: Unpaired software combination: $0.4 \times \text{ML\_RAW} + 0.6 \times \text{DL\_RAW}$. No paired patient dataset exists. 0.50 is an unvalidated software midpoint.

---

## 1. Feature Parity Audit Table

| Feature | Legacy Behavior (`5b6c72c`) | Current Pre-Batch-D State | Scientific Compatibility | Batch D Action |
| :--- | :--- | :--- | :--- | :--- |
| **Structured Feature Inputs** | No 30 input controls on fusion tab; only supported loading via CSV or OCR into background state `state.fusionClinicalData`. | 30 plain inputs without units, WDBC descriptions, reference ranges, or outlier safeguards. | Requires parity with frozen 30-feature WDBC pipeline. | **REBUILD & ENHANCE**: Reuse Batch B components: 30 visible inputs, WDBC descriptions, reference intervals, live status counters, progress bar, clear/reset. |
| **Presets / Examples** | Legacy fusion tab lacked direct benign/malignant preset buttons for structured data. | Basic preset buttons with mock-feeling values. | Research examples must match verified WDBC samples. | **RESTORE**: Provide verified Benign (Case #8510426) and Malignant (Case #842302) research examples matching Batch B. |
| **CSV Import & Template** | Legacy supported clinical CSV upload into multimodal state with column checking. | Generic or missing CSV flow on fusion page. | Fully compatible with 30 WDBC features. | **RESTORE**: Reuse Batch B CSV drag-and-drop parsing, preview modal, column validation, and downloadable research CSV template. |
| **Report / OCR Extraction** | Extracted 30 values from lab report image using Gemini/OpenAI/local OCR into fusion state. | Endpoint `/predict/extract-clinical/` exists, but UI integration was disconnected on fusion. | Fully compatible. | **RESTORE**: Provide report-image extraction flow allowing OCR prepopulation of the Structured branch with field review. |
| **Mammography Image Upload & Preview** | Basic file input with small thumbnail preview; no dimension or format validation. | Simple dropzone without dimension readout or format safeguards. | Fully compatible with EfficientNet-B0 ($224 \times 224 \times 3$). | **IMPROVE**: Reuse Batch C medical dropzone: drag/drop, JPEG/PNG validation, dimensions, file size, thumbnail, Replace, and Remove. |
| **Mammography Demo Presets** | Legacy loaded demo images from static assets. | Demo buttons disabled or pointing to missing assets. | Fully compatible research assets. | **RESTORE**: Wire Benign and Malignant research demo presets (224x224 RGB PNGs) restored in Batch C without auto-running. |
| **Grad-CAM Attention Map** | Sent `include_explanation=true`, but backend CNN Grad-CAM was incompatible with frozen EfficientNet-B0. | Frontend hardcoded `include_explanation=false`; no Grad-CAM generated in fusion runs. | Grad-CAM on `top_conv` layer restored in Batch C for standalone DL. | **RESTORE & INTEGRATE**: Frontend requests `include_explanation=true`. Return Grad-CAM in DL branch. Graceful fallback if Grad-CAM fails. |
| **Patient Context (Doctor)** | Doctor could select patient in dropdown, but separate inputs could theoretically decouple. | Patient selector missing or decoupled across endpoints. | Clinical requirement: analysis subject must be uniform. | **RESTORE & LOCK**: Shared doctor patient context bar at top; one uniform patient ID applied to both branches. Server validates ownership. |
| **Branch Result Rendering** | Rendered separate ML and DL cards, but mixed raw and calibrated numbers under "Xác suất". | Single combined result card hiding branch details. | Each branch must display frozen model metrics (thresholds 0.36 and 0.515). | **REBUILD**: Render independent Structured ML workstation and Mammography DL workstation alongside combined result. |
| **Probability Space Formulation** | Mixed raw ML probability with Platt-calibrated DL probability in the 40/60 formula. | Mixed raw ML with calibrated DL: $0.4 \times p_{\text{ml,raw}} + 0.6 \times p_{\text{dl,calibrated}}$. | **SCIENTIFIC BUG**: Mixing probability spaces is mathematically and semantically invalid. | **MANDATORY SCIENTIFIC FIX**: Calculate score strictly as $0.4 \times p_{\text{ml,raw}} + 0.6 \times p_{\text{dl,raw}}$. Never use calibrated DL. |
| **Combined Result Semantics** | Displayed "Độ tin cậy của kết luận tổng hợp" and clinical "Nguy cơ tổng hợp". | Displayed "combined_confidence" as pseudo-diagnostic confidence. | **MISLEADING**: 40/60 weighting is an unvalidated software heuristic, not a trained multimodal model. | **CORRECT**: Label as "Experimental Combined Score" (`combined_malignant_score`), 0.50 software decision midpoint disclaimer. |
| **Branch Disagreement Behavior** | Legacy completely ignored branch disagreement; silent weighted compromise. | Added brief text warning in uncertainty array, but combined score still dictated diagnosis. | Dangerous: silent averaging overrules conflicting clinical signals. | **PROMINENT REBUILD**: Prominent "BRANCH DISAGREEMENT" panel before combined score explaining unpaired dataset nature. |
| **Branch Agreement Behavior** | Legacy treated agreement as validated clinical confidence. | Treated agreement as generic success. | Unpaired datasets mean agreement does not validate combination. | **REBUILD**: Show "BRANCH AGREEMENT" banner while clearly noting it does not constitute clinical validation. |
| **Unpaired Dataset Communication** | Completely absent in legacy UI. | Vague note buried in footer. | Essential scientific truth: WDBC and CBIS-DDSM have zero paired patients. | **MANDATORY NOTICE**: Prominent callout before execution and in results explaining software-only combination. |
| **AI Educational Guidance** | Generic advice block attempting to synthesize both branches as a unified patient case. | AI advice omitted or hidden in fusion UI. | AI must not resolve disagreement or declare clinical certainty. | **RESTORE & CONSTRAIN**: Re-render AI Educational Guidance with strict guardrails acknowledging unpaired data. |
| **Printable Analysis Report** | Legacy button downloaded raw JSON or incomplete summary. | Report link missing from fusion UI. | Full auditability required for research. | **RESTORE & UPGRADE**: Dedicated "View Analysis Report" with branch breakdowns, formula math, disagreement status, and disclaimers. |
| **History Persistence** | Persisted raw payload to SQLite without stripping large base64 Grad-CAM images. | Inactive or risked SQLite bloat if Grad-CAM enabled. | Risk of megabyte-scale SQLite growth per run. | **RESTORE WITH HYGIENE**: Strip `dl_result.explanation_image` before `db.save_prediction` to store only metadata. |
| **Reset / Clear Workflow** | Cleared state but left inconsistent UI fragments. | Incomplete reset. | Usability requirement. | **RESTORE**: Clean "Reset Fusion" clearing 30 fields, CSV, OCR, image, preview, Grad-CAM, results, while preserving session. |
| **AI Guide Handoff** | Generic button without structured context. | Absent in fusion. | Crucial educational tool. | **RESTORE**: "Ask AI Guide About This Fusion Result" passing structured fusion context via `sessionStorage` without PII. |

---

## 2. Key Scientific Bug Analysis: Probability-Space Inconsistency

### Legacy and Pre-Batch-D Implementation:
```python
p_ml = float(ml_res['probability'])     # Raw malignant probability from Logistic Regression
p_dl = float(dl_res['probability'])     # Platt-calibrated probability from EfficientNet-B0
combined_p = (p_ml * 0.4) + (p_dl * 0.6)
```

### Scientific Correction:
The Platt-calibrated probability in Study B is an empirical display mapping fitted specifically to calibrate reliability diagrams for human interpretation. It is not an uncalibrated latent output, nor is it commensurate with the raw logistic probability of Study A.

Mixing raw ML with calibrated DL distorts the intended $40/60$ ratio because Platt sigmoid scaling alters the distribution non-linearly. To maintain scientific consistency:
```python
p_ml_raw = float(ml_res['raw_probability'])
p_dl_raw = float(dl_res['raw_probability'])
combined_malignant_score = round((p_ml_raw * 0.4) + (p_dl_raw * 0.6), 6)
```

### Invariant Rules:
1. `combined_malignant_score` is computed strictly from raw model probabilities.
2. Changes to Platt calibration parameters or `dl_res['calibrated_probability']` must have zero effect on `combined_malignant_score`.
3. The threshold of 0.50 is labeled as the "Software Decision Midpoint", not a clinical diagnostic threshold.
