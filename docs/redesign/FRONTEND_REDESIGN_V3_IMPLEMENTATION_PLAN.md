# Frontend Redesign V3 — Technical Implementation Plan & Roadmap (Revised)

**Document Status:** Phase 0 Implementation Plan (Revised)  
**Target Branch:** `feat/frontend-redesign-v3`  
**Base Commit SHA:** `5246fa19037831726b5e74c5db5db24e09c0454d`  
**Date:** 2026-09-07  
**Author:** Senior Frontend Architect & Design Systems Engineer  

---

## 1. Architectural Strategy & Framework Re-Evaluation

Following the major product expansion (top navigation, mega-menus, public medical education hub, video library, medical imagery, Google Sign In, and doctor-role security changes), the framework evaluation has been re-examined:

### 1.1 In-Depth Framework Comparison Matrix

| Evaluation Dimension | Option A: Enhanced Modular Vanilla Architecture (Vanilla ES Modules + Modern CSS Design System) | Option B: Build-Based Modern Framework (React + TypeScript + Vite) |
|---|---|---|
| **Architectural Nature** | Native browser ES Modules; modern CSS custom properties; structured JSON/HTML content layer; zero build step. | Single Page Application (SPA); JSX/TSX compilation; Vite bundler; virtual DOM; React state management. |
| **New Scope Handling (Mega-Menus, Content Hub, Videos)** | **High Efficiency.** Mega-menus and video cards are clean, declarative DOM structures. Content is cleanly separated in `frontend/content/` modules. | **High Capability.** Clean component composition; JSX simplifies conditional rendering for complex tabs. |
| **Google Sign-In Integration** | **Native & Frictionless.** Official Google Identity Services script (`https://accounts.google.com/gsi/client`) natively mounts to a DOM container in 5 lines of vanilla JS. | **Identical.** Uses `@react-oauth/google` or vanilla GSI wrapper component. |
| **API & Backend Compatibility** | **100% Identical.** Consumes existing FastAPI endpoints, session tokens, and the new `/api/v1/auth/google/` endpoint. | **100% Identical.** Consumes same endpoints. |
| **Nginx & Docker Hosting Impact** | **Zero Impact.** Served directly by existing Nginx (`try_files $uri $uri/ =404;`) and existing Compose volume mounts (`./frontend:/usr/share/nginx/html:ro`). | **High Impact.** Requires: (1) multi-stage Dockerfile or pre-commit build step to produce `dist/`; (2) modifying `nginx.conf` to add SPA fallback (`try_files $uri $uri/ /index.html;`); (3) updating Docker Compose build context. |
| **Static Verification & CI Gates** | **Zero Risk.** Preserves and extends `scripts/verify_frontend_v2.py` checks (route integrity, reachability, zero dead files, no local paths). | **Breaking.** Completely invalidates `scripts/verify_frontend_v2.py`. Requires rewriting CI verification scripts from scratch. |
| **Performance & Bundle Overhead** | **Zero Overhead.** 0 KB framework runtime; instant initial load; zero bundling delay; native browser execution. | **Moderate Overhead.** ~150-250 KB minified React/ReactDOM/Router runtime bundle before application code. |
| **Visual Quality & Polish Ceiling** | **Unconstrained (100%).** Modern CSS (Grid, Flexbox, Container Queries, Transitions, Shadows, Inter & JetBrains typography, SVG icons) provides identical visual fidelity to Stripe, Linear, or Vercel. | **Unconstrained (100%).** Equal visual capability. |
| **Deployment Timeline Risk** | **Zero Deployment Risk.** Fully aligned with the immediate server deployment phase (`deploy/server-production`). | **High Risk.** Introduces Node.js build dependencies, package lock churn, and deployment script revisions right before production release. |

