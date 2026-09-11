# Legacy Feature Parity Matrix & V4 Restoration Plan

**Document Version**: 1.0.0  
**Date**: 2026-09-08  
**Branch**: `feat/product-experience-v4`  
**Committed V3 Baseline**: `8eba137b5a8113ba4dcf86d2c86c82d466747974` (Phase 3B.2)  
**Functional Baseline Commit**: `5b6c72c5ae1d4cb4e16bb9989dd6adfb49a5d99a` (`frontend/app.js` monolith + `frontend/index.html`)  
**Scientific Source of Truth**: Frozen ML/DL Runtimes & Checksummed Artifacts (`models/final/`)  

---

## Non-Regression Rule

> [!IMPORTANT]
> **MANDATORY NON-REGRESSION RULE**:  
> No feature classified as **PRESERVED** or **RESTORED** may disappear in a later visual redesign without explicit user approval. Visual reskinning must strictly enhance or maintain functionality, never remove it.

---

## 1. Baseline Principles

1. **Old Working Frontend (`5b6c72c`)**: Functional behavior source of truth. Every user workflow that existed prior to modularization is cataloged and protected.
2. **Committed V3 (`8eba137`)**: Visual design system, modular ES module architecture, topbar mega-menu navigation, and security/session guards baseline.
3. **Current Frozen Backend & Model Artifacts**: Scientific and operational source of truth. WDBC Logistic Regression ($\tau=0.36$ raw) and CBIS-DDSM EfficientNet-B0 ($\tau=0.515$ raw with Platt display calibration) are inviolable.

---

## 2. Layer-Aware Feature Parity Matrix

### Status Legend
- **`PRESERVED`**: Fully functioning in both frontend UI/logic and backend API.
- **`PRESERVED — UX DEGRADED`**: Fully functioning end-to-end, but presentation, labeling, or visual hierarchy was weakened during redesign.
- **`PARTIALLY PRESERVED`**: Core mechanics exist, but key sub-features, filters, or links were omitted.
- **`FRONTEND REGRESSION — BACKEND PRESERVED`**: Backend endpoint and service remain operational, but frontend UI controls or calls were removed.
- **`FULLY LOST`**: Both UI presentation and client-side workflow logic were removed during redesign.
- **`SCIENTIFICALLY INCOMPATIBLE — REIMPLEMENT AGAINST FINAL MODEL`**: Legacy feature used deprecated/unpromoted models (e.g. legacy CNN or RF SHAP); must be reimplemented using frozen models.
- **`NEW ENHANCEMENT`**: New value-add capability requested or created to improve workflow safety.
- **`INTENTIONALLY DEFERRED`**: Operational items deferred until live staging (e.g. Google OAuth handshake, live SMTP).

---

### Matrix Table

