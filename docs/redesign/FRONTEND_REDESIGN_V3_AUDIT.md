# Frontend Redesign V3 — Comprehensive Audit & Analysis (Revised)

**Document Status:** Phase 0 Discovery Baseline (Revised)  
**Target Branch:** `feat/frontend-redesign-v3`  
**Base Commit SHA:** `5246fa19037831726b5e74c5db5db24e09c0454d` (`docs/final-documentation`)  
**Date:** 2026-09-07  
**Author:** Senior Product Designer & Frontend Architect  

---

## 1. Executive Summary & Context

The Breast Cancer AI research platform is a functional, scientifically frozen software system combining:
1. **Study A (WDBC):** 569 samples, 30 fine-needle aspirate (FNA) numerical cytological features, with a frozen Logistic Regression pipeline using a raw classification decision threshold of `0.36`.
2. **Study B (CBIS-DDSM):** 2,559 processed source mammogram images (5,118 manifest rows including ROIs, 2,354 inferred study-like groups), with a frozen EfficientNet-B0 full-image architecture using a raw classification decision threshold of `0.515`, accompanied by Platt scaling used exclusively for display/reliability assessment.
3. **Study C (Reliability & Explainability):** Calibration curves, 2,000-replicate bootstrap confidence intervals, error analysis (FN/FP tracking), non-causal SHAP feature contributions for WDBC, and coarse qualitative Grad-CAM attention maps for CBIS-DDSM.
4. **Platform Infrastructure:** FastAPI backend with SQLite persistence (`app.db`), session-based bearer authentication, doctor/user role segregation, patient management, automated prediction persistence, authenticated HTML report generation, and an informational AI Advisor.

### Strategic Revision (Post-Phase 0 Review):
Based on explicit executive product decisions, the previous V3 blueprint has been fundamentally redirected:
- **Left Sidebar Rejected:** The "pinned full-height sidebar" is completely discarded. The product will adopt an expansive, modern **Top-Navigation & Horizontal Contextual AppShell**.
- **New Visual Concept:** Abandon generic SaaS admin styling in favor of the **"Breast Health Intelligence Studio"** — an editorial, image-led, medical laboratory experience.
- **New Medical Education Hub (LEARN):** A substantial public visual learning center covering breast cancer biology, screening/mammography, evidence-based nutrition & lifestyle, myths vs. facts, and a curated privacy-conscious video library.
- **Auth & Role Security Overhaul:** Open public registration restricted strictly to `role = user` (preventing unauthorized self-assignment of doctor privileges), paired with **Sign in with Google (OAuth 2.0 / OIDC)**.
- **Unsafe Terminology Purged:** Replacement of clinical-claim terms with responsible research phrasing (*AI Analysis Lab*, *Research Workspace*, *Prediction Report*, *AI Information Assistant*).

---

## 2. Backend & System Architecture

### 2.1 Technology Stack
- **API Runtime:** FastAPI (`backend/app/main.py`) running with Uvicorn.
- **Data Persistence:** SQLite 3 (`backend/data/app.db`) managed via `app.core.database.Database` with WAL mode and foreign keys enabled.
- **Static File Serving & Proxy:** Nginx 1.27-Alpine (`deploy/nginx.conf`) proxying `/api/`, `/results/`, `/healthz`, and `/readyz` to `breast_cancer_api:8000`, serving `/` statically with `try_files $uri $uri/ =404;`.
- **Runtime Model Execution:**
  - `FinalMLRuntimeService`: Loads `logistic_regression_final_seed42.joblib` (StandardScaler + LogisticRegression), verified by SHA-256 against `models/model_registry.example.json`.
  - `FinalDLRuntimeService`: Loads `efficientnetb0_final_seed42.keras` (224x224x3 RGB) and `efficientnet_b0_platt_final_seed42.json`, verified by dual SHA-256 checksums. Fails closed upon mismatch.
- **AI Advisor Service:** OpenAI API integration with safe, deterministic local fallback logic (`app.services.ai_advisor.AIAdvisorService`).

