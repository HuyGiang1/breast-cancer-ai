# Frontend V2 Final QA

Date: 2026-09-07
Branch: `feat/frontend-architecture-v2`
Baseline: `6c30a7b`

## Result

Frontend V2 is **FROZEN FOR RELEASE**. This means no further feature redesign before final documentation/release unless a blocker is discovered. Research/model contracts were not changed.

## Evidence matrix

| Gate | Evidence | Result |
| --- | --- | --- |
| Canonical routes | 21/21 HTTP and browser render checks | PASS |
| Viewports | 21 routes at 1440x900, 1280x800, 768x1024, and 390x844: 84/84 | PASS |
| Browser runtime | Expected controller/CSS, nonblank DOM, active navigation, no overflow, no legacy request, no uncaught exception or unexpected HTTP error | PASS |
| Auth | Register, duplicate registration, wrong password, unknown email, forgot/reset, login, logout, auth guard, guest guard | PASS |
| Roles | Ordinary-user patient access returned controlled 403; doctor-owned disposable patient lifecycle passed | PASS |
| ML | Test fixture, 30/30 completion, value retention, browser validation, Logistic Regression, raw threshold 0.36 | PASS |
| DL | Frozen CBIS fixture, preview/remove/re-upload, EfficientNet-B0, raw threshold 0.515, separate Platt display, corrupt image 400 | PASS |
| Multimodal | Both components, 40/60 score, experimental/unpaired warning | PASS |
| Workspace | Create/list/search/detail/edit/associated predictions/timeline/history/delete using disposable records | PASS |
| Reports | Authenticated HTML, bearer header flow, no token URL, research/nonreplacement disclaimer, missing report 404 | PASS |
| Advisor | Saved history, suggestion, keyboard-capable form, local clear, plain-text response, provider/fallback-safe UX | PASS |
| Status/profile | Runtime/readiness refresh and offline state; supported profile fields, update, password change, logout | PASS |
| Research semantics | WDBC/CBIS metrics, dataset counts/group caveats, calibration values, XAI limitations verified from rendered DOM | PASS |
| Static/backend | JS syntax, dependency validator, diff check, 24 pytest tests, compileall, final application and production readiness | PASS |

## Route and viewport matrix

Public/auth routes: `/`, login, register, forgot password, reset password. Workspace routes: dashboard; ML, DL, and experimental multimodal; Research Center, Model Comparison, Datasets, Explainability, Calibration; Patients, Patient Detail, History, Reports; Advisor, Model Status, Profile.

Every route passed structural inspection at desktop, laptop, tablet, and mobile sizes. Mobile public and authenticated drawers open and close, support Escape, maintain `aria-expanded`, and return focus to the trigger. Direct unauthenticated workspace navigation redirects to login; authenticated visits to login return to Dashboard.

## Scientific verification

- WDBC Logistic Regression rendered ROC-AUC 0.9954, sensitivity 0.9524, specificity 0.9861, balanced accuracy 0.9692, FN 2, FP 1.
- CBIS-DDSM EfficientNet-B0 rendered ROC-AUC 0.7229, sensitivity 0.6786, specificity 0.6250, balanced accuracy 0.6518, FN 54, FP 84.
- Dataset UI distinguishes 5,118 manifest rows from independent mammograms and calls 2,354 groups inferred study-like groups, not verified patients. Split overlap is 0/0/0.
- DL calibration rendered validation Brier 0.2327 raw versus 0.2118 Platt and ECE 0.1139 raw versus 0.0221 Platt. Classification remains raw probability `>= 0.515`.
- SHAP and Grad-CAM remain noncausal research explanations; the UI does not claim segmentation, localization, pathology truth, or cross-study ranking.

## Accessibility, performance, network, and security

Forms use labels/native validation, result/status regions use live semantics, status is not color-only, images have alt text, reduced motion is respected, and keyboard focus is visible. Buttons have a 42px minimum height. Tables retain text and horizontal wrappers; there are no canvas-only charts.

Tracked static frontend source is under 90 KB excluding ignored runtime results. No removed legacy bundles, external trackers, polling, resize loops, or large referenced images were observed. Page requests are action/data bounded; offline model-status failure resolves to controlled retry UI rather than an infinite spinner.

No `eval`/`new Function`, patient/password/token logging, bearer query parameter, or secret was found. Advisor output uses text nodes; patient/history and model identity fields are escaped. Report HTML is fetched with the Authorization header and opened as a Blob URL.

## Fixes from final QA

- Added close control, Escape handling, focus return, and link-close behavior to the mobile workspace drawer.
- Added Escape/link-close behavior and accurate accessible name/controls state to the public drawer.
- Bound Advisor controls before awaiting saved history so slow history cannot swallow early user actions.
- Added global keyboard focus visibility and minimum command-button height.

## Known limitations

- The structured ML form is a continuous grouped 30-field form, not a wizard with back/next steps.
- Explainability describes frozen evidence but does not publish unverified dynamic Grad-CAM placeholders or a fabricated SHAP ranking.
- Browser QA used desktop Chrome emulation, not a physical-device lab or formal WCAG certification.
- External advisor providers can return availability/quota errors; controlled fallback/error behavior is retained.
- Static-client authentication continues to use the existing local-storage bearer contract.
- VPS, domain, DNS, TLS, and external deployment remain blocked on infrastructure/credentials.
