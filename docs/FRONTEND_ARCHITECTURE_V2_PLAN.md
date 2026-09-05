# Frontend Architecture V2 Plan

## Objective

Replace the single-page monolith with static HTML pages and vanilla ES modules while preserving all frozen research and backend contracts.

## Migration

1. Establish shared CSS, API/auth core, service modules, shell components, and static route validation.
2. Create public/auth entry pages and the reusable authenticated workspace shell.
3. Move dashboard, prediction, research, patient, history, report, advisor, model-status, and profile controllers into page modules.
4. Remove the giant `app.js` from active entry pages only after each workflow has an equivalent module path.

## Invariants

- ML raw classification threshold: `0.36`.
- DL raw classification threshold: `0.515`; Platt is display/reliability only.
- WDBC and CBIS-DDSM evidence stays separate.
- All model surfaces state research/educational use and `clinical_use=false`.
- Nginx continues serving only static frontend files and proxying `/api/` and `/results/`.

## Batch 2 Verification

Completed on 2026-09-05 for commit `116cde8`.

- Nginx served `200` for `/`, `/login.html`, `/register.html`, `/forgot-password.html`, `/reset-password.html`, and `/pages/dashboard.html`.
- Public CSS and V2 core/service/component/page modules resolved over Nginx with `200`; static `node --check` passed for every V2 module.
- Chrome headless rendered the landing successfully through `http://127.0.0.1/` at desktop viewport. The host Chrome emitted its known display/updater permission noise but produced a valid screenshot; no application asset failure was observed.
- Auth smoke was non-destructive: invalid login returned controlled `401 {"detail":"Invalid email or password"}`. Forgot-password with a non-existent email returned the intended generic `200` response with no reset token.
- Browser interaction checks at tablet/mobile remain a final full-browser QA gate for Batch 8. Batch 2's HTTP/module/auth gate is complete.

## Batch 3 Verification

Completed on 2026-09-05 from research product checkpoint `d2b817c`.

- Nginx returned `200` for the landing, dashboard, Research Center, Model Comparison, Dataset Explorer, Explainability, Calibration, sampled controllers/services/components/CSS, and `/api/v1/research/evidence/`.
- All research pages consume `researchService.studies()`, which adapts the central frozen evidence endpoint. WDBC and CBIS-DDSM remain separate and no combined leaderboard is rendered.
- Chrome rendered Research Center through Nginx at `1440x900`; metrics and tables resolved without `NaN`, `undefined`, missing modules, or broken images. Host display/updater messages were Chrome infrastructure noise.
- A `390x844` screenshot exposed horizontal grid/table overflow and a missing mobile sidebar trigger. The focused responsive fix constrains grid children/table wrappers and adds an ARIA-controlled mobile menu.
- Explainability intentionally renders no Grad-CAM case images or SHAP values without canonical case/vector metadata. Calibration displays frozen raw/Platt validation Brier and ECE and states that classification uses raw probability `>= 0.515`.
- Static validation, all JS syntax checks, `24` backend tests, compileall, and final application verification passed.

## Batch 4 Analysis Contracts And Verification

- Canonical routes are `pages/ml-analysis.html`, `pages/dl-analysis.html`, and `pages/multimodal.html`; shared feature configuration prevents duplicated payload keys.
- ML sends the exact 30-key `PredictionRequest` JSON to `POST /predict/`. Optional model/patient association uses query parameters. Backend preprocessing is unchanged and classification remains raw malignant probability `>= 0.36`.
- DL sends multipart field `file` to `POST /predict/image/`; model/patient/explanation options are query parameters. Classification remains raw probability `>= 0.515`; Platt is displayed separately for reliability only.
- Experimental multimodal sends `clinical_data` and `image_file` to `POST /predict/multimodal/`. Both component outputs stay visible; the 40% ML / 60% DL combined score is labeled an unvalidated heuristic over unpaired datasets.
- Authenticated predictions are automatically persisted by the backend; V2 therefore does not present a fake Save action. Reports/history remain later Batch 5 destinations.
- Nginx returned `200` for all three routes and sampled controllers/services/components/CSS. Chrome rendered the desktop ML workflow with correct active navigation and no missing assets.
- All JS syntax checks, V2 static validation, `24` backend tests, compileall, final-application verification, and production-readiness verification passed. Responsive CSS stacks features and analysis/result columns for narrow screens; full interactive cross-device automation remains the final Batch 8 sweep.

## Batch 5 Workspace Contracts And Verification

- Canonical authenticated routes are `pages/patients.html`, `pages/patient-detail.html?id=<id>`, `pages/history.html`, and `pages/reports.html`. Only numeric patient ids enter query strings; patient data is not persisted in URLs or local storage.
- Patient CRUD uses backend fields `full_name`, `date_of_birth`, `gender`, and `notes`. Listing and mutations are doctor-protected by the backend. Search is explicitly client-side over the complete currently loaded response; the API has no search or pagination contract.
- Prediction history is automatically persisted for authenticated predictions and returns at most 100 records. Patient-specific history uses `GET /predictions/history/?patient_id=<id>` and retains stored raw probability fields without reconstructing missing calibrated values.
- The backend has no report registry or PDF generator. Reports Library derives entries from persisted history and opens live authenticated HTML from `GET /predictions/{id}/report/`. Shared shell code fetches report HTML with the bearer header and opens a Blob URL, keeping credentials out of URLs.
- Dynamic patient/history values are HTML-escaped and no patient records are logged. Authentication guards protect canonical workspace pages; backend `401`, `403`, `404`, and validation messages are rendered as controlled text.
- Patient detail analysis links pass only a validated numeric `patient_id`; both ML and DL controllers forward it through the existing prediction-service query contract so authenticated predictions retain their patient association.
- Nginx returned `200` for all workspace routes, controllers, and shared components. Static validation, JavaScript syntax checks, `24` backend tests, and compileall passed. Desktop rows collapse into mobile cards via semantic responsive CSS.