### 2.2 Operational Health Endpoints
- `GET /healthz` → `{"status": "ok"}`
- `GET /readyz` → `{"status": "ready", "database": "ok", "final_ml": "research_demo", "final_dl": "research_demo"}`
- `GET /api/v1/models/final/status/` → Central runtime operational readiness metadata.

---

## 3. Full API Contract Matrix (Including Google Auth & Role Security Updates)

| Area | HTTP Method & Path | Auth Required? | Allowed Roles | Request Body / Query / Multipart | Response Schema | Error Codes | Persistence Behavior | Patient Association | UI Surface / Consuming Page |
|---|---|---|---|---|---|---|---|---|---|
| **AUTH** | `POST /api/v1/auth/register/` | No | Public | JSON: `RegisterRequest` (`email`, `full_name`, `password`). *Client role ignored/enforced to `user`*. | `AuthResponse` (`access_token`, `token_type`, `user`) | 409 (Email exists), 422 (Validation) | Inserts into `users` (always `role='user'`) and `sessions` | N/A | `register.html` |
| **AUTH** | `POST /api/v1/auth/login/` | No | Public | JSON: `LoginRequest` (`email`, `password`) | `AuthResponse` (`access_token`, `token_type`, `user`) | 401 (Invalid creds), 422 (Validation) | Inserts into `sessions` | N/A | `login.html` |
| **AUTH (NEW)**| `POST /api/v1/auth/google/` | No | Public | JSON: `GoogleAuthRequest` (`credential` - Google ID token JWT) | `AuthResponse` (`access_token`, `token_type`, `user`) | 400 (Invalid token), 401 (Unverified email) | Verifies JWT server-side; links/inserts `users` (`role='user'`) & `oauth_accounts`; issues session token | N/A | `login.html`, `register.html` |
| **AUTH** | `GET /api/v1/auth/me/` | Yes (Bearer) | Any authenticated | None | Dict (`id`, `email`, `full_name`, `role`) | 401 (Invalid/expired token) | Reads `users` via session | N/A | Global Topbar, Auth state |
| **AUTH** | `POST /api/v1/auth/logout/` | Yes (Bearer) | Any authenticated | Header: `Authorization: Bearer <token>` | `{"message": "Logged out successfully."}` | 401 (Unauthorized) | Deletes current session from `sessions` | N/A | Topbar Profile Menu |
| **AUTH** | `POST /api/v1/auth/logout-all/` | Yes (Bearer) | Any authenticated | None | `{"message": "Logged out from all sessions."}` | 401 (Unauthorized) | Deletes all sessions for user | N/A | `profile.html` |
| **AUTH** | `PUT /api/v1/auth/profile/` | Yes (Bearer) | Any authenticated | JSON: `UpdateProfileRequest` (`full_name`) | Dict (`id`, `email`, `full_name`, `role`) | 400 (Empty name), 401 (Unauthorized) | Updates `users.full_name`, `updated_at` | N/A | `profile.html` |
| **AUTH** | `POST /api/v1/auth/change-password/` | Yes (Bearer) | Any authenticated | JSON: `ChangePasswordRequest` (`current_password`, `new_password` min 8) | `{"message": "Password changed successfully."}` | 401 (Incorrect password), 422 (Validation) | Updates `users.password_hash`, `updated_at` | N/A | `profile.html` |
| **AUTH** | `POST /api/v1/auth/forgot-password/` | No | Public | JSON: `ForgotPasswordRequest` (`email`) | `ForgotPasswordResponse` (`message`, `reset_token`, `expires_at`) | 422 (Validation) | Inserts into `password_reset_tokens` (expires 2h). | N/A | `forgot-password.html` |
| **AUTH** | `POST /api/v1/auth/reset-password/` | No | Public | JSON: `ResetPasswordRequest` (`token`, `new_password` min 8) | `{"message": "Password updated successfully."}` | 400 (Invalid/expired token), 422 (Validation) | Updates `users.password_hash`, marks token `used_at` | N/A | `reset-password.html` |
| **PATIENTS** | `GET /api/v1/patients/` | Yes (Bearer) | Doctor only | None | `List[PatientResponse]` (`id`, `user_id`, `full_name`, `date_of_birth`, `gender`, `notes`, `created_at`, `updated_at`) | 401, 403 (Forbidden if not doctor) | Selects all patients where `user_id = current_user.id` | N/A | `pages/patients.html` |
| **PATIENTS** | `POST /api/v1/patients/` | Yes (Bearer) | Doctor only | JSON: `PatientCreateRequest` (`full_name`, optional `date_of_birth`, `gender`, `notes`) | `PatientResponse` | 401, 403, 422 | Inserts new patient linked to doctor `user_id` | Owned by doctor | `pages/patients.html` drawer |
| **PATIENTS** | `PUT /api/v1/patients/{patient_id}/` | Yes (Bearer) | Doctor only | Path: `patient_id` (int), JSON: `PatientUpdateRequest` | `PatientResponse` | 401, 403, 404 (Not owner), 422 | Updates patient record | Verifies ownership | `pages/patients.html` edit drawer |
| **PATIENTS** | `DELETE /api/v1/patients/{patient_id}/` | Yes (Bearer) | Doctor only | Path: `patient_id` (int) | `{"message": "Patient deleted successfully."}` | 401, 403, 404 (Not owner) | Deletes row; cascades predictions to `patient_id = NULL` | Verifies ownership | `pages/patients.html` |
| **PREDICTIONS**| `POST /api/v1/predict/` | Optional (Bearer) | Any (Doctor required if `patient_id` provided) | JSON: `PredictionRequest` (30 float fields), Query: `model_name`, `patient_id` (optional int) | `PredictionResponse` (`model_name`, `diagnosis`, `probability`, `raw_probability`, `decision_threshold`, `risk_band`, `analysis_text`, `advice`, etc.) | 400, 403, 404, 503 (Model unavailable) | If authenticated: automatically persists into `predictions` with inputs & outputs | Links to `patient_id` if doctor owned | `pages/ml-analysis.html` |
| **PREDICTIONS**| `POST /api/v1/predict/image/` | Optional (Bearer) | Any (Doctor required if `patient_id` provided) | Multipart: `file` (JPEG/PNG/WebP <=20MB), Form: `model_name`, `include_explanation`, `patient_id` | `PredictionResponse` (`calibrated_probability`, `decision_threshold=0.515`, `raw_probability`, `analysis_text`, `advice`, etc.) | 400 (Bad image), 413, 403, 404, 503 | If authenticated: automatically persists into `predictions` | Links to `patient_id` if doctor owned | `pages/dl-analysis.html` |
| **PREDICTIONS**| `POST /api/v1/predict/multimodal/` | Optional (Bearer) | Any (Doctor required if `patient_id` provided) | Multipart: `clinical_data` (JSON string), `image_file`, Form: `ml_model`, `dl_model`, `patient_id` | `MultiModalResponse` (`ml_result`, `dl_result`, `combined_diagnosis`, `combined_confidence`, `combined_risk_band`, `advice`, `uncertainty_*`) | 400, 403, 404, 503 | If authenticated: persists with fusion metadata | Links to `patient_id` if doctor owned | `pages/multimodal.html` |
| **PREDICTIONS**| `GET /api/v1/predictions/history/` | Yes (Bearer) | Any (Doctor if `patient_id` filtered) | Query: `patient_id` (optional int) | `List[SavedPredictionResponse]` (max 100 recent predictions) | 401, 403, 404 | Reads `predictions` table for user (and optional patient) | Filterable by `patient_id` | `pages/history.html`, `pages/patient-detail.html` |
| **REPORTS** | `GET /api/v1/predictions/{prediction_id}/report/` | Yes (Bearer) | Owner of prediction | Path: `prediction_id` (int) | HTML Document (`text/html; charset=utf-8`, attachment header) | 401, 404 | Renders standalone print-ready HTML prediction report | Verifies user ownership | `pages/reports.html`, `pages/history.html` |
| **AI ADVISOR** | `POST /api/v1/chat/ask/` | Optional (Bearer) | Any | JSON: `ChatRequest` (`message`, `history: List[ChatTurn]`) | `ChatResponse` (`answer`, `provider`, `model`, `created_at`) | 400 (Empty message), 422 | If authenticated: logs turn to `chat_messages` | Unlinked to patient | `pages/advisor.html` |
| **AI ADVISOR** | `GET /api/v1/chat/history/` | Yes (Bearer) | Any authenticated | None | `List[SavedChatMessage]` (max 50 recent turns) | 401 | Reads `chat_messages` where `user_id = current_user.id` | N/A | `pages/advisor.html` |
| **RESEARCH** | `GET /api/v1/research/evidence/` | No | Public | None | Dict: `source`, `ml_candidate`, `ml_metrics`, `dl_candidate`, `dl_metrics`, `roi_decision`, `calibration`, `limitations`, `scope` | None (200) | Reads frozen snapshot `final_results_snapshot.json` | All research pages |
| **MODEL / SYS**| `GET /api/v1/models/final/status/` | No | Public | None | Dict: `{"ml": ..., "dl": ..., "clinical_use": false, "multimodal_status": "experimental_only"}` | None (200) | Returns runtime memory/checksum status | Global Topbar, `pages/dashboard.html`, `pages/model-status.html` |
| **MODEL / SYS**| `POST /api/v1/models/dl/warmup/` | No | Public | Query: `model_name` (optional) | Dict: Status of DL model preload | 503 if unavailable | Preloads TF model into memory | `pages/model-status.html` |

