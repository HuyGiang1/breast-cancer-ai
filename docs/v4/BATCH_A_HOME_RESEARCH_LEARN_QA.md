# Phase 4R Batch A QA & Restoration Report: Canonical Overview, Home, Learn & Research

**Document Version**: 1.0.0  
**Execution Date**: 2026-09-08  
**Branch**: `feat/product-experience-v4`  
**Audit Baseline**: `98e2f1e` (`docs: lock legacy feature parity baseline for v4 restoration`)  
**Functional Baseline**: `5b6c72c` (`frontend/app.js` + `frontend/index.html`)  
**Status**: **PASS (0 Defects, 0 Regressions)**

---

## 1. Executive Summary & Core Objective

The primary objective of **Phase 4R — Batch A** was to restore and enrich the educational and research capabilities of the application while establishing `/index.html` as the **single canonical Overview** for both guest visitors and authenticated users (researchers and physicians).

The user explicitly rejected dividing the application into a public landing page and a detached, generic SaaS dashboard (`dashboard.html`). In Batch A, `/index.html` remains the singular editorial gateway, adapting seamlessly based on user authentication state.

### Key Deliverables Completed:
1. **Parity Matrix Reconciliation**: Corrected arithmetic and classified rows so that the category sums match the 52 audited features exactly ($2 + 18 + 7 + 4 + 8 + 8 + 2 + 1 + 2 = 52$).
2. **Canonical Overview**: `/index.html` serves as the primary overview for both guests and authenticated sessions.
3. **Session-Aware Adaptation**:
   - Guests see public actions (`Sign In`, `Create Account`, `Explore Research Studies`, `Learn Breast Health`).
   - Authenticated normal users see compact identity (`Welcome, <name>`), profile links, and an integrated **Quick Start** bar (FNA Cytology Analysis, Mammography Vision, Experimental Fusion, My Analysis History, Prediction Reports).
   - Doctors additionally see the **Doctor Workspace** shortcut in both the topbar and Quick Start strip.
4. **Auth Redirects**: Successful login and registration now route to `/index.html`.
5. **Dashboard Compatibility Route**: Visiting `/pages/dashboard.html` executes an immediate, loop-free redirection to `../index.html`, preserving query strings and hash anchors.
6. **Top Navigation Simplification**: Canonical navigation comprises `Overview` (`/index.html`), `Analyze` (mega-menu), `Research` (`#research`), `Learn` (`#learn`), `Doctor Workspace` / `My Activity`, `AI Guide`, and `Account`. From internal `/pages/*` routes, anchors point to `../index.html#research` and `../index.html#learn`.
7. **Smooth Anchor Scrolling**: CSS `scroll-margin-top` accounts for the sticky 72px topbar with native smooth scrolling and full accessibility under `prefers-reduced-motion`.
8. **Research Rebuild for Normal People**: Replaced intimidating engineering tables with a 60-second visual research narrative:
   - What Did We Study? (Study A WDBC FNA vs Study B CBIS-DDSM Mammography)
   - What Models Did We Test? (Study A: LR, RF, XGB; Study B: EfficientNet-B0, ResNet50, Custom CNN)
   - How Did We Choose the Final Model? (Validation-first selection on 5-fold OOF CV and frozen validation split)
   - Held-Out Test Evidence (Study A LR ROC-AUC ~0.9954; Study B EfficientNet-B0 ROC-AUC ~0.7229 with separate Platt reliability display)
   - Explainability & Limitations (Strict decoupling, non-clinical research prototype disclaimer)
   - 6 Secondary Deep-Dive Buttons to technical research sub-pages.
9. **Learn Educational Hub Rebuild**: Substantial progressive disclosure hub containing:
   - Anatomy & Cellular Biology reference schematic
   - Age-Stratified Screening Guidance table with verified ACS/USPSTF source citations
   - 6 Clinical Warning Signs cards with responsible, non-alarmist educational framing
   - Evidence-Based Nutrition & Lifestyle Modalities (AICR New American Plate) with strict non-cure guardrails
   - Recovery, Survivorship & Wellbeing guidance
   - 4 Myths vs Facts cards
   - Video Library with verified metadata, duration, posters, and privacy-respecting lazy loading
   - Practical FAQ Accordion answering key clinical/AI questions using semantic, accessible HTML5 `<details>`.

---

## 2. Old → New Feature Parity Proof

