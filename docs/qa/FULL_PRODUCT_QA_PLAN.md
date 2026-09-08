# Full Product QA & Pre-Deployment Stability Plan

**Branch**: `feat/frontend-redesign-v3`  
**Target Environment**: Local Docker Stack (`http://localhost`)  
**Scope**: Pre-deployment quality audit, stability verification, accessibility smoke, performance audit, and defect remediation.

---

## 1. Inventory of User-Facing Routes

The application features 21 canonical user-facing HTML pages:

| Category | Route / Path | Primary Role | Core Purpose |
| :--- | :--- | :--- | :--- |
| **Public** | `/index.html` (or `/`) | Public | Research studio landing page, telemetry overview, scientific principles, methodology. |
| **Auth** | `/login.html` | Public | V3 Sign In, credential authentication, deferred Google entry. |
| **Auth** | `/register.html` | Public | Account creation (role forced to `user`), duplicate email resolution card. |
| **Auth** | `/forgot-password.html` | Public | V3 password recovery request (enumeration-safe generic feedback). |
| **Auth** | `/reset-password.html` | Public | V3 password reset via URL token, security address-bar cleanup. |
| **Workspace** | `/pages/dashboard.html` | User / Doctor | Primary workspace hub, quick access to analysis, recent activity, system status. |
| **Workspace** | `/pages/profile.html` | User / Doctor | Account settings, password change, connected OAuth accounts management. |
| **Analyze** | `/pages/ml-analysis.html` | User / Doctor | Study A 30-feature WDBC numerical FNA inference ($\tau=0.36$). |
| **Analyze** | `/pages/dl-analysis.html` | User / Doctor | Study B CBIS-DDSM mammography inference ($\tau=0.515$), Platt display, Grad-CAM. |
| **Analyze** | `/pages/multimodal.html` | User / Doctor | Experimental 40/60 dual-branch fusion heuristic (demo only). |
| **Research** | `/pages/research.html` | Public / All | High-level research methodology, Study A vs Study B decoupling. |
| **Research** | `/pages/model-comparison.html` | Public / All | Candidate architecture comparisons, ablation studies, parameter counts. |
| **Research** | `/pages/datasets.html` | Public / All | Dataset cohorts (WDBC 569, CBIS-DDSM 2,559 images / 5,118 entries, inferred groups). |
| **Research** | `/pages/explainability.html` | Public / All | Feature attribution: WDBC Tree SHAP & CBIS-DDSM Grad-CAM coarse attention. |
| **Research** | `/pages/calibration.html` | Public / All | Reliability curves, Brier scores, Platt scaling for post-hoc display. |
| **Research** | `/pages/model-status.html` | Public / All | Live model integrity, checksum status, runtime health, threshold contract. |
| **Workspace Data**| `/pages/history.html` | User / Doctor | Historical predictions audit log, filtering, modality labels, result view. |
| **Workspace Data**| `/pages/reports.html` | User / Doctor | Generated clinical/educational research reports with probability breakdowns. |
| **Doctor Only** | `/pages/patients.html` | Doctor | Clinical registry: patient directory, demographic search, new patient modal. |
| **Doctor Only** | `/pages/patient-detail.html`| Doctor | Longitudinal patient profile, linked predictions, medical notes. |
| **AI Guide** | `/pages/advisor.html` | User / Doctor | Clinical & educational AI advisory chat, rule-based / offline fallback. |

---

## 2. Test Personas & Test Data Isolation

1. **Anonymous / Logged-Out**:
   - Must freely access `/index.html`, Auth pages, and Research pages.
   - Manually navigating to protected workspace routes (`/pages/dashboard.html`, `/pages/ml-analysis.html`, `/pages/patients.html`, etc.) must cleanly redirect to `/login.html?v=auth-v3`.
2. **Standard User (`role: user`)**:
   - Disposable account: `qa-ui-<timestamp>@example.invalid`.
   - Access to Dashboard, Analysis, History, Profile, Advisor.
   - Strictly forbidden from viewing or manipulating Doctor-only patient pages (`/pages/patients.html`, `/pages/patient-detail.html`).
3. **Doctor User (`role: doctor`)**:
   - Controlled test doctor account created via secure backend fixture.
   - Access to full patient management registry and patient-linked records.
   - Verified cross-doctor ownership isolation.

---

## 3. Detailed QA Test Matrix

### A. Broken Links & Asset Integrity
- Automated crawl of all 21 HTML pages.
- Every `<a href>`, `<link rel="stylesheet">`, `<script src>`, `<img src>`, and `<video poster>` must resolve locally with HTTP 200 or an intentional auth guard redirect. Zero 404s allowed.

### B. Authentication & Credential Safety
- Normal registration, duplicate registration with resolution UX card, validation errors (password length, mismatch).
- Login correct password, wrong password, logout session invalidation.
- Forgot password enumeration protection: identical generic message regardless of email existence.
- Reset password: automatic token capture, `history.replaceState` URL cleanup, password update, token expiration/invalidation.
- Google Sign-In: graceful unconfigured notification (no mock logins).

### C. Session Guards & Back-Button Cache
- Attempt accessing protected pages without session -> Clean redirect to login.
- Logout session clearance -> Back button navigation must not render authenticated patient data or permit unauthorized API execution.

### D. Model Runtime & Inference Workflows
- **ML Analysis**: 30-feature WDBC numerical inputs, preset loading, raw probability calculation, decision threshold $\tau=0.36$, double-click submission prevention, persistence.
- **DL Analysis**: Mammogram image upload, size/type validation, raw probability calculation, decision threshold $\tau=0.515$, Platt calibration separate display (not titled "Reliability Score"), Grad-CAM generation, disclaimer.
- **Multimodal**: Dual-branch heuristic weighting, conflict resolution, failure resilience.

### E. Responsive Viewports & Accessibility
- Tested at 1440x900 (desktop wide), 1280x800 (desktop standard), 768x1024 (tablet portrait), 390x844 (mobile standard).
- Check for horizontal overflow, mobile navigation sheet, tap targets >= 44x44px, visible keyboard focus indicators, landmark hierarchy.

### F. Console Errors & Network Failures
- 0 unexplained `console.error` logs.
- 0 unhandled Promise rejections.
- 0 unexpected 4xx / 5xx HTTP responses.

### G. Restart Resilience & Privacy
- Container restart (`docker restart breast_cancer_api && docker restart breast_cancer_web`) must preserve database entries and runtime model readiness.
- Passwords, hashes, and session tokens must never appear in frontend logs or HTML attributes.