---

## 4. Domain & Entity Model Audit (With Google Auth Extensions)

### 4.1 SQLite Tables & Relationships
```
[users]
  ├── id (INTEGER PRIMARY KEY AUTOINCREMENT)
  ├── email (TEXT UNIQUE)
  ├── full_name (TEXT)
  ├── password_hash (TEXT NULL)  <-- NULL permitted for pure Google OAuth users
  ├── role (TEXT: 'user' | 'doctor')  <-- Public signup ALWAYS 'user'
  ├── is_active (INTEGER DEFAULT 1)
  ├── created_at (TEXT ISO)
  └── updated_at (TEXT ISO)
        │
        ├──< [oauth_accounts] (user_id -> users.id CASCADE)  <-- NEW TABLE
        │      ├── id (INTEGER PRIMARY KEY AUTOINCREMENT)
        │      ├── provider (TEXT NOT NULL, e.g. 'google')
        │      ├── provider_subject (TEXT NOT NULL, Google 'sub')
        │      ├── email (TEXT NOT NULL)
        │      ├── created_at (TEXT ISO)
        │      └── UNIQUE(provider, provider_subject)
        │
        ├──< [sessions] (user_id -> users.id CASCADE)
        │      ├── token (TEXT UNIQUE)
        │      └── expires_at (TEXT ISO)
        │
        ├──< [password_reset_tokens] (user_id -> users.id CASCADE)
        │      ├── token (TEXT UNIQUE)
        │      ├── expires_at (TEXT ISO)
        │      └── used_at (TEXT ISO NULL)
        │
        ├──< [patients] (user_id -> users.id CASCADE) [DOCTOR ONLY]
        │      ├── id (INTEGER PRIMARY KEY)
        │      ├── full_name, date_of_birth, gender, notes
        │      └── created_at, updated_at
        │             └──< [predictions] (patient_id -> patients.id SET NULL)
        │
        ├──< [predictions] (user_id -> users.id SET NULL)
        │      ├── id, prediction_type ('ml'|'dl'|'multimodal'), model_name, diagnosis,
        │      │   probability, raw_probability, calibration_mode, risk_band, advice,
        │      │   analysis_text, input_payload, response_payload, created_at
        │      └──> dynamic HTML report generation
        │
        └──< [chat_messages] (user_id -> users.id CASCADE)
               └── id, question, answer, created_at
```