| Parity Row | Feature Name | BEFORE: Legacy Capability (`5b6c72c`) | CURRENT V3: What Was Degraded / Lost (`8eba137`) | AFTER V4: Restored / Improved State | REGRESSION CHECK: Evidence Current Capabilities Not Lost |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **#1** | **Hero & Public Entry** | Hero banner with quick triage CTA and workflow entry cards. | Public landing only; redirected authenticated users to separate `dashboard.html`. | `/index.html` is the canonical Overview for both guests and logged-in users. Added session-aware Quick Start strip without disrupting the editorial layout. | `frontend/index.html`, `v4-a-overview-guest-1440.png`, `v4-a-overview-auth-1440.png`. Full public hero and telemetry demo preserved. |
| **#2** | **Clinical Warning Signs Gallery** | 6 descriptive warning signs with images and advice (`5b6c72c:L68-L98`). | Condensed into generic landing text cards without detailed symptom guidance or visual icons. | Restored 6 rich medical warning cards with icons, specific morphological descriptions, and calm "when to seek evaluation" guidance. | `frontend/index.html:L1060-L1140`. E2E suite verified no horizontal overflow at 390px. |
| **#3** | **Screening Guidelines by Age** | Age-stratified mammography screening guideline tables (`5b6c72c:L150-L180`). | Text mention only; structured age table omitted from landing. | Restored structured, readable screening table stratified by age bands (20s–30s, 40–44, 45–54, 55+, and High-Risk), explicitly citing ACS and USPSTF with source links. | `frontend/index.html:L980-L1050`. Verified source registry compliance. |
| **#4** | **Nutrition & Lifestyle Modalities** | Care guide cards for plant foods, animal foods, hydration, exercise. | Preserved in V3, but lacked clear medical guardrails. | Enhanced with AICR New American Plate evidence, hydration, gentle activity, and explicit disclaimers: foods do not cure cancer or alter model probabilities. | `frontend/index.html:L1140-L1210`. Tested on desktop and mobile. |
| **#5** | **Interactive FAQ Accordion** | Searchable/expandable FAQ accordion (`bindFaqToggle`). | Basic accordion list. | Rebuilt using native HTML5 `<details class="faq-item">` and `<summary>` for instant accessibility, keyboard navigation (Tab/Space/Enter), and screen-reader compliance. | `frontend/index.html:L1320-L1410`. E2E test `FAQ accordion toggled open: true`. |
| **#6** | **Educational Video Library** | Video preview cards with modal player. | 2 video preview cards with unverified metadata. | Verified real videos from American Cancer Society (ACS Guideline Overview: 05:40; Science Behind Screening: 02:21). Implemented poster-first lazy loading (no third-party iframes until play button clicked). | `frontend/index.html:L1260-L1310`. E2E test `Lazy video iframe initialized on click: true`. |
| **#7** | **Research Evidence & Decoupling** | Monolithic text cards mixing datasets and models. | Technical engineering dashboard pages (`research.html`), too complex for general visitors. | Built 60-second visual storytelling section directly on `index.html#research` (Studies A & B separated, validation-first selection, exact frozen held-out metrics, XAI, limitations) + links to secondary deep-dive pages. | `frontend/index.html:L420-L820`, `v4-a-research-1440.png`. Secondary routes (`research.html`, `model-comparison.html`, `datasets.html`) fully preserved. |

---

## 3. Route & Compatibility Audit

### A. Auth Redirection Verification
- **Login Flow (`/login.html`)**:
  - Submitting valid credentials redirects directly to `/index.html`.
  - Tested with regular user and doctor accounts.
- **Registration Flow (`/register.html`)**:
  - Submitting valid registration form auto-logs in and routes directly to `/index.html`.
  - User role is strictly enforced as `'user'` on both client and server.
- **Password Reset Flow (`/reset-password.html`)**:
  - Successfully updating password routes user to login / index overview cleanly.

### B. Backward Compatibility (`/pages/dashboard.html`)
- **Direct Navigation by Guest**: Visiting `http://localhost/pages/dashboard.html` when logged out immediately executes `location.replace('../index.html' + location.search + location.hash)`. Arrives at public overview without auth loops.
- **Direct Navigation by Authenticated User**: Visiting `http://localhost/pages/dashboard.html` when logged in redirects immediately to `../index.html`, displaying the authenticated Overview and Quick Start strip.
- **Query & Hash Preservation**: Any appended search parameters or anchor hashes are passed through safely.

---

## 4. Screenshot Evidence Gate

All 7 required visual artifacts were captured via Chrome DevTools Protocol at native resolutions, saved to `docs/redesign/screenshots/` and IDE artifact directories, and manually inspected for aesthetic excellence.