| # | Feature | Legacy UI / Behavior (`5b6c72c`) | Current V3 Frontend UI (`8eba137`) | Current V3 Frontend Logic | Current Backend / API Support | Current Final-Model Compatibility | Status | V4 Action | Evidence / Verification |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1** | **Hero & Public Entry** | Hero banner with quick triage CTA and workflow entry cards | Premium dark hero with headline, status chips, and CTA | `index.html` inline navigation logic | N/A (Static) | Fully compatible | **PRESERVED** | Maintain current premium layout | `frontend/index.html:L42-L78` |
| **2** | **Clinical Warning Signs Gallery** | 6 descriptive warning signs with images and advice | Restored 6 rich medical warning sign cards with non-alarmist phrasing and guidance | Interactive smooth scroll to `#learn-warnings` | N/A (Static) | Fully compatible | **RESTORED** | Restored in Batch A with verified clinical copy & evaluation advice | `frontend/index.html:L1060-L1140` |
| **3** | **Screening Guidelines by Age** | Age-stratified mammography screening guideline tables | Restored structured age-stratified screening table with official ACS & USPSTF citations | Interactive navigation to `#learn-screening` | N/A (Static) | Fully compatible | **RESTORED** | Restored in Batch A with authoritative source links | `frontend/index.html:L980-L1050` |
| **4** | **Nutrition & Lifestyle Modalities** | Care guide cards for plant foods, animal foods, hydration, exercise | 4 glassmorphic cards in landing | Fully rendered in V3 | N/A (Static) | Fully compatible | **PRESERVED** | Preserved in Phase 3A.2/3A.5 | `frontend/index.html:L240-L310` |
| **5** | **Interactive FAQ Accordion** | Searchable/expandable FAQ accordion (`bindFaqToggle`) | Expandable FAQ section in landing | Native `<details>` or JS toggle | N/A (Static) | Fully compatible | **PRESERVED** | Maintain and verify keyboard accessibility | `frontend/index.html:L350-L410` |
| **6** | **Educational Video Library** | Video preview cards with modal / embedded player | 2 video preview cards in landing | Media card elements | N/A (Static) | Fully compatible | **PRESERVED** | Maintain verified poster assets | `frontend/index.html:L320-L348` |
| **7** | **Research Evidence & Decoupling** | Academic decoupling narrative between Study A and B | Research telemetry and model selection sections | Dynamic telemetry script | `GET /api/v1/models/final/status/` | Fully compatible | **PRESERVED** | Maintained across Landing and Research Center | `frontend/pages/research.html` |
| **8** | **Toast Notifications** | Lightweight floating toast notifications (`showToast`) | Ad-hoc alert paragraphs | Local status text elements | N/A | Fully compatible | **PRESERVED — UX DEGRADED** | Implement centralized non-blocking toast service | `5b6c72c:frontend/app.js:L530-L550` |
| **9** | **Mobile Navigation Drawer** | Slide-out hamburger drawer with nav links | Header hamburger drawer with ARIA controls | Interactive JS in `index.html` & `shell.js` | N/A | Fully compatible | **PRESERVED** | Verified at 390px viewport | `frontend/js/components/shell.js` |
| **10** | **ML Sample Presets (Benign / Malignant)** | One-click loading of canonical Benign and Malignant vectors | One-click toolbar buttons with canonical research examples | Interactive JS populating all 30 inputs without auto-prediction | Supported (standard payload) | 100% compatible with frozen LR | **RESTORED (Batch B)** | Restored canonical presets (Row 19 Benign, Row 0 Malignant) with full live validation | `frontend/js/pages/ml-analysis.js` |
| **11** | **ML Clear Inputs Action** | Resets all 30 fields to blank | Clear All toolbar button | Resets 30 fields, validation indicators, CSV/OCR modals, results | Supported | Fully compatible | **RESTORED (Batch B)** | Restored with confirmation prompt when user input or results exist | `frontend/js/pages/ml-analysis.js` |
| **12** | **ML Input Progress Counter** | Live tracking: `X / 30 đặc trưng` | Progress indicator: `30 / 30 complete` | Event listener updates count | Supported | Fully compatible | **PRESERVED** | Retain live counter in toolbar | `frontend/js/pages/ml-analysis.js` |
| **13** | **ML CSV Import & Template** | File input parsing 30 feature columns from CSV (`parseClinicalCsvText`) | Robust multi-format CSV importer + single/multi-row preview modal + CSV templates | Header normalization, multi-row row selector table, error handling, CSV template download | Supported | Fully compatible | **RESTORED & ENHANCED (Batch B)** | Restored with WDBC alias normalization, multi-row preview selector, and clean 30-feature template download | `frontend/js/utils/clinical-csv.js`, `frontend/js/pages/ml-analysis.js` |
| **14** | **ML Report-Image / OCR Feature Extraction** | Upload lab report photo to extract features (`extractClinicalFromImage`) | Report image upload + review modal + editable preview | Review extracted vs missing fields, provider/model attribution, user inspection before loading | `POST /api/v1/predict/extract-clinical/` active | Calls AI Advisor OCR vision backend | **RESTORED (Batch B)** | Restored upload trigger and review-before-load inspection modal | `frontend/js/pages/ml-analysis.js`, `backend/app/api/endpoints.py` |
| **15** | **ML Feature Reference & Outliers** | Hardcoded approximate ranges without clear provenance | Exact WDBC development reference (N=455, test excluded) | 4 distinct live visual tiers (Common P5–P95, Unusual <P5/>P95, Extreme <P1/>P99, Outside observed) + outlier review safeguard | Reference stats generated deterministically | Verified against 455 WDBC dev samples only | **RESTORED & ENHANCED (Batch B)** | Reproducible development reference artifact + live validation + confirmation modal for values outside observed min/max | `frontend/content/wdbc_feature_reference.json`, `scripts/build_wdbc_feature_reference.py` |
| **16** | **ML Linear Model Feature Contributions** | Displayed top SHAP features from legacy RF | Deterministic log-odds contributions ($z_i = w_i \cdot \frac{x_i - \mu_i}{\sigma_i}$) from frozen LR | Centered horizontal contribution bars (Top Benign vs Top Malignant) + expandable 30-feature breakdown table | Server computes and returns exact linear contributions | Exact mathematical parity with frozen LR ($\Delta < 10^{-12}$) | **RESTORED & ENHANCED (Batch B)** | Fully faithful to frozen StandardScaler $\to$ LogisticRegression pipeline without retraining | `backend/app/services/final_ml_runtime.py`, `frontend/js/pages/ml-analysis.js` |
| **17** | **ML Reliability & Decision Threshold** | Displayed threshold and risk band | Displays raw cutoff 0.36 and raw probability | Rendered in result card | Supported | Aligned to frozen threshold 0.36 | **PRESERVED** | Maintain prominent threshold and probability display | `frontend/js/pages/ml-analysis.js` |
| **18** | **ML AI Clinical Advice Display** | Dedicated advice card with provider/model badge | Educational guidance section with advice text and provider/model badges | Rendered in result workspace; graceful fallback if offline | Backend attaches `advice`, `advice_provider`, `advice_model` | Fully compatible | **RESTORED (Batch B)** | Restored educational guidance display with provider badge and safety disclaimers | `frontend/js/pages/ml-analysis.js` |
| **19** | **ML Result Action: Printable Report** | Button to download/open printable HTML report | "View Analysis Report" action button | Launches authenticated persisted report in new tab | `GET /api/v1/predictions/{id}/report/` active | Fully compatible | **RESTORED (Batch B)** | Restored direct link to persisted HTML prediction report | `frontend/js/pages/ml-analysis.js` |
| **20** | **ML Result Action: Contextual AI Handoff** | Button linking prediction outcome to AI Assistant | "Ask AI Guide About This Result" action button | Transfers structured prediction context via `sessionStorage` to `advisor.html` with contextual banner | Supported | Fully compatible | **RESTORED (Batch B)** | Pre-seeds AI advisor conversation with structured analysis ID, outcome, and key contributors without URL leakage | `frontend/js/pages/ml-analysis.js`, `frontend/js/pages/advisor.js` |
| **21** | **ML Patient Linkage Selector** | Doctor selects active patient before prediction | Doctor-only patient selection bar with active patient status | Dropdown selector populates `patient_id`; non-doctors cannot associate patients | Supported by backend | Enforced by server authorization | **RESTORED (Batch B)** | Restored patient selector for authenticated doctors with URL query param support and strict RBAC | `frontend/js/pages/ml-analysis.js` |
| **22** | **DL Image Upload & Preview** | File upload with instant thumbnail and metadata | Professional 3-column workstation with large dropzone & immediate medical canvas preview | Interactive JS measuring naturalWidth/Height, file size, type | `POST /api/v1/predict/image/` active | Fully compatible | **RESTORED & ENHANCED (Batch C)** | Rebuilt into medical imaging inspection canvas with metadata bar, format validation, and memory-safe URL cleanup | `frontend/js/pages/dl-analysis.js` |
| **23** | **DL Demo Sample Mammograms** | Demo buttons loading benign and malignant mammograms | One-click toolbar buttons loading canonical research examples | Fetches committed demo assets into `File` without auto-submitting | Supported (standard image payload) | 100% compatible with frozen EfficientNet-B0 | **RESTORED (Batch C)** | Restored canonical benign (0.425 raw) and malignant (0.614 raw) research assets with immediate preview | `frontend/assets/demo-images/`, `frontend/js/pages/dl-analysis.js` |
| **24** | **DL Grad-CAM Attention Heatmap** | Heatmap overlay on legacy CNN (`include_explanation=true`) | Interactive Visual Comparison canvas (Side-by-side, Original, Grad-CAM overlay) | Requests `include_explanation: true`, renders overlay data URL | TensorFlow GradientTape on `top_conv` layer of frozen EfficientNet-B0 | Zero-dependency JET colormap; strict raw score gradient | **RESTORED & ENHANCED (Batch C)** | Implemented runtime Grad-CAM targeting `top_conv` on frozen EfficientNet-B0 with zero-dependency JET colormap and fail-safe fallback | `backend/app/services/final_dl_gradcam.py`, `backend/app/services/final_dl_runtime.py`, `frontend/js/pages/dl-analysis.js` |
| **25** | **DL Decision Threshold & Calibration** | Mixed calibration and threshold narrative | Prominent raw cutoff 0.515 driving class + separate Platt calibration card | Clearly decouples raw classification cutoff from Platt display reliability | Supported | Strictly decoupled per scientific contract | **PRESERVED & ENHANCED (Batch C)** | Raw cutoff $\ge 0.515$ strictly drives classification; Platt calibrated probability clearly isolated for display only | `frontend/js/pages/dl-analysis.js` |
| **26** | **DL AI Clinical Advice Display** | Advice block with provider/model badge | Dedicated AI Educational Guidance card with provider/model badges | Rendered in result workspace; non-blocking fallback | Backend attaches `advice`, `advice_provider`, `advice_model` | Fully compatible | **RESTORED (Batch C)** | Restored educational guidance card with provider badge, advice text, and medical review disclaimers | `frontend/js/pages/dl-analysis.js` |
| **27** | **DL Result Actions (Report & AI)** | Report download and AI handoff buttons | "View Analysis Report" & "Ask AI Guide About This Result" & "Analyze Another Image" | Launches persisted report tab, handles contextual session handoff, and revokes object URLs | Supported | Fully compatible | **RESTORED (Batch C)** | Restored report link, AI guide contextual handoff, and safe state reset action | `frontend/js/pages/dl-analysis.js` |
| **28** | **DL Patient Linkage Selector** | Doctor selects active patient | Doctor-only patient selection bar with active patient status | Dropdown selector populates `patient_id`; supports `?patient_id` query param | Supported by backend | Enforced by server authorization | **RESTORED (Batch C)** | Restored patient selector for authenticated doctors with URL query param support and strict RBAC | `frontend/js/pages/dl-analysis.js` |
| **29** | **Multimodal Combined Inputs** | 30 ML features + mammogram image | 30 ML inputs + image input | Form data assembled | `POST /api/v1/predict/multimodal/` active | Heuristic combination | **PRESERVED** | Retain dual-input layout | `frontend/pages/multimodal.html` |
| **30** | **Multimodal Demo Presets** | One-click loader for combined demo case | None | Omitted | Demo data available | Compatible | **FULLY LOST** | Add "Load Multimodal Demo Case" button | `5b6c72c:frontend/app.js:L316-L340` |
| **31** | **Multimodal Two-Branch Result Cards** | Separate ML branch card (features) & DL card (heatmap) | Single basic combined card | Omitted branch breakdown | Backend returns `ml_result` and `dl_result` | Compatible | **FRONTEND REGRESSION — BACKEND PRESERVED** | Restore side-by-side branch cards showing ML features & DL heatmap | `5b6c72c:frontend/app.js:L1600-L1650` |
| **32** | **Multimodal Weighted Synthesis** | 40% ML / 60% DL synthesis narrative | Text mention of weights | Rendered in card | Supported | Heuristic software demo only | **PRESERVED** | Maintain clear educational heuristic disclaimer | `frontend/js/pages/multimodal.js` |
| **33** | **Multimodal Result Actions & AI** | AI advice block, report button, AI handoff | None | Omitted | Backend returns advice | Compatible | **FRONTEND REGRESSION — BACKEND PRESERVED** | Add advice block and action buttons to Fusion result | `backend/app/api/endpoints.py:L1340-L1350` |
| **34** | **Patient Search** | Filter patient list by patient name or notes | Live search input `#search` | Filters `patients` array by `full_name` | `GET /api/v1/patients/` active | Fully compatible | **PRESERVED — UX DEGRADED** | Improve visual styling, empty state, and debounced search | `frontend/js/pages/patients.js:L1` |
| **35** | **Patient Create** | Form for full name, DOB, gender, clinical notes | Modal/inline form `#patientForm` | Submits `POST /api/v1/patients/` | `POST /api/v1/patients/` active | Fully compatible | **PRESERVED — UX DEGRADED** | Polish form layout with glassmorphic modal styling | `frontend/js/pages/patients.js:L1` |
| **36** | **Patient Edit** | In-place edit form (`beginPatientEdit`) | Edit button on row opens pre-filled form | Submits `PUT /api/v1/patients/{id}` | `PUT /api/v1/patients/{id}` active | Fully compatible | **PRESERVED — UX DEGRADED** | Polish edit experience with clear cancel action | `frontend/js/pages/patients.js:L1` |
| **37** | **Patient Delete** | Delete button with confirmation modal | Delete button with `confirm()` dialog | Calls `DELETE /api/v1/patients/{id}` | `DELETE /api/v1/patients/{id}` active | Fully compatible | **PRESERVED — UX DEGRADED** | Replace browser native confirm with accessible studio dialog | `frontend/js/pages/patients.js:L1` |
| **38** | **Patient-Linked Analysis Handoff** | Quick buttons launching prediction for selected patient | Links to ML, DL, History on `patient-detail.html` | Passes `?patient_id=<id>` | Supported by backend | Fully compatible | **PARTIALLY PRESERVED** | Add quick "Analyze (ML)" / "Analyze (DL)" action buttons directly on patient list rows | `frontend/js/pages/patient-detail.js:L1` |
| **39** | **Patient Timeline & History Drill-down** | Detailed timeline of predictions for single patient | Timeline rendered on `patient-detail.html` | Calls `patientService.history(id)` | `GET /api/v1/patients/{id}/predictions/` active | Fully compatible | **PRESERVED** | Enhance timeline cards with modality badges and metrics | `frontend/js/pages/patient-detail.js:L1` |
| **40** | **Prediction History: Modality & Label Filters** | Filter history by type (ML/DL/Fusion) & diagnosis | Filter controls for Analysis Type & Label | Filters client array | Supported | Fully compatible | **PRESERVED** | Verified working in `history.js` | `frontend/js/pages/history.js:L1` |
| **41** | **Prediction History: Doctor Patient-Name Filter** | Patient selector dropdown `#historyPatientSelect` | Supports `?patient_id` query param | No in-page patient dropdown | Supported | Fully compatible | **PARTIALLY PRESERVED** | Add patient selector dropdown in history toolbar for doctors | `5b6c72c:frontend/app.js:L625-L640` |
| **42** | **Prediction History: Rich Summary Cards** | Detailed cards with top features, thumbnails, patient name | Text row with link and basic meta | Formatted text row | Persisted in `predictions` table | Fully compatible | **PRESERVED — UX DEGRADED** | Enhance history items with modality badges, patient names, and metric tags | `frontend/js/components/workspace.js` |
| **43** | **Reports: Prediction Report Listing** | Listing of past predictions with direct report view | Table rendered from `reportService.history()` | Fetches persisted history | `GET /api/v1/predictions/` active | Fully compatible | **PRESERVED — UX DEGRADED** | Improve visual hierarchy, replace "HTML research reports" title with "Prediction Reports" | `frontend/js/pages/reports.js:L1` |
| **44** | **Reports: Printable Live HTML Report** | Printable view with charts and institutional headers | Printable view with `Breast Health Studio` branding | Generated server-side | `GET /api/v1/predictions/{id}/report/` active | Fully compatible | **PRESERVED** | Verified in Phase 3B QA | `backend/app/api/endpoints.py:L1365-L1395` |
| **45** | **AI Advisor: Interactive Research Chat** | Conversational chat with suggested prompts | Chat interface with 8 prompt chips | Calls `aiService.advisor()` | `POST /api/v1/advisor/` active | Fully compatible | **PRESERVED** | Verified in Phase 3B QA | `frontend/js/pages/advisor.js` |
| **46** | **AI Advisor: Contextual Result Seeding** | Prediction result passed directly into chat context | Active context banner and customized prompt suggestions | Transfers structured analysis or mammography context via `sessionStorage` without URL exposure | Supported | Fully compatible | **RESTORED (Batch B & C)** | Pre-seeds AI advisor conversation with structured analysis or mammography analysis context and tailored questions | `frontend/js/pages/ml-analysis.js`, `frontend/js/pages/dl-analysis.js`, `frontend/js/pages/advisor.js` |
| **47** | **AI Advisor: Persistent Floating Trigger (FAB)** | Floating `#chatFab` button across all pages | None | Omitted | N/A | Fully compatible | **FULLY LOST** | Add non-intrusive floating Assistant launcher in authenticated shell | `5b6c72c:frontend/index.html:L950-L955` |
| **48** | **Profile: Identity & Password Management** | Edit full name, view role, change password | Edit full name, view role, change password | Calls `authService.updateProfile` & `changePassword` | `PUT /auth/profile/`, `POST /auth/change-password/` | Fully compatible | **PRESERVED** | Verified in Phase 3A.7 QA | `frontend/js/pages/profile.js` |
| **49** | **Profile: Single-Session Sign Out** | Terminate current session token | Button "Sign out" | Calls `authService.logout()` | `POST /api/v1/auth/logout/` active | Fully compatible | **PRESERVED** | Verified in Phase 3A.7/3B QA | `frontend/js/pages/profile.js:L87` |
| **50** | **Profile: Logout All Devices** | "Đăng xuất mọi thiết bị" button | None | Omitted | `POST /api/v1/auth/logout-all/` active | Fully compatible | **FRONTEND REGRESSION — BACKEND PRESERVED** | Add `logoutAll` method to `authService` and button in `profile.js` | `backend/app/api/endpoints.py:L851-L855` |
| **51** | **Google OAuth Real Integration** | Demo modal notification | Demo modal notification | Handshake deferred | Backend config endpoint ready | Intentional deferral | **INTENTIONALLY DEFERRED** | Defer until live staging phase | `frontend/js/pages/profile.js:L140-L160` |
| **52** | **Production SMTP Email Delivery** | Outbox link in development | Outbox link in development | Outbound delivery deferred | Development reset link generator | Intentional deferral | **INTENTIONALLY DEFERRED** | Defer until live staging phase | `backend/app/api/endpoints.py:L940-L960` |

