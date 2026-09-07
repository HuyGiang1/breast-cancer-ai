# Frontend Architecture V2

Last updated: 2026-09-07

## Canonical architecture

```text
HTML route -> page controller -> service -> core API client -> FastAPI
                         |-> shared component
app.css -> semantic CSS modules
Nginx -> static files, /api/, /results/, /healthz, /readyz
```

The frontend is static HTML, CSS, and browser ES modules. Each canonical HTML route owns exactly one page controller. Controllers coordinate interaction; services own HTTP contracts; `core/api.js` owns API base resolution, bearer authentication, JSON parsing, and common error handling.

## Route inventory

Public routes are `/`, `/login.html`, `/register.html`, `/forgot-password.html`, and `/reset-password.html`.

Authenticated workspace routes are:

- Overview: `/pages/dashboard.html`
- Analysis: `/pages/ml-analysis.html`, `/pages/dl-analysis.html`, `/pages/multimodal.html`
- Research: `/pages/research.html`, `/pages/model-comparison.html`, `/pages/datasets.html`, `/pages/explainability.html`, `/pages/calibration.html`
- Workspace: `/pages/patients.html`, `/pages/patient-detail.html?id=<id>`, `/pages/history.html`, `/pages/reports.html`
- Assistant: `/pages/advisor.html`
- System: `/pages/model-status.html`, `/pages/profile.html`

Public landing hash links are same-page document anchors, not SPA routes. Authenticated navigation contains only explicit V2 HTML destinations.

## Modules

- `frontend/js/core/`: API, auth storage, configuration, guards, and JSON storage.
- `frontend/js/services/`: auth, prediction, patient, report, research, advisor, and model APIs.
- `frontend/js/components/`: shell, auth shell, analysis/result, probability, research, workspace, support, and toast UI.
- `frontend/js/pages/`: one controller for each of the 21 canonical HTML pages.
- `frontend/css/`: tokens, reset, typography, layout/navigation, components/forms/tables/charts, prediction, research, workspace, support, auth, public, and responsive rules.

## Contracts and safety

WDBC Logistic Regression classification uses raw probability threshold `0.36`. CBIS-DDSM EfficientNet-B0 classification uses raw probability threshold `0.515`; frozen Platt is display/reliability only. The datasets remain separate studies and multimodal 40/60 output combination remains `experimental_only`.

Patient CRUD and patient-specific history use backend ownership/doctor checks. Reports are authenticated generated HTML, not a PDF registry. Advisor messages are plain text and no patient data is automatically supplied. Profile exposes only email, full name, backend role, name update, password change, and logout.

Bearer tokens and cached user identity use local storage as the existing static-client session contract. Tokens are added only as Authorization headers, never query parameters. Dynamic patient/history values and model-result identity fields are escaped; advisor content uses `textContent`. No patient, password, or token data is logged.

## Research data

Research pages consume the central `/api/v1/research/evidence/` adapter. Small WDBC/CBIS protocol constants describe dataset structure; frozen performance evidence comes from the packaged API snapshot. The UI does not combine ML and DL into a shared leaderboard.

## Static hosting

Nginx serves `frontend/` at `/`, proxies API/runtime routes, and returns a real `404` for missing static routes. There is no SPA fallback and no directory listing. ES modules are served with JavaScript MIME type. The API is internal to the Compose network; Nginx is the public entry point.

## Legacy retirement

Before cutover, `app.js` was 113,040 bytes, `styles.css` 53,350 bytes, and `premium.css` 16,286 bytes: 182,676 bytes total. No canonical route imported them. Batch 7 removed all three, two unreachable JS shims, and eight unreferenced demo/article images. Workspace and support rules moved into semantic CSS modules.

Legacy sample-image/autofill conveniences, image-to-clinical extraction UI, floating chat launcher, health article cards, and hash-based SPA switching were intentionally retired. They were development/convenience or obsolete presentation behavior outside the canonical product inventory; backend endpoints were not removed. Ignored `frontend/results/` remains available for runtime-generated outputs and is not final research evidence.

The final tracked frontend has 21 canonical pages, 21 page controllers, 5 core modules, 7 services, 8 components, and 18 CSS files. `scripts/verify_frontend_v2.py` enforces route-controller mapping, references, imports, reachability, navigation uniqueness, CSS graph integrity, and absence of legacy bundles/local paths.

## Final QA and freeze

Batch 8 verified all 21 routes at 1440x900, 1280x800, 768x1024, and 390x844 for an 84/84 browser matrix. The matrix checked controllers, CSS, page titles, populated content, active navigation, overflow, network responses, exceptions, and absence of legacy requests. Disposable API/browser workflows covered auth and roles, ML/DL/multimodal predictions, patient association, history/reports, advisor, model status, profile, and representative error states.

Final QA added accessible mobile drawer close/Escape behavior, global keyboard focus visibility, minimum button height, and immediate advisor control binding while history loads. Full evidence and known limitations are recorded in `docs/FRONTEND_FINAL_QA.md`. Frontend V2 is frozen for release; only release-blocking defects should change it before final documentation.
