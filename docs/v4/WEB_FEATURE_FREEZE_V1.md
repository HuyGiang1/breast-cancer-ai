# Web Feature Freeze Specification (V1)

**Document Version**: 1.0.0  
**Phase**: Phase 4R — Web Feature Freeze  
**Date**: 2026-09-12  
**Branch**: `feat/product-experience-v4`  
**Baseline Commit**: `feat/product-experience-v4` (Batch F)  
**Status**: **FROZEN (Release Candidate Candidate 1 / RC-1)**

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
  - Restricted to Doctor Workspace accounts; personal accounts receive an access-restricted card.
  - Workspace metrics strip (Total Patients, Analyses Logged, ML, DL, Fusion counts).
  - Real-time patient search by name, ID, or research notes.
  - Modality filtering and multi-attribute sorting.
  - Accessible modal dialogs for patient registration, demographic editing, and safety-explicit deletion (preserving analysis logs).
- **Patient Detail & Longitudinal Timeline (`pages/patient-detail.html`)**:
  - Demographic summary and Research Notes sidebar.
  - 3-modality quick launch action bar linking directly to analysis workstations with preselected patient ID.
  - Chronological analysis timeline displaying modality badges, classification pills, and direct report triggers.
- **Activity History (`pages/history.html`)**:
  - Personal accounts: "My Activity" personal analysis history.
  - Doctor accounts: "Analysis Activity" with in-memory patient dropdown selector filtering across the entire dataset.
  - Date range filters (From / To) and dynamic count badge (`Showing X of Y analyses`).
  - Authenticated report view and print triggers.
- **Reports Workspace (`pages/reports.html`)**:
  - Comprehensive listing of persisted analyses with Date Range filters, modality filters, and active count badges.
  - Direct authenticated report inspection and browser print triggers.

### 2.4 AI Guide & Communication
- **AI Research Guide (`pages/advisor.html`)**:
  - Safe DOM markdown parser (`renderSafeContent`) with zero unsafe `innerHTML` injection.
  - Grounded multimodal contextual banners explaining branch weighting ($0.40 / 0.60$), software midpoints, and dataset decoupling.
  - Progressive disclosure, conversation restart without data loss, and retry actions on network failure.
  - English safety guardrails prohibiting clinical self-diagnosis, tumor localization, and treatment recommendations.

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

> [!CAUTION]
> **PRE-DEPLOY BLOCKER (P0)**:  
> Prior to deploying this web product to any public or staging environment accessible beyond localhost, the license and provenance of the two demo mammogram image assets (`frontend/assets/demo-images/demo-benign-mammogram.png` and `frontend/assets/demo-images/demo-malignant-mammogram.png`) MUST be confirmed against The Cancer Imaging Archive (TCIA) / CBIS-DDSM data usage agreements:
>
> 1. **Attribution Requirements**: Verify required TCIA and CBIS-DDSM citations in public UI footers and report templates (e.g., Clark et al., *J Digit Imaging* 2013; Lee et al., *Scientific Data* 2017).
> 2. **Commercial / Academic Distribution Rights**: Ensure the cropped 224×224 grayscale patches comply with CC-BY 3.0 / TCIA Data Usage Policies for public web demonstration.
> 3. **Synthetic / Public Domain Alternative**: If TCIA attribution is restricted in certain deployment contexts, replace the demo assets with CC0 public domain mammography phantoms or synthetically generated diffusion mammograms prior to DNS cutover.

---

## 4. Explicitly Deferred Integrations

The following items are outside the scope of the web product feature freeze and are formally deferred to pre-deployment configuration and infrastructure phases:

| Item | Description | Deferral Justification |
| :--- | :--- | :--- |
| **Google OAuth Live Credentials** | Live `client_id` / `client_secret` and production OAuth redirect URIs | Requires production domain and Google Cloud Console OAuth consent screen verification. Client-side architecture is decoupled and ready. |
| **Production SMTP Email Service** | Live transactional email delivery for password resets and verification | Requires dedicated transactional email service (e.g. AWS SES, SendGrid, Postmark) and SPF/DKIM/DMARC DNS configuration. Local development outbox remains active. |
| **Production Domain, HTTPS & DNS** | Public FQDN, SSL/TLS certificates (Let's Encrypt / Cloudflare), and HTTP/2 reverse proxy | Managed at infrastructure deployment layer via Kubernetes / Docker Compose / Cloud Run. |
| **Mobile Native Applications** | React Native / Flutter / iOS / Android wrapper apps | Phase 4R is strictly a web-only feature freeze. Mobile apps will interface with the frozen REST API in subsequent phases. |
| **Model Retraining & Multimodal Learning** | Retraining ML or DL models or training an end-to-end learned multimodal network | Frozen scientific evidence baseline must remain intact and reproducible. |

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
