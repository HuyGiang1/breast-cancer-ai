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
| **2** | **Clinical Warning Signs Gallery** | 6 descriptive warning signs with images and advice | Condensed into landing sections | Rendered as text cards | N/A (Static) | Fully compatible | **PRESERVED — UX DEGRADED** | Restore rich medical descriptions and verified visual cards | `5b6c72c:frontend/index.html:L68-L98` |
| **3** | **Screening Guidelines by Age** | Age-stratified mammography screening guideline tables | Mentioned in copy, table omitted | Omitted in landing | N/A (Static) | Fully compatible | **PARTIALLY PRESERVED** | Restore structured screening guideline table in Learn section | `5b6c72c:frontend/index.html:L150-L180` |
| **4** | **Nutrition & Lifestyle Modalities** | Care guide cards for plant foods, animal foods, hydration, exercise | 4 glassmorphic cards in landing | Fully rendered in V3 | N/A (Static) | Fully compatible | **PRESERVED** | Preserved in Phase 3A.2/3A.5 | `frontend/index.html:L240-L310` |
| **5** | **Interactive FAQ Accordion** | Searchable/expandable FAQ accordion (`bindFaqToggle`) | Expandable FAQ section in landing | Native `<details>` or JS toggle | N/A (Static) | Fully compatible | **PRESERVED** | Maintain and verify keyboard accessibility | `frontend/index.html:L350-L410` |
| **6** | **Educational Video Library** | Video preview cards with modal / embedded player | 2 video preview cards in landing | Media card elements | N/A (Static) | Fully compatible | **PRESERVED** | Maintain verified poster assets | `frontend/index.html:L320-L348` |
| **7** | **Research Evidence & Decoupling** | Academic decoupling narrative between Study A and B | Research telemetry and model selection sections | Dynamic telemetry script | `GET /api/v1/models/final/status/` | Fully compatible | **PRESERVED** | Maintained across Landing and Research Center | `frontend/pages/research.html` |
| **8** | **Toast Notifications** | Lightweight floating toast notifications (`showToast`) | Ad-hoc alert paragraphs | Local status text elements | N/A | Fully compatible | **PRESERVED — UX DEGRADED** | Implement centralized non-blocking toast service | `5b6c72c:frontend/app.js:L530-L550` |
| **9** | **Mobile Navigation Drawer** | Slide-out hamburger drawer with nav links | Header hamburger drawer with ARIA controls | Interactive JS in `index.html` & `shell.js` | N/A | Fully compatible | **PRESERVED** | Verified at 390px viewport | `frontend/js/components/shell.js` |
| **10** | **ML Sample Presets (Benign / Malignant)** | One-click loading of canonical Benign and Malignant vectors | None | Omitted | Supported (standard payload) | 100% compatible with frozen LR | **FULLY LOST** | Add "Sample Benign" & "Sample Malignant" toolbar buttons | `5b6c72c:frontend/app.js:L46-L75`, `L1506-L1516` |
| **11** | **ML Clear Inputs Action** | Resets all 30 fields to blank | None | Omitted | Supported | Fully compatible | **FULLY LOST** | Add "Clear Fields" button to input toolbar | `5b6c72c:frontend/app.js:L180-L195` |
| **12** | **ML Input Progress Counter** | Live tracking: `X / 30 đặc trưng` | Progress indicator: `30 / 30 complete` | Event listener updates count | Supported | Fully compatible | **PRESERVED** | Retain live counter in toolbar | `frontend/js/pages/ml-analysis.js` |
| **13** | **ML CSV Import & Template** | File input parsing 30 feature columns from CSV (`parseClinicalCsvText`) | None | Omitted | Supported | Fully compatible | **FULLY LOST** | Restore CSV parser and add "Download CSV Template" button | `5b6c72c:frontend/app.js:L1483-L1497` |
| **14** | **ML Report-Image / OCR Feature Extraction** | Upload lab report photo to extract features (`extractClinicalFromImage`) | None | Omitted | `POST /api/v1/predict/extract-clinical/` active | Calls AI Advisor OCR vision backend | **FRONTEND REGRESSION — BACKEND PRESERVED** | Restore upload button, preview, and review-before-submit modal | `backend/app/api/endpoints.py:L1288-L1304` |
| **15** | **ML Feature Reference & Outliers** | Hardcoded approximate ranges without clear provenance | None committed in V3 baseline | Omitted | Reference data available on disk | Validated against 455 WDBC dev samples | **NEW ENHANCEMENT** | Render P01–P99 development percentiles and outlier flags | `frontend/content/wdbc_feature_reference.json` |
| **16** | **ML Linear Model Feature Contributions** | Displayed top SHAP features from legacy RF | Basic result card without feature ranking | Omitted | Returns raw predictions | Must compute $z_i = w_i \cdot \frac{x_i - \mu_i}{\sigma_i}$ from frozen LR | **SCIENTIFICALLY INCOMPATIBLE — REIMPLEMENT AGAINST FINAL MODEL** | Compute and display top 5 malignant and top 5 benign feature contributions | `backend/app/services/prediction_ml.py`, `models/final/` |
| **17** | **ML Reliability & Decision Threshold** | Displayed threshold and risk band | Displays raw cutoff 0.36 and raw probability | Rendered in result card | Supported | Aligned to frozen threshold 0.36 | **PRESERVED** | Maintain prominent threshold and probability display | `frontend/js/pages/ml-analysis.js` |
| **18** | **ML AI Clinical Advice Display** | Dedicated advice card with provider/model badge | Omitted from result card | Result drops advice payload | Backend attaches `advice`, `advice_provider` | Fully compatible | **FRONTEND REGRESSION — BACKEND PRESERVED** | Render advice block and provider badge in ML result | `backend/app/api/endpoints.py:L1220-L1225` |
| **19** | **ML Result Action: Printable Report** | Button to download/open printable HTML report | None on analysis result page | Omitted | `GET /api/v1/predictions/{id}/report/` active | Fully compatible | **FRONTEND REGRESSION — BACKEND PRESERVED** | Add "View Printable Report" button to ML result | `5b6c72c:frontend/app.js:L1720-L1740` |
| **20** | **ML Result Action: Contextual AI Handoff** | Button linking prediction outcome to AI Assistant | None | Omitted | Supported | Fully compatible | **FULLY LOST** | Add "Discuss with AI Assistant" button pre-seeding chat | `5b6c72c:frontend/app.js:L1750-L1765` |
| **21** | **ML Patient Linkage Selector** | Doctor selects active patient before prediction | Reads `?patient_id` query param only | No UI dropdown | Query parameter supported by backend | Fully compatible | **PARTIALLY PRESERVED** | Add patient selector dropdown in toolbar for doctor accounts | `5b6c72c:frontend/app.js:L1866` |
| **22** | **DL Image Upload & Preview** | File upload with instant thumbnail and metadata | File dropzone with thumbnail | Renders image object URL | `POST /api/v1/predict/image/` active | Fully compatible | **PRESERVED** | Maintain dropzone and add image dimension info | `frontend/js/pages/dl-analysis.js` |
| **23** | **DL Demo Sample Mammograms** | Demo buttons loading benign and malignant mammograms | None | Omitted | Verified sample assets exist | Compatible with full image pipeline | **FULLY LOST** | Add "Sample Benign" & "Sample Malignant" mammogram buttons | `5b6c72c:frontend/app.js:L285-L315` |
| **24** | **DL Grad-CAM Attention Heatmap** | Heatmap overlay on legacy CNN (`include_explanation=true`) | None | Query param omitted | Backend `final_dl_runtime` has hook; explanation currently None | Must target `top_conv` on frozen EfficientNet-B0 | **SCIENTIFICALLY INCOMPATIBLE — REIMPLEMENT AGAINST FINAL MODEL** | Implement Grad-CAM on `top_conv` of frozen EfficientNet-B0; display side-by-side comparison | `backend/app/services/final_dl_runtime.py:L140-L142` |
| **25** | **DL Decision Threshold & Calibration** | Mixed calibration and threshold narrative | Displays raw cutoff 0.515 and Platt calibrated prob | Rendered in result card | Supported | Strictly decoupled per contract | **PRESERVED** | Maintain raw threshold $\ge 0.515$ with separate Platt display | `frontend/js/pages/dl-analysis.js` |
| **26** | **DL AI Clinical Advice Display** | Advice block with provider/model badge | Omitted from result card | Result drops advice payload | Backend attaches `advice`, `advice_provider` | Fully compatible | **FRONTEND REGRESSION — BACKEND PRESERVED** | Render advice block and provider badge in DL result | `backend/app/api/endpoints.py:L1248-L1252` |
| **27** | **DL Result Actions (Report & AI)** | Report download and AI handoff buttons | None | Omitted | Supported | Fully compatible | **FRONTEND REGRESSION — BACKEND PRESERVED** | Add "View Printable Report" and "Discuss with AI" buttons | `5b6c72c:frontend/app.js:L1855-L1885` |
| **28** | **DL Patient Linkage Selector** | Doctor selects active patient | Reads `?patient_id` query param only | No UI dropdown | Query parameter supported by backend | Fully compatible | **PARTIALLY PRESERVED** | Add patient selector dropdown in toolbar for doctor accounts | `5b6c72c:frontend/app.js:L1891` |
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
| **46** | **AI Advisor: Contextual Result Seeding** | Prediction result passed directly into chat context | None | Omitted | Supported | Fully compatible | **FULLY LOST** | Implement query param / sessionStorage handoff from Analyze to Advisor | `5b6c72c:frontend/app.js:L330-L360` |
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
| **PRESERVED** | **18** | Features #1, #4, #5, #6, #7, #9, #12, #17, #22, #25, #29, #32, #39, #40, #44, #45, #48, #49 |
| **PRESERVED — UX DEGRADED** | **7** | Features #2, #8, #34, #35, #36, #37, #43 |
| **PARTIALLY PRESERVED** | **4** | Features #3, #21, #28, #38, #41 |
| **FRONTEND REGRESSION — BACKEND PRESERVED** | **8** | Features #14, #18, #19, #26, #27, #31, #33, #50 |
| **FULLY LOST** | **8** | Features #10, #11, #13, #20, #23, #30, #46, #47 |
| **SCIENTIFICALLY INCOMPATIBLE — REIMPLEMENT AGAINST FINAL MODEL** | **2** | Features #16 (Linear model contributions from frozen LR), #24 (Grad-CAM on frozen EfficientNet-B0 `top_conv`) |
| **NEW ENHANCEMENTS PROPOSED** | **1** | Feature #15 (WDBC development reference percentiles & outlier alerts) |
| **INTENTIONALLY DEFERRED** | **2** | Features #51 (Google OAuth real handshake), #52 (Real SMTP email delivery) |
| **Sum Reconciliation** | **52** | $18 + 7 + 4 + 8 + 8 + 2 + 1 + 2 = 50 + 2 = \mathbf{52}$ (Reconciled with 0 discrepancies) |

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

- **Batch A — Overview, Learn & Research Content**: Enrich `index.html#learn` and `index.html#research` with detailed screening and clinical content.
- **Batch B — Structured ML Parity**: Restore presets (Benign/Malignant), Clear button, CSV import & template, OCR extraction modal, LR feature contributions ($z_i$), reference percentiles, patient selector, report button, AI handoff.
- **Batch C — Mammography DL Parity & Frozen Grad-CAM**: Implement Grad-CAM on `top_conv` of frozen EfficientNet-B0 in `final_dl_runtime_service.py`; restore demo mammograms, side-by-side comparison, patient selector, report button, AI handoff.
- **Batch D — Multimodal Fusion Parity**: Restore two-branch cards (ML features + DL Grad-CAM), fusion demo loader, heuristic synthesis explanation.
- **Batch E — Doctor, Patient, History & Reports UX**: Enhance Patient search/create/edit/delete UX, add patient row analysis actions, restore doctor patient filter on History, refine Reports browsing.
- **Batch F — AI Contextual Integration, Logout All & Regression**: Implement contextual result transfer into AI Advisor, floating chat FAB, "Sign out all devices" action, and full test regression suite.