### 4.2 Security Governance Rules
1. **Public Signup Security:** Self-registration assigns strictly `role = 'user'`. The `role` parameter is either removed from `RegisterRequest` or coerced server-side.
2. **Doctor Role Promotion:** Upgrading an account to `role = 'doctor'` requires an administrative promotion mechanism (database migration script or invite token), preventing unauthorized access to patient health information (PHI) tools.
3. **Google Identity Verification:**
   - Frontend passes Google-signed JWT credential.
   - Backend verifies token via Google API / public certs (verifying signature, issuer `accounts.google.com`, audience `GOOGLE_CLIENT_ID`, and expiry).
   - If user exists by email, safely link `oauth_accounts` row; otherwise create new `users` row with `role='user'` and null `password_hash`.
   - Issue standard application session token into `sessions`.

---

## 5. Frozen Scientific & Safety Contracts

The redesign **must strictly preserve** all scientific statements and runtime semantics:

| Parameter | Study A: WDBC Structured ML | Study B: CBIS-DDSM Mammography DL | Multimodal Combination |
|---|---|---|---|
| **Data Scope** | 569 samples, 30 cytological features derived from digitized FNA images. Stratified split: 455 dev, 114 held-out test. Seed 42. | 2,559 processed images, 2,559 ROIs, 5,118 manifest rows, 2,354 inferred study-like groups. Zero split group overlap. | Unpaired datasets. No patient overlap. Heuristic demonstration only. |
| **Model** | Logistic Regression (StandardScaler + LogisticRegression). | EfficientNet-B0 full processed image (224x224x3). ROI rejected (ROI-C). | 40% ML + 60% DL weighted probability average. |
| **Decision Threshold** | `0.36` raw malignant probability. | `0.515` raw malignant probability. | `0.50` combined probability (heuristic cutoff). |
| **Probability Display** | Raw probability. Calibration: none. | Platt calibrated probability (display/reliability only). **Never classify on Platt probability!** | Combined weighted probability. |
| **Reported Metrics** | ROC-AUC: 0.9954, Sens: 0.9524, Spec: 0.9861, Bal Acc: 0.9692, FN: 2, FP: 1 (held-out test). | ROC-AUC: 0.7229, Sens: 0.6786, Spec: 0.6250, Bal Acc: 0.6518, FN: 54, FP: 84 (held-out test). | No clinical validation claim. |
| **Explainability Semantics** | SHAP explains contribution to malignant log-odds. **Non-causal**. | Grad-CAM provides qualitative coarse attention maps. **Not lesion segmentation or pathology ground truth**. | Discrepancy indicator when ML and DL classifications diverge. |
| **Safety Disclaimers** | Research / Educational Prototype. `clinical_use: false`. Not for clinical diagnosis. | Research / Educational Prototype. `clinical_use: false`. Not for clinical diagnosis. | Experimental software fusion only. |

