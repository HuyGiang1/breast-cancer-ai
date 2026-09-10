# Batch B — Structured ML Feature Parity Audit & Action Mapping

**Reference Baseline**: Legacy commit `5b6c72c5ae1d4cb4e16bb9989dd6adfb49a5d99a` (`frontend/app.js`)  
**Current Product State**: Modular V4 frontend (`frontend/pages/ml-analysis.html`, `frontend/js/pages/ml-analysis.js`)  
**Scientific Source of Truth**: Study A — WDBC (569 samples, 30 FNA nuclear morphology features), frozen `StandardScaler -> LogisticRegression`, decision cutoff $\ge 0.36$ raw malignant probability.

---

## 1. Feature Parity Audit Matrix

### Feature 1: `SAMPLES.benign` & `SAMPLES.malignant`
- **Legacy Feature (`5b6c72c:frontend/app.js:46-77`)**:
  - `SAMPLES.benign`: canonical 30-feature vector matching WDBC index 19 (benign cytology: `mean_radius: 13.54`, `mean_texture: 14.36`, `worst_radius: 15.11`, etc.).
  - `SAMPLES.malignant`: canonical 30-feature vector matching WDBC index 0 (malignant cytology: `mean_radius: 17.99`, `mean_texture: 10.38`, `worst_radius: 25.38`, etc.).
  - Bound to `#sampleBenignBtn` and `#sampleMalignantBtn`. Filled inputs, called `updateMlFeatureProgress()`, set prediction status toast, did NOT auto-run prediction.
- **Current State (`03393bc:frontend/js/pages/ml-analysis.js`)**:
  - Completely absent. The minified V3 page removed all sample buttons and sample constants.
- **Action**:
  - Restore canonical research samples with explicit provenance (WDBC development cohort row 19 for benign, row 0 for malignant).
  - Add Quick Entry toolbar buttons: `[ Load benign research example ]`, `[ Load malignant research example ]`.
  - On click: populate all 30 inputs, validate against development reference, update progress to 30/30, clear errors, and DO NOT auto-submit.

---

### Feature 2: `parseClinicalCsvText`
- **Legacy Feature (`5b6c72c:frontend/app.js:1483-1497`)**:
  - Handled line splitting (`\r?\n`), parsed line 0 as headers and line 1 as values.
  - Looked up each feature from `FEATURES` array by exact header name match. Ignored non-model columns like `id` and `diagnosis`.
  - Converted values using `Number()`, ignoring NaNs. Threw if `< 2` lines. Only read row 1 (single row only, no preview, no multi-row selection).
- **Current State (`03393bc:frontend/js/pages/ml-analysis.js`)**:
  - Completely absent.
- **Action**:
  - Restore and substantially improve CSV parsing:
    - Support both snake_case API headers (`mean_radius`) and original WDBC space headers (`mean radius`).
    - Safely ignore metadata columns: `id`, `diagnosis`, `target`, `label`, `Unnamed: 32`.
    - Single data row: preview values and prompt user to confirm `Load Values`.
    - Multiple data rows: display a clean preview table with row index, completion/validation status, allowing user to choose exactly ONE row.
    - Provide robust error handling for empty file, missing required features, duplicate headers, NaNs, infinities, non-numeric cells, and malformed encoding.

---

### Feature 3: `extractClinicalFromImage`
- **Legacy Feature (`5b6c72c:frontend/app.js:1951-1985`)**:
  - Sent image file to `POST /api/v1/predict/extract-clinical/` using `FormData`.
  - Backend performed OCR/Vision extraction. Response returned `{ values: {...}, provider: "local_ocr"|"gemini"|"openai" }`.
  - Filled inputs and displayed status/toast: `"Đã điền X/30 chỉ số từ ảnh bằng {provider}"`.
- **Current State (`03393bc:frontend/js/pages/ml-analysis.js`)**:
  - Completely absent in V3/V4 modular frontend, even though `POST /api/v1/predict/extract-clinical/` backend endpoint is fully operational.
- **Action**:
  - Restore frontend control: `[ Extract from Report Image ]` in the Quick Entry toolbar.
  - Implement full review modal: upload report/image -> show extraction progress -> display all 30 features with extracted vs missing status, show provider/model -> allow user editing before loading -> click `Load Extracted Values`.
  - Never auto-predict directly from image upload.

---

### Feature 4: `updateMlFeatureProgress`
- **Legacy Feature (`5b6c72c:frontend/app.js:1519-1525`)**:
  - Listened on form `input` events, counted how many of the 30 fields had non-empty values, updated text `"X/30 chỉ số"`.
- **Current State (`03393bc:frontend/js/pages/ml-analysis.js`)**:
  - Minimal `<progress>` bar and text `n / 30 complete`. Lacks group-level breakdown, lacks data quality indicators, and inputs are ambiguous empty white boxes.
- **Action**:
  - Retain live completion counter (`X / 30 fields complete`) in the toolbar and sticky side panel.
  - Add per-group progress (Mean 0/10, SE 0/10, Worst 0/10).
  - Add live WDBC development reference indicators (P5–P95 common, P1–P99 unusual, outside min/max extreme).

---

### Feature 5: `renderTopFeatures`
- **Legacy Feature (`5b6c72c:frontend/app.js:1554-1569`)**:
  - Rendered `result.top_features` (first 6 items) as a simple list of cards showing `formatFeatureLabel(feat.feature)` and `feat.description`.
  - Relying on backend SHAP or fallback coefficients.
- **Current State (`03393bc:frontend/js/pages/ml-analysis.js`)**:
  - Completely absent. Only renders a basic `resultCard` with diagnosis and raw probability.