### 1.2 Senior Architectural Recommendation: Option A (Enhanced Modular Architecture)
**Recommendation:** We firmly reaffirm **Option A**.  
**Rationale:**
1. Visual elegance, rich typography, mega-menus, lazy-loaded video embeds, and medical imagery are **design system and CSS capabilities**, not framework-bound limitations.
2. Option A keeps the frontend 100% native, lightning-fast, and completely decoupled from Node build pipelines.
3. It guarantees that the impending server deployment (`deploy/server-production`), Docker configuration, and existing automated CI test suite remain completely reliable and uninterrupted.

---

## 2. Backend & Security Enhancements Required

To support the updated product decisions, three controlled backend changes are incorporated:

### 2.1 Public Registration Security (`role = user`)
- **Action:** In `backend/app/api/endpoints.py`, update `register()` so that public registration strictly assigns `role = 'user'`.
- **Validation:** Disregard any client-supplied `role` parameter during public self-registration.
- **Doctor Promotion:** Provide an administrative promotion mechanism (or migration script) for verified clinical accounts.

### 2.2 Google Authentication Endpoint (`POST /api/v1/auth/google/`)
- **Request Schema:** `GoogleAuthRequest(credential: str)` (receives the Google ID token JWT).
- **Server-Side Token Validation:** Verify signature using Google public keys (`google-auth` library or lightweight `jwt` verification against `https://www.googleapis.com/oauth2/v3/certs`).
- **Validation Checks:** Validate signature, issuer (`accounts.google.com`), audience (`GOOGLE_CLIENT_ID`), expiry, and `email_verified == true`.
- **Identity Linking:**
  - Create SQLite table `oauth_accounts` (`user_id`, `provider`, `provider_subject`, `email`, `created_at`).
  - If a user with that email already exists, link the Google `sub` to the existing account.
  - If new user, insert into `users` (`role = 'user'`, `password_hash = NULL`) and record the link.
  - Issue standard session token into `sessions`.

---

## 3. Revised 10-Phase Implementation Roadmap

```
[Phase 0] Discovery & Blueprint Revision (Current Baseline)
    ↓
[Phase 1] Studio Design System & CSS Foundation
    ↓
[Phase 2] Global Topbar, Mega-Menus & Top-Sheet Mobile Navigation
    ↓
[Phase 3] 12-Beat Public Landing Page & Healthcare Storytelling
    ↓
[Phase 4] Public Medical Education Hub (LEARN) & Lazy Video Library
    ↓
[Phase 5] Auth Redesign, Role Security & Sign in with Google
    ↓
[Phase 6] Studio Command Dashboard & Operational Telemetry
    ↓
[Phase 7] AI Analysis Workstations (Structured ML, Mammography DL, Multimodal)
    ↓
[Phase 8] Research Evidence Hub & Methodology Suite
    ↓
[Phase 9] Patient Workspace & Prediction Reporting
    ↓
[Phase 10] Cross-Device QA, Triple QA Gates & Documentation Sync
```

---

### Detailed Phase Breakdown

#### Phase 0: Discovery, Blueprint & Architecture Revision (CURRENT)
- **Scope:** Update all 4 blueprint documents with top-navigation architecture, "Breast Health Intelligence Studio" visual concept, Learn hub, medical imagery strategy, Google Auth, and doctor-role security model.
- **Commit Checkpoint:** `docs: establish revised frontend redesign v3 blueprint`
- **Stop Condition:** Await user review and authorization.

#### Phase 1: Studio Design System & CSS Foundation
- **Scope:** Complete design tokens overhaul. Google Font **Inter** and **JetBrains Mono** integration; Slate neutral palette; Teal and Sapphire accents; multi-layered shadow diffusion; full-width layout utilities.
- **Files Touched:**
  - `frontend/css/tokens.css`
  - `frontend/css/typography.css`
  - `frontend/css/layout.css`
  - `frontend/css/components.css`
  - `frontend/css/reset.css`
  - `frontend/css/app.css`

#### Phase 2: Global Topbar, Mega-Menus & Top-Sheet Mobile Navigation
- **Scope:** Build the top-based horizontal navigation header, mega-menu overlays for *Analyze*, *Research*, and *Learn*, horizontal contextual sub-tabs, and full-screen top-sheet navigation for mobile/tablet.
- **Files Touched:**
  - `frontend/js/components/shell.js`
  - `frontend/css/navigation.css`