---

## 6. Current Frontend Architecture Audit

### 6.1 Directory & Dependency Graph
```
frontend/
├── index.html (Landing)
├── login.html, register.html, forgot-password.html, reset-password.html
├── pages/ (16 workspace HTML pages)
├── css/ (app.css aggregating 16 modular stylesheets via @import)
└── js/
    ├── core/ (api.js, auth.js, config.js, guards.js, storage.js)
    ├── services/ (auth, prediction, patient, report, research, advisor, model)
    ├── components/ (shell.js, auth-shell.js, analysis.js, research.js, workspace.js, support.js, toast.js, probability-bar.js)
    ├── config/ (ml-features.js)
    └── pages/ (21 page controller scripts, 1-to-1 with HTML routes)
```

### 6.2 Major Structural Deficiencies in Existing V2
1. **The Left Sidebar Constraint:** Pinned/floating left sidebar restricts horizontal workspace width, squashes complex medical image viewers, and creates an outdated "admin dashboard" visual feel.
2. **Missing Public Educational Experience:** No dedicated educational content for patients or students; all health information was previously buried in raw research tables.
3. **Card-Grid Overuse:** Monotonous repetition of 3-column white boxes with thin borders across every page.
4. **Hero Banner Waste:** 200px mint-tinted banners on every single page push interactive tools below the fold.

