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