| Screenshot Name | Viewport | Target State / View | Visual Quality & Parity Verification |
| :--- | :---: | :--- | :--- |
| `v4-a-overview-guest-1440.png` | 1440×900 | Public Guest Overview | Premium editorial landing, hero safety pill, mammography scan with Grad-CAM Coarse Attention overlay, frozen metric pills, topbar actions (`Sign In`, `Create Account`). |
| `v4-a-overview-auth-1440.png` | 1440×900 | Authenticated User Overview | Seamless session adaptation: topbar shows `Welcome, QA Normal User` and `Profile`; Quick Start strip shows 5 workflow shortcuts; Doctor Workspace is strictly hidden. |
| `v4-a-overview-auth-390.png` | 390×844 | Mobile Authenticated Overview | Zero horizontal overflow; clean vertical Quick Start stack with tactile touch targets; hamburger menu with role-appropriate links. |
| `v4-a-research-1440.png` | 1440×900 | Research Story Section (`#research`) | 60-second visual story; distinct Study A and Study B selection boards; exact frozen metrics (LR ROC-AUC 0.9954; EfficientNet-B0 ROC-AUC 0.7229); 6 secondary route buttons. |
| `v4-a-learn-1440.png` | 1440×900 | Learn Educational Hub (`#learn`) | Educational nav pills; anatomy reference schematic; screening guidelines table; warning signs gallery; nutrition guidelines; lazy video library; accessible FAQ. |
| `v4-a-learn-390.png` | 390×844 | Mobile Learn Hub (`#learn`) | Zero horizontal overflow; fluid typography; touch-friendly video cards and expandable FAQ accordions. |
| `v4-a-doctor-overview-1440.png` | 1440×900 | Doctor Role Overview | Doctor session state: greeting `Welcome back, Dr QA Doctor` with `Physician / Doctor` badge; `Doctor Workspace` button in Quick Start strip and topbar. |

---

## 5. Automated Verification & Test Results

```bash
# 1. Frontend JavaScript Syntax Check
find frontend/js -name "*.js" -print0 | xargs -0 -n1 node --check
# Result: PASS (0 syntax errors across all modular JS files)

# 2. Git Diff Whitespace Check
git diff --check
# Result: PASS (0 whitespace errors)

# 3. Static Frontend Validator
python3 scripts/verify_frontend_v2.py
# Result: FRONTEND V2 STATIC VALIDATION: PASS

# 4. Pytest Backend Suite
PYTHONPATH=.:backend venv/bin/python -m pytest -q
# Result: 37 passed, 3 warnings in 12.79s

# 5. Final Application Integration Verifier
PYTHONPATH=.:backend venv/bin/python scripts/verify_final_application.py
# Result: FINAL APPLICATION VERIFICATION: PASS

# 6. Broken Link & Asset Crawler
node scripts/qa_broken_link_crawler.js
# Result: Audited 116 internal links, scripts, stylesheets, and media references. Total defects found: 0

# 7. End-to-End Browser QA Suite
node scripts/qa_browser_e2e_suite.js
# Result: QA SUITE FINISHED. Total Defects: 0, Console errors: 0, Unexpected network errors: 0
```

---

## 6. Scientific Decoupling & Frozen Runtime Integrity

1. **Study A (WDBC Cytology)**:
   - Development Selection: Logistic Regression chosen on 5-fold OOF CV.
   - Held-out Test Report: ROC-AUC 0.9954, Sensitivity 95.24%, Specificity 98.61%, Brier score 0.0209 at raw decision threshold $\ge 0.360$.
   - Display: Strictly decoupled; no comparison against Study B.
2. **Study B (CBIS-DDSM Mammography)**:
   - Development Selection: EfficientNet-B0 chosen on frozen validation split.
   - Held-out Test Report: ROC-AUC 0.7229, Sensitivity 67.86%, Specificity 62.50%, Brier score 0.2297 at raw decision threshold $\ge 0.515$.
   - Calibration: Platt calibration used exclusively for display/reliability interpretation; raw threshold $\ge 0.515$ governs binary prediction.
3. **Clinical Guardrail**:
   - Explicit disclaimer preserved across all pages: `clinical_use = false`.
   - Clear distinction between coarse Grad-CAM attention saliency and histological tumor margins.
4. **Project Identity**:
   - Supervisor: `GV. Đoàn Thị Thanh Hằng`.
   - Title: `Nghiên cứu ứng dụng học sâu trong hỗ trợ chẩn đoán ung thư vú qua ảnh X-quang tuyến vú và đặc trưng tế bào học`.

---

## 7. Untracked Artifact Integrity Check

The two candidate WDBC feature reference artifacts remain untracked and intact on disk for Batch B review:
- `experiments/final/wdbc_feature_reference.json` (untracked, preserved)
- `frontend/content/wdbc_feature_reference.json` (untracked, preserved)

No other unintended untracked files exist in the worktree.