#### Phase 3: 12-Beat Public Landing Page & Healthcare Storytelling
- **Scope:** Implement the 12-beat storytelling homepage featuring high-resolution medical imagery, Study A vs. Study B comparison cards, live interactive analysis preview, and safety boundaries.
- **Files Touched:**
  - `frontend/index.html`
  - `frontend/js/pages/landing.js`
  - `frontend/css/public.css`

#### Phase 4: Public Medical Education Hub (LEARN) & Lazy Video Library
- **Scope:** Build the 5 public education modules (Understanding Breast Cancer, Screening & Mammography, Nutrition & Lifestyle, Myths vs. Facts, and Video Library) with structured content files and lazy-loaded privacy-conscious video embeds.
- **Files Touched:**
  - `frontend/pages/learn.html`
  - `frontend/pages/learn-breast-cancer.html`
  - `frontend/pages/learn-screening.html`
  - `frontend/pages/learn-nutrition.html`
  - `frontend/pages/learn-myths-facts.html`
  - `frontend/pages/learn-videos.html`
  - `frontend/js/pages/learn*.js`
  - `frontend/content/` (structured articles & metadata)
  - `frontend/css/learn.css`

#### Phase 5: Auth Redesign, Role Security & Sign in with Google
- **Scope:** Redesign login, register, forgot-password, and reset-password with the medical split-screen layout. Implement `POST /api/v1/auth/google/` backend verification, database schema addition (`oauth_accounts`), and enforce `role = user` on public signup.
- **Files Touched:**
  - `backend/app/core/database.py`
  - `backend/app/api/endpoints.py`
  - `backend/app/api/schemas.py`
  - `frontend/login.html`, `frontend/register.html`, `frontend/forgot-password.html`, `frontend/reset-password.html`
  - `frontend/js/pages/login.js`, `frontend/js/pages/register.js`
  - `frontend/css/auth.css`

#### Phase 6: Studio Command Dashboard & Operational Telemetry
- **Scope:** Upgrade `/pages/dashboard.html` into the Studio Command Center: quick analysis actions, live runtime telemetry tiles (WDBC `0.36`, CBIS `0.515`), and recent workspace activity feed.
- **Files Touched:**
  - `frontend/pages/dashboard.html`
  - `frontend/js/pages/dashboard.js`
  - `frontend/css/workspace.css`

#### Phase 7: AI Analysis Workstations (Structured ML, Mammography DL, Multimodal)
- **Scope:** Complete redesign of the core inference interfaces. Grouped ML parameter tabs with 1-click benchmark case loaders; radiological drag-and-drop mammogram uploader with dark preview canvas; dual-probability decision gauges; side-by-side multimodal fusion with divergence warnings.
- **Files Touched:**
  - `frontend/pages/ml-analysis.html`, `frontend/js/pages/ml-analysis.js`
  - `frontend/pages/dl-analysis.html`, `frontend/js/pages/dl-analysis.js`
  - `frontend/pages/multimodal.html`, `frontend/js/pages/multimodal.js`
  - `frontend/js/components/analysis.js`
  - `frontend/css/prediction.css`

#### Phase 8: Research Evidence Hub & Methodology Suite
- **Scope:** Modernize the 5 research modules with unified horizontal sub-tabs, tabular comparisons featuring 95% bootstrap CIs, interactive SHAP log-odds feature bars, and Grad-CAM attention galleries.
- **Files Touched:**
  - `frontend/pages/research.html`, `frontend/js/pages/research.js`
  - `frontend/pages/model-comparison.html`, `frontend/js/pages/model-comparison.js`
  - `frontend/pages/datasets.html`, `frontend/js/pages/datasets.js`
  - `frontend/pages/explainability.html`, `frontend/js/pages/explainability.js`
  - `frontend/pages/calibration.html`, `frontend/js/pages/calibration.js`
  - `frontend/css/research.css`