---

## 3. Reconciliation of Feature Counts

| Category | Count | Detailed Breakdown |
| :--- | :---: | :--- |
| **Total Meaningful Features Audited** | **52** | Exhaustive census across `frontend/index.html`, `frontend/app.js`, and V3 pages |
| **RESTORED (Batch A)** | **2** | Features #2 (Warning Signs Gallery), #3 (Age Screening Guidelines) |
| **RESTORED & ENHANCED (Batch B)** | **10** | Features #10 (ML Samples), #11 (ML Clear), #13 (ML CSV & Template), #14 (ML OCR Review), #15 (WDBC References), #16 (LR Exact Contributions), #18 (ML AI Advice), #19 (ML Printable Report), #20 (ML AI Context Handoff), #21 (ML Patient Linkage) |
| **RESTORED & ENHANCED (Batch C)** | **8** | Features #22 (DL Upload & Preview Canvas), #23 (DL Demo Presets), #24 (Frozen EfficientNet Grad-CAM), #25 (DL Raw Cutoff & Platt Display), #26 (DL AI Advice), #27 (DL Report & Reset Actions), #28 (DL Patient Linkage), #46 (AI Advisor Contextual Result Seeding for DL & ML) |
| **PRESERVED** | **16** | Features #1, #4, #5, #6, #7, #9, #12, #17, #29, #32, #39, #40, #44, #45, #48, #49 |
| **PRESERVED — UX DEGRADED** | **7** | Features #8, #34, #35, #36, #37, #42, #43 |
| **PARTIALLY PRESERVED** | **2** | Features #38, #41 |
| **FRONTEND REGRESSION — BACKEND PRESERVED** | **3** | Features #31, #33, #50 |
| **FULLY LOST** | **2** | Features #30, #47 |
| **SCIENTIFICALLY INCOMPATIBLE — REIMPLEMENT AGAINST FINAL MODEL** | **0** | All scientific reimplementation completed in Batch C (#24) |
| **NEW ENHANCEMENTS PROPOSED** | **0** | Completed in Batch B (#15) |
| **INTENTIONALLY DEFERRED** | **2** | Features #51 (Google OAuth real handshake), #52 (Real SMTP email delivery) |
| **Sum Reconciliation** | **52** | $2 + 10 + 8 + 16 + 7 + 2 + 3 + 2 + 0 + 0 + 2 = \mathbf{52}$ (Reconciled with 0 discrepancies) |

---

## 4. Key Corrections & Clarifications from Prior Audit

1. **Doctor Patient Registry (Features #34–#37)**:
   - Corrected from "Lost" to **PRESERVED — UX DEGRADED**. 
   - Patient Search, Patient Create, Patient Edit, and Patient Delete are all actively implemented in [frontend/js/pages/patients.js](file:///Users/GiangNguyenHuy/Documents/breast-cancer-ai/frontend/js/pages/patients.js). The V4 goal is visual and ergonomic enhancement, not rebuilding nonexistent backend/frontend logic.
2. **Patient-Linked Analysis Workflow (Feature #38)**:
   - Corrected from "Lost" to **PARTIALLY PRESERVED**.
   - [frontend/js/pages/patient-detail.js](file:///Users/GiangNguyenHuy/Documents/breast-cancer-ai/frontend/js/pages/patient-detail.js) already provides "New Structured Analysis" and "New Mammography Analysis" links carrying `?patient_id=<id>`. V4 will add direct action buttons in the main patient table and visible patient context banners in analysis pages.
3. **Prediction History (Features #40–#42)**:
   - Corrected from "Unfiltered table" to **PRESERVED** for analysis type and diagnosis label filtering; **PARTIALLY PRESERVED** for doctor-specific patient dropdown selection.
4. **Prediction Reports (Features #43–#44)**:
   - Corrected from "Placeholder" to **PRESERVED BUT UX DEGRADED**. The page calls `reportService.history()` and renders live persisted analyses; V4 will refine titles, layout hierarchy, and browsing ergonomics.
5. **Report-Image / OCR Feature Extraction (Feature #14)**:
   - Added as a first-class parity row. Backend endpoint `POST /api/v1/predict/extract-clinical/` remains fully operational. Frontend UI was omitted and will be restored with strict numeric validation, reference range verification, and mandatory user review before running predictions.
6. **AI Advice Display vs Handoff (Features #18, #20, #26, #27, #46)**:
   - Distinguished backend generation (PRESERVED) from in-result display (FRONTEND REGRESSION) and contextual transfer to the AI Advisor chat (FULLY LOST).
7. **Logout All Devices (Feature #50)**:
   - Added as a verified row. Backend endpoint `POST /api/v1/auth/logout-all/` is fully operational in `endpoints.py:L851-L855`. Frontend button was omitted from `profile.js` and will be restored.
8. **WDBC Feature Reference Artifact**:
   - `experiments/final/wdbc_feature_reference.json` and `frontend/content/wdbc_feature_reference.json` were audited. They are uncommitted artifacts generated from the 455-sample WDBC development partition (seed 42 outer split, 114 test samples excluded).
   - Classified as: **CANDIDATE NEW ENHANCEMENT — NOT YET BASELINE**. They will be reviewed and formally incorporated during Batch B (Structured ML).

---

## 5. Non-Regression & Restoration Execution Batches

- **Batch A — Overview, Learn & Research Content**: **COMPLETED (PASS)**.
  - Canonical authenticated & guest Overview on `index.html` with compact identity and quick-start bar.
  - Top navigation streamlined to Overview, Analyze, Research (`#research`), Learn (`#learn`), Doctor Workspace / My Activity, AI Guide.
  - Safe compatibility redirect from `/pages/dashboard.html` to `../index.html` with query/hash preservation.
  - 60-second visual research narrative in `#research` with validation-first selection, exact frozen metrics (Study A LR ROC-AUC 0.9954, Study B EfficientNet-B0 ROC-AUC 0.7229), and links to secondary deep-dive routes.
  - Substantial educational hub in `#learn`: anatomy schematic, source-backed screening table (ACS/USPSTF), 6 warning signs cards with non-alarmist framing, AICR New American Plate nutrition, recovery guidance, 4 myth/fact pairs, verified lazy-loaded video library, and accessible native FAQ accordions.
- **Batch B — Structured ML Parity**: Restore presets (Benign/Malignant), Clear button, CSV import & template, OCR extraction modal, LR feature contributions ($z_i$), reference percentiles, patient selector, report button, AI handoff.
- **Batch C — Mammography DL Parity & Frozen Grad-CAM**: Implement Grad-CAM on `top_conv` of frozen EfficientNet-B0 in `final_dl_runtime_service.py`; restore demo mammograms, side-by-side comparison, patient selector, report button, AI handoff.
- **Batch D — Multimodal Fusion Parity**: Restore two-branch cards (ML features + DL Grad-CAM), fusion demo loader, heuristic synthesis explanation.
- **Batch E — Doctor, Patient, History & Reports UX**: Enhance Patient search/create/edit/delete UX, add patient row analysis actions, restore doctor patient filter on History, refine Reports browsing.
- **Batch F — AI Contextual Integration, Logout All & Regression**: Implement contextual result transfer into AI Advisor, floating chat FAB, "Sign out all devices" action, and full test regression suite.
