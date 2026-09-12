# Web Feature Freeze Specification (V1)

**Document Version**: 1.0.0  
**Phase**: Phase 4R — Web Feature Freeze  
**Date**: 2026-09-12  
**Branch**: `feat/product-experience-v4`  
**Baseline Commit**: `feat/product-experience-v4` (Batch F)  
**Status**: **FROZEN (Release Candidate 1 / RC-1)**

---

## 1. Feature Freeze Declaration

As of Batch F completion, all web features, user experiences, scientific copy, machine learning / deep learning inference pipelines, and role-based access workflows are formally **FROZEN**.

No new web features, structural layout changes, API schema modifications, or model retraining operations may take place on the web product without formal unfreezing and re-verification.

---

## 2. Frozen Web Scope & Capabilities

The following capabilities represent the complete, verified, frozen web product:

### 2.1 Public & Educational Experience
- **Overview Landing (`index.html`)**:
  - Contextual authentication display: dynamically adapts to guest, personal user, or clinician.
  - Sourced screening guidelines visibly separating ACS (Oeffinger et al., *JAMA* 2015) and USPSTF (2024 Update, *JAMA* 2024) recommendations.
  - Clinical warning signs gallery with 6 non-alarmist informational cards.
  - AICR New American Plate lifestyle recommendations.
  - Interactive accessible FAQ accordions with keyboard navigation.
  - Academic decoupling narrative between Study A (Wisconsin ML) and Study B (CBIS-DDSM Mammography DL).
  - Telemetry and model validation summaries linking to research deep dives.