#### Phase 9: Patient Workspace & Prediction Reporting
- **Scope:** Upgrade doctor-only patient management: searchable registry table, slide-over drawer for patient editing, patient timeline dossier, and authenticated HTML report preview modal.
- **Files Touched:**
  - `frontend/pages/patients.html`, `frontend/js/pages/patients.js`
  - `frontend/pages/patient-detail.html`, `frontend/js/pages/patient-detail.js`
  - `frontend/pages/history.html`, `frontend/js/pages/history.js`
  - `frontend/pages/reports.html`, `frontend/js/pages/reports.js`
  - `frontend/css/workspace.css`

#### Phase 10: Cross-Device QA, Triple QA Gates & Documentation Sync
- **Scope:** Enforce the Triple QA Gates (Functional, Visual, Product QA). Run full automated regression test suite; refresh release screenshots; synchronize README and compiled report artifacts.
- **Commands Executed:**
  - `find frontend/js -name "*.js" -print0 | xargs -0 -n1 node --check`
  - `python3 scripts/verify_frontend_v2.py`
  - `PYTHONPATH=.:backend venv/bin/python -m pytest -q`
  - `PYTHONPATH=.:backend venv/bin/python scripts/verify_final_application.py`
  - `PYTHONPATH=.:backend venv/bin/python scripts/verify_production_readiness.py`
  - `venv/bin/python scripts/build_final_report.py`
  - `venv/bin/python scripts/validate_final_report.py`

---

## 4. Triple QA Gates (Mandatory Evaluation Standard)

Every redesigned page must pass three independent evaluation gates before being considered complete:

```
                  ┌────────────────────────┐
                  │    1. FUNCTIONAL QA    │  (API contracts, error codes, auth tokens)
                  └───────────┬────────────┘
                              │ PASS
                              ▼
                  ┌────────────────────────┐
                  │     2. VISUAL QA       │  (Editorial polish, typography, no card soup)
                  └───────────┬────────────┘
                              │ PASS
                              ▼
                  ┌────────────────────────┐
                  │     3. PRODUCT QA      │  (Safety disclaimers, terminology, ethics)
                  └───────────┬────────────┘
                              │ PASS
                              ▼
                        PAGE COMPLETE
```

### 4.1 Gate 1: Functional QA
- All API contracts strictly satisfied (matching schemas in `endpoints.py`).
- Zero console exceptions or unhandled promise rejections.
- Smooth asynchronous loading states, shimmer skeletons, and descriptive error recovery banners.
- Keyboard navigation functional with visible 2px focus ring.
- Session persistence verified across page reloads.

### 4.2 Gate 2: Visual QA
- **Originality & Distinctiveness:** The page does **NOT** resemble a generic Bootstrap dashboard, Tailwind template, or AI-generated card grid.
- **Composition & Hierarchy:** Clear editorial flow with intentional whitespace, varied component widths, and asymmetric layouts where appropriate.
- **Typography Rigor:** Clear size and weight contrast (Inter headings, JetBrains Mono for data/metrics, tabular numerals).
- **Imagery Relevance:** High-resolution medical, anatomical, or lifestyle imagery properly framed, credited, and responsive.
- **Interaction Polish:** Smooth 150–250ms transitions on hover, focus, and modal reveals.

### 4.3 Gate 3: Product QA
- **Non-Diagnostic Disclaimer:** Prominent display of *Research / Educational Prototype. Not for clinical diagnosis.*
- **Frozen Contract Integrity:** Exact thresholds verified (`0.36` for ML, `0.515` for DL). Platt calibration explicitly framed as display/reliability only.
- **Approved Terminology:** Strictly avoids forbidden terms (*Clinical AI Workspace*, *Cancer Cure Diet*, etc.) in favor of approved research terms.
- **Medical Attribution:** Every educational claim and video cites verified public health sources (NCI, CDC, WHO, ACS).
- **Role Permissions:** Doctor-only features strictly hidden or guarded for standard user accounts.