---

## 7. Visual & UI Audit (From Real Interface Screenshots)

Inspection of frozen release screenshots (`docs/assets/screenshots/01-landing.jpg` through `08-model-status.jpg`):
- **Landing (`01-landing.jpg`):** Flat mint hero with low-contrast buttons; plain card grids; lack of medical storytelling imagery.
- **Dashboard (`02-dashboard.jpg`):** Massive empty green hero banner; two rows of generic white cards; floating sidebar eats 260px of screen real estate.
- **Structured ML (`03-ml-analysis.jpg`):** An intimidating wall of 30 bare number inputs in a 5-column grid without presets, units, or clinical context.
- **Mammography DL (`04-dl-analysis.jpg`):** Unstyled default file input (`Choose File No file chosen`), broken image state on initial load, empty right column.
- **Research Center (`05-research-center.jpg`):** Metrics dumped as unformatted text strings without visual scorecards or confusion matrix graphics.

---

## 8. UX Problems Ranked by Severity

| Rank | Severity | Issue | User Impact | Redesign Requirement in V3 Studio |
|---|---|---|---|---|
| **1** | **CRITICAL** | Intimidating 30-feature ML input form | Users cannot easily test the ML model without manual, error-prone entry of 30 float numbers. | Introduce grouped step tabs, inline validation, and 1-click canonical benchmark cases (Benign, Malignant, Borderline). |
| **2** | **CRITICAL** | Amateurish DL mammography upload & empty state | Unstyled file input, broken preview image, and lack of drag-drop polish diminish credibility immediately. | High-fidelity drop zone with active drag animations, medical scan preview canvas, file metadata chip, and sample selector. |
| **3** | **HIGH** | Outdated left-sidebar admin layout | Constrains canvas width; feels like generic SaaS instead of a medical intelligence studio. | Shift to sticky top navigation with mega menus and horizontal contextual tabs. |
| **4** | **HIGH** | Lack of public health & educational content | Visitors looking to understand screening, benign vs malignant, or nutrition find only raw ML research. | Build a dedicated, evidence-based Learn / Medical Education Hub. |
| **5** | **HIGH** | Public registration allows self-assigned doctor role | Unauthorized users can gain access to patient management features. | Restrict public registration to `role = user`; implement administrative promotion for doctors. |
| **6** | **HIGH** | Lack of visual differentiation between Raw vs. Platt probability in DL | Risk of user confusing displayed Platt reliability with classification decision cutoff. | Distinct, dedicated probability meters: Primary "Classification Decision (Raw >= 0.515)" alongside secondary "Display Reliability (Platt Scaled)". |
| **7** | **MEDIUM** | Missing modern Google OAuth sign-in | Users forced into manual password creation. | Integrate official Sign in with Google (OIDC) with server-side token validation. |
| **8** | **MEDIUM** | Plain text metric dumps instead of rich data visualization | Evidence looks like an academic draft rather than a premier AI research workspace. | Polished metric scorecards, interactive confusion matrix heatmaps, ROC/PR curves from frozen artifacts. |

---

## 9. Revised Route & Feature Inventory

With the addition of the **Learn Content Hub**, the rigid 21-route constraint is expanded to a comprehensive, organized information architecture:

| Domain | Canonical Path | Role / Access | Feature Classification | Redesign Strategy in V3 |
|---|---|---|---|---|
| **HOME** | `/` (`index.html`) | Public | **REDESIGN** | 12-beat storytelling homepage with medical imagery, research distinction, interactive previews, and educational highlights. |
| **AUTH** | `/login.html` | Public | **REDESIGN** | Premium split-screen layout with medical imagery, Google Sign In, email/password fallback. |
| **AUTH** | `/register.html` | Public | **REDESIGN** | Clean public registration (`role=user` enforced), Google Sign In, confirm password. |
| **AUTH** | `/forgot-password.html` | Public | **REDESIGN** | Cohesive auth styling with clear recovery steps. |
| **AUTH** | `/reset-password.html` | Public | **REDESIGN** | Secure token-based password reset interface. |
| **ANALYZE** | `/pages/dashboard.html` | Authenticated | **REDESIGN** | Studio Overview & Command Center: live telemetry, quick launch cards, recent activity. |
| **ANALYZE** | `/pages/ml-analysis.html` | Authenticated | **REDESIGN** | Structured ML Workstation: 1-click presets, categorized feature tabs, multi-tier result scorecard. |
| **ANALYZE** | `/pages/dl-analysis.html` | Authenticated | **REDESIGN** | Mammography Analysis Studio: drag-drop uploader, scan canvas, dual-probability meter (Raw vs Platt). |
| **ANALYZE** | `/pages/multimodal.html` | Authenticated | **REDESIGN** | Experimental Fusion Lab: side-by-side branch execution with conflict detection and prominent heuristic warning. |
| **RESEARCH** | `/pages/research.html` | Public / Auth | **REDESIGN** | Research Center: master narrative, separate Study A & B cards, protocol links. |
| **RESEARCH** | `/pages/model-comparison.html`| Public / Auth | **REDESIGN** | Benchmark Tables: tabular comparisons with 95% bootstrap CIs and error tracking (FN/FP). |
| **RESEARCH** | `/pages/datasets.html` | Public / Auth | **REDESIGN** | Dataset Explorer: interactive WDBC & CBIS-DDSM manifest splits with zero-overlap verification. |
| **RESEARCH** | `/pages/explainability.html` | Public / Auth | **REDESIGN** | XAI Center: SHAP log-odds feature contributions & Grad-CAM coarse attention gallery. |
| **RESEARCH** | `/pages/calibration.html` | Public / Auth | **REDESIGN** | Reliability Hub: Brier scorecards, Platt sigmoid curves, calibration explanation. |
| **LEARN (NEW)**| `/pages/learn.html` | Public | **NEW** | Education Center Index: visual overview of all 5 learning modules with featured guides. |
| **LEARN (NEW)**| `/pages/learn-breast-cancer.html` | Public | **NEW** | Understanding Breast Cancer: biology, benign vs malignant, risk factors, terminology. |
| **LEARN (NEW)**| `/pages/learn-screening.html` | Public | **NEW** | Screening & Mammography: imaging basics, age recommendations, AI screening limits. |
| **LEARN (NEW)**| `/pages/learn-nutrition.html` | Public | **NEW** | Evidence-Based Nutrition & Lifestyle: plant-rich eating, physical activity, alcohol facts, medical disclaimer. |
| **LEARN (NEW)**| `/pages/learn-myths-facts.html`| Public | **NEW** | Myths vs. Facts: interactive misconception cards with scientific evidence. |
| **LEARN (NEW)**| `/pages/learn-videos.html` | Public | **NEW** | Curated Medical Video Library: lazy-loaded embeds from CDC, NCI, and university health systems. |
| **WORKSPACE** | `/pages/patients.html` | Doctor Only | **REDESIGN** | Patient Registry: searchable table with slide-over drawer for patient creation/editing. |
| **WORKSPACE** | `/pages/patient-detail.html` | Doctor Only | **REDESIGN** | Patient Dossier: demographics, chronological prediction timeline, direct report triggers. |
| **WORKSPACE** | `/pages/history.html` | Authenticated | **REDESIGN** | Prediction History Log: paginated analysis log filterable by type and diagnosis. |
| **WORKSPACE** | `/pages/reports.html` | Authenticated | **REDESIGN** | Prediction Reports: modal preview and instant HTML report download. |
| **SYSTEM** | `/pages/advisor.html` | Public / Auth | **REDESIGN** | AI Information Assistant: chat stream with suggested research prompt chips and non-diagnostic disclaimers. |
| **SYSTEM** | `/pages/model-status.html` | Public / Auth | **REDESIGN** | Runtime Telemetry: live health pulse, SHA checksum tags, input shape specs, memory warmup. |
| **SYSTEM** | `/pages/profile.html` | Authenticated | **REDESIGN** | Account & Security: profile details, role badge, password change, single/all session termination. |