### 2.2 Model Analysis Workstations
- **Wisconsin Cytology ML (`pages/ml-analysis.html`)**:
  - 30-feature WDBC input grid with real-time field status classification (Common, Unusual, Extreme, Outside observed).
  - Canonical research presets (Benign #842302, Malignant #842517).
  - Outlier review safeguard modal for values outside observed development bounds ($N=455$).
  - CSV multi-row importer with data normalization and preview selector.
  - OCR report-image feature extractor with user inspection dialog.
  - Frozen Logistic Regression runtime with raw decision threshold $0.360$.
  - Exact log-odds feature contribution visualizer ($z_i = w_i \cdot \frac{x_i - \mu_i}{\sigma_i}$).
  - Contextual AI Guide handoff and authenticated printable report viewer.
  - Doctor-only patient linkage selector.
- **Mammography DL (`pages/dl-analysis.html`)**:
  - 2D digital projection mammogram dropzone and canvas preview with metadata inspector.
  - Canonical research presets (Benign 0.425 raw, Malignant 0.614 raw).
  - Frozen EfficientNet-B0 runtime with raw classification cutoff $0.515$.
  - Decoupled Platt calibrated display probability ($p_{\text{cal}} = \sigma(A \cdot z + B)$).
  - Real-time Grad-CAM on `top_conv` with interactive visual comparison canvas (Side-by-side, Original, Grad-CAM Overlay) and fail-safe fallback.
  - Contextual AI Guide handoff, authenticated report viewer, and doctor patient selector.
- **Experimental Multimodal Fusion (`pages/multimodal.html`)**:
  - Dual-branch converging research workstation accepting 30 WDBC features and a mammography image.
  - Prominent Branch Disagreement card rendered BEFORE combined score when model classifications conflict.
  - Transparent mathematical formula visualizer ($0.40 \times \text{ML\_RAW} + 0.60 \times \text{DL\_RAW}$).
  - Explicit software heuristic labeling with $0.50$ midpoint; zero clinical diagnosis claims.
  - Shared doctor patient context, Grad-CAM visualization, authenticated report viewer, and AI Guide handoff.

### 2.3 Doctor & Patient Management Workspaces
- **Doctor Workspace (`pages/patients.html`)**:
  - Searchable patient registry with real-time text query filtering.
  - New Patient registration modal with client validation.
  - Patient record deletion modal with cascading safety confirmation.
  - Longitudinal patient timeline on `patient-detail.html`.
- **Shared Workspaces**:
  - Activity History (`pages/history.html`) with role-adaptive patient filter.
  - Analysis Reports workspace (`pages/reports.html`) with one-click view and print actions.
  - Profile & Security (`pages/profile.html`) with password update, account management, and session revocation.

### 2.4 Research Transparency & Telemetry
- **Research Transparency Hub (`pages/research.html`)**:
  - Side-by-side study design cards comparing Wisconsin WDBC (Study A) and CBIS-DDSM (Study B).
  - Authoritative TCIA / CBIS-DDSM provenance and attribution card with official DOI citations.
  - Frozen calibration methodology (Platt scaling with isotonic regression comparisons).
  - Formal study decoupling statement clarifying that Study A and Study B are independent patient cohorts.
- **Model Status & Telemetry (`pages/model-status.html`)**:
  - Real-time healthcheck querying live runtime model endpoints.
  - Model artifact checksums and input shape specifications.

### 2.5 Security, Authentication & Privacy
- **Strict Role Contracts**:
  - Registration strictly enforces `account_type: Literal["personal", "doctor"] = "personal"`.
  - Rejection of invalid types or role escalation attempts with HTTP 422.
- **Transient Context Privacy**:
  - Mandatory clearance of `bcai_advisor_context`, `bcai_active_analysis`, and `bcai_patient_context` upon logout, session termination, or new user login.
- **Session Revocation**:
  - Dedicated "Revoke All Sessions" action on `profile.html` with clean session invalidation wording (no refresh token references).
- **Modal Accessibility**:
  - Universal Tab focus trapping, Escape key closing, and focus restoration via `bindModalAccessibility`.

---

## 3. Pre-Deploy Blocker: Demo Mammogram TCIA Attribution

> [!NOTE]
> **PRE-DEPLOY BLOCKER STATUS: RESOLVED (100% Verified)**
> The license and provenance of the two demonstration mammogram assets have been byte-for-byte audited and formally documented:
>
> 1. **Verified Lineage**:
>    - `demo-benign-mammogram.png` (SHA-256: `3876586b8d712a4782c790bdc184bd602ec6432be2a228fe1b3cabc7252c3dbe`) is byte-for-byte identical to CBIS-DDSM test ROI `1.3.6.1.4.1.9590.100.1.2.16525291111973690409014716492507936377`.
>    - `demo-malignant-mammogram.png` (SHA-256: `966a7860655798e6f061392d3cedbd9e8ca57db8c37a5776ca16735d7837e8ac`) is byte-for-byte identical to CBIS-DDSM test ROI `1.3.6.1.4.1.9590.100.1.2.404758686111730252108640081234072137432`.
> 2. **License Compliance**: Distributed under **Creative Commons Attribution 3.0 Unported (CC BY 3.0)** per TCIA Data Usage Policies.
> 3. **Formal Documentation**: Detailed citations for Sawyer-Lee et al. (2016), Lee et al. (2017), and Clark et al. (2013) are recorded in [CBIS_DDSM_DATA_AND_DEMO_ATTRIBUTION.md](file:///Users/GiangNguyenHuy/Documents/breast-cancer-ai/docs/legal/CBIS_DDSM_DATA_AND_DEMO_ATTRIBUTION.md) and exposed via an authoritative card in `frontend/js/pages/research.js`.

---

## 4. Deferred Live Credentials & Infrastructure Steps

The following operational items require external live infrastructure (DNS, domain TLS certificates, operator secrets) and are deferred to live integration:

| Item | Architecture & Requirements | Deferred Status |
| :--- | :--- | :--- |
| **Google OAuth Live Credentials** | Uses **Google Identity Services (GIS)** client-side popup/callback flow + backend ID token verification (`google.oauth2.id_token.verify_oauth2_token`). **No `GOOGLE_CLIENT_SECRET` is needed**; only `GOOGLE_CLIENT_ID` and authorized JavaScript origins in Google Cloud Console. | Waiting for operator Google Cloud Console client ID |
| **Production SMTP Email Service** | Transactional email delivery for password resets. `APP_MAIL_MODE=smtp` requires live operator credentials (`SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`). | Waiting for operator SMTP relay configuration |
| **Production Domain, HTTPS & DNS** | Public FQDN, Let's Encrypt / Certbot TLS certificates, and Nginx reverse proxy configuration. | Waiting for operator DNS cutover |
| **Mobile Native Applications** | React Native / Flutter / iOS / Android wrapper apps. Phase 4R is strictly a web-only feature freeze. | Out of scope for web freeze |
| **Model Retraining & Multimodal Learning** | Retraining ML or DL models or training an end-to-end learned multimodal network. Frozen scientific evidence baseline must remain intact. | Frozen / Not permitted |

---

## 5. Verification Sign-Off

- **Batch B E2E (Structured ML)**: PASS (100%)
- **Batch C E2E (Mammography DL)**: PASS (100%)
- **Batch D E2E (Multimodal Fusion)**: PASS (100%)
- **Batch E E2E (Doctor Workspaces)**: PASS (100%)
- **Batch F E2E (Final Web Polish)**: PASS (100%)
- **Backend Unit & Integration Tests**: 73/73 PASSED
- **Broken Link & Asset Crawler**: 21 documents audited, 117 links verified, 0 broken links
- **Static Frontend Code Quality**: PASS
- **Legacy Feature Parity**: 52/52 accounted for (50 operational, 2 deferred, 0 lost)