- **Action**:
  - Implement deterministic frozen Logistic Regression feature contribution decomposition ($z_i = w_i \cdot \frac{x_i - \mu_i}{\sigma_i}$).
  - Render "Why Did the Model Respond This Way?" with horizontal diverging contribution bars centered at 0:
    - Features pushing toward Malignant ($z_i > 0$) in red/amber.
    - Features pushing toward Benign ($z_i < 0$) in blue/teal.
  - Include raw value, standardized value, log-odds contribution, and reference state.
  - Provide full expandable 30-feature table with sorting (highest malignant contribution, highest benign contribution, most unusual input, standard order).

---

### Feature 6: `renderReliabilityBox`
- **Legacy Feature (`5b6c72c:frontend/app.js:1601-1621`)**:
  - Displayed `reliability_label` (High, Medium, Low) and uncertainty reasons/warnings if present.
- **Current State (`03393bc:frontend/js/pages/ml-analysis.js`)**:
  - Absent on the ML page.
- **Action**:
  - Integrate Input Quality and Reliability section:
    - Report number of values within common development range (P5–P95), unusual (outside P5–P95), and extreme (outside min/max).
    - Distinguish dataset unusualness from model contribution (unusual values don't necessarily drive prediction, and vice versa).

---

### Feature 7: `renderAdviceBlock`
- **Legacy Feature (`5b6c72c:frontend/app.js:1623-1628, 1762-1766`)**:
  - Rendered backend-provided AI educational advice (`result.advice`, `advice_provider`, `advice_model`) in an advice block.
- **Current State (`03393bc:frontend/js/pages/ml-analysis.js`)**:
  - Completely absent. The backend continues to generate `advice` via `get_clinical_advice()`, but the V3/V4 frontend dropped it entirely.
- **Action**:
  - Restore "AI Educational Guidance" section in result view:
    - Display AI advice text, provider, and model.
    - Enforce safety boundaries: advice clearly states research/educational nature, never says "you have cancer" or prescribes drugs/treatments.
    - Fallback gracefully if advisor provider is offline without interrupting deterministic ML predictions.
  - Add separate "General Wellbeing Guidance" section (lifestyle, balanced nutrition, clinical follow-up) clearly detached from specific FNA morphology values.

---

### Feature 8: `downloadPredictionReport`
- **Legacy Feature (`5b6c72c:frontend/app.js:1104-1138`)**:
  - Fetched `GET /api/v1/predictions/{id}/report/` to obtain a printable HTML report and triggered browser download.
- **Current State (`03393bc:frontend/js/pages/ml-analysis.js`)**:
  - Completely absent in ML analysis page.
- **Action**:
  - If a prediction is persisted (logged-in user or doctor-patient context), display `[ View Analysis Report ]`.
  - Opens/prints the persisted report cleanly from `GET /api/v1/predictions/{id}/report/`.
  - Hidden or disabled when running anonymous unpersisted predictions.

---

### Feature 9: Patient Selector / Patient Linkage
- **Legacy Feature (`5b6c72c:frontend/app.js:1009-1025, 2085-2090`)**:
  - `#predictionPatientSelect` dropdown populated with doctor's patients if `currentUser.role === 'doctor'`.
  - Normal users saw "Guest mode" or no selector.
  - Passed `patient_id` to prediction API.
- **Current State (`03393bc:frontend/js/pages/ml-analysis.js`)**:
  - URL parameter `?patient_id=123` is read passively, but no selector exists. If doctor lands on the page without query param, they cannot select a patient. Normal users see no patient context.
- **Action**:
  - If user has role `doctor`:
    - Display Doctor Patient Selector with options: `No patient / research-only` + list of assigned patients (`state.patients`).
    - If `?patient_id=...` is present and owned by doctor, pre-select that patient and display banner: `"Analyzing for <Patient Name>"` with link `[ View Patient ]`.
  - Normal users:
    - Completely hide the doctor selector.
    - Reject any unauthorized `patient_id` parameter.

---

### Feature 10: AI Advisor Contextual Handoff
- **Legacy Feature (`5b6c72c:frontend/app.js:2196-2200`)**:
  - Chat suggestions navigated to assistant page with prefilled query, but structured ML results had no deep contextual handoff.
- **Current State (`03393bc:frontend/js/pages/ml-analysis.js`)**:
  - None.
- **Action**:
  - Add `[ Ask AI Guide About This Result ]` button in result workspace.
  - Stores structured context in `sessionStorage` (`bcai_advisor_context`):
    - `prediction_id` (if persisted)
    - `model_name`: Logistic Regression (WDBC)
    - `classification`: Benign / Malignant
    - `raw_probability`, `threshold`: 0.36
    - `top_contributors`: top 3 malignant and top 3 benign features
    - `input_quality_summary`: count within reference vs unusual
  - Navigates to `pages/advisor.html`.
  - Advisor detects context, displays `"Discussing Structured Analysis #..."`, and offers contextual starter prompts without putting sensitive clinical data in URL queries.

---

### Feature 11: Clear All
- **Legacy Feature (`5b6c72c:frontend/app.js`)**:
  - Reset form inputs on demand.
- **Current State (`03393bc:frontend/js/pages/ml-analysis.js`)**:
  - Absent.
- **Action**:
  - Add `[ Clear All ]` to the Quick Entry toolbar.
  - Resets all 30 fields, progress counter, CSV state, OCR state, typo warnings, and result container.
  - Prompts confirmation only if active inputs or results would be lost.
