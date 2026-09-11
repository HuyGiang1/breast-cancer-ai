# Phase 4R — Batch E: Doctor Workspace, Personal Accounts, Patient Registry, Activity & Reports QA Record

## 1. Executive Summary

- **Batch**: Phase 4R — Batch E
- **Branch**: `feat/product-experience-v4`
- **Scope**: Web-only. Account Types separation, Server-Enforced Doctor Security & Invite Codes, Doctor Workspace & Patient Registry, Single-Patient Detail Endpoint & Longitudinal Timelines, Role-Differentiated Activity ("My Activity" vs "Analysis Activity"), Printable Research Reports, Profile Capabilities Breakdown & "Sign out all devices".
- **Result**: **PASS** (100% automated test pass rate, zero regression across Batches B, C, and D).

---

## 2. Architecture & Security Invariants

### 2.1 Server-Enforced Registration & Invite Code Verification
- **Configuration**:
  - `DOCTOR_REGISTRATION_MODE=invite` (default for production-like environments).
  - `DOCTOR_INVITE_CODE=BHS-DOC-2026-DEV` (configurable secret).
- **Constant-Time Verification**:
  - Validated using `hmac.compare_digest(request.doctor_invite_code.strip(), invite_code.strip())` to protect against timing attacks.
  - Client-submitted `role` fields are explicitly ignored. The server dictates account role exclusively based on verified account type and authorization.
- **Client Flow**:
  - `frontend/register.html` provides radio card selection between **Personal Analysis** and **Doctor Workspace**.
  - Selecting **Doctor Workspace** dynamically reveals the **Doctor Workspace Invite Code** input with explanatory notice.
  - Personal accounts default to `role = "user"`, while successful doctor registrations receive `role = "doctor"`.

### 2.2 Patient Ownership & Single-Patient Retrieval API
- **Endpoint Added**: `GET /patients/{patient_id}/` in `backend/app/api/endpoints.py`.
- **Authorization**:
  - Strictly requires `role == "doctor"`.
  - Enforces database ownership: `SELECT * FROM patients WHERE id = :id AND user_id = :current_user_id`.
  - Returns `404 Not Found` if the patient belongs to another doctor or does not exist (cross-doctor isolation).
  - Non-doctor accounts receiving `403 Forbidden`.

### 2.3 Safe Patient Deletion Semantics
- In the database, `predictions.patient_id` has `FOREIGN KEY(patient_id) REFERENCES patients(id) ON DELETE SET NULL`.
- Deleting a patient deletes the demographic registry entry only.
- All historical model telemetry runs, prediction confidence scores, and generated reports remain permanently preserved in historical logs.
- The UI modal explicitly states this to clinicians before deletion:
  > *"Deleting this patient record removes the demographic registry entry. All historical prediction records, model telemetry runs, and generated reports are preserved in system logs, but will no longer be associated with this patient."*

### 2.4 Browser-Driven Printable Reports
- In `backend/app/api/endpoints.py`, `_build_prediction_report_html` includes a browser-native print action bar:
  - `<button onclick="window.print()">Print / Save PDF</button>`
  - Print-specific media query: `@media print { .report-action-bar { display: none !important; } ... }`
- Avoids fragile server-side headless browser rendering dependencies while enabling one-click Print / Save as PDF across all browsers.

### 2.5 Multi-Device Session Security
- Added `POST /auth/logout-all/` calling `authService.logoutAll()`.
- Invalidates all sessions in the `sessions` table for the user across every device.
- Profile UI provides a confirmation modal with clear explanation before executing global revocation.

---

## 3. Automated Test Suite Results

### 3.1 Backend Workspace & Security Tests (`tests/test_batch_e_workspace_security.py`)
- **11 / 11 Passed**:
  1. `test_personal_registration_always_assigns_user_role`: PASS
  2. `test_client_role_injection_ignored`: PASS
  3. `test_doctor_registration_requires_invite_code`: PASS
  4. `test_doctor_registration_fails_with_invalid_code`: PASS
  5. `test_doctor_registration_succeeds_with_valid_code`: PASS
  6. `test_normal_user_cannot_access_patient_apis`: PASS
  7. `test_doctor_single_patient_endpoint`: PASS
  8. `test_doctor_cannot_access_other_doctor_patient`: PASS
  9. `test_safe_patient_deletion_preserves_prediction`: PASS
  10. `test_report_endpoint_security`: PASS
  11. `test_logout_all_sessions_invalidates_active_token`: PASS

### 3.2 Frontend Contract Tests (`scripts/test_workspace_frontend_contract.js`)
- **11 / 11 Passed**:
  1. `authService.logoutAll` implementation and endpoint routing: PASS
  2. `patientService.get(id)` implementation: PASS
  3. `guards.js` `requireDoctor` export: PASS
  4. `register.html` & `register.js` account type & invite code: PASS
  5. `workspace.js` components (`patientModalHtml`, `deleteConfirmModalHtml`, `accessRestrictedHtml`): PASS
  6. `patients.js` role guard and summary strip: PASS
  7. `patient-detail.js` single-patient fetching and 3-modality quick launch links: PASS
  8. `history.js` Personal vs Doctor activity headings and patient selector: PASS
  9. `reports.js` modality filter and report cards: PASS
  10. `profile.js` capabilities display and Logout All modal: PASS
  11. `shell.js` role-aware navigation: PASS

### 3.3 Static Dependency Contract (`scripts/verify_frontend_v2.py`)
- **PASS**: All 16 canonical pages, modules, stylesheets, and navigation references are valid.

### 3.4 Broken Link & Asset Crawler (`scripts/qa_broken_link_crawler.js`)
- **0 defects**: 117 internal links, scripts, stylesheets, and media references verified across 21 canonical documents.

### 3.5 Full Regression Verification
- **Batch B E2E Suite (`scripts/qa_batch_b_e2e.js`)**: 100% PASS
- **Batch C E2E Suite (`scripts/qa_batch_c_e2e.js`)**: 100% PASS
- **Batch D E2E Suite (`scripts/qa_batch_d_e2e.js`)**: 100% PASS

---

## 4. Visual QA Verification & Screenshot Manifest

All 17 screenshots captured across desktop (1440×900) and mobile (390×844) viewports:

| # | Filename | Viewport | Description |
|---|---|---|---|
| 1 | `register-personal-1440.png` | 1440px | Registration page with default Personal Analysis card selected. |
| 2 | `register-doctor-selected-1440.png` | 1440px | Registration page with Doctor Workspace card selected and revealable invite code field. |
| 3 | `patients-doctor-overview-1440.png` | 1440px | Doctor Workspace showing summary metrics strip, toolbar, and patient list. |
| 4 | `patients-add-modal-1440.png` | 1440px | Add Patient accessible modal dialog with demographics and notes inputs. |
| 5 | `patients-populated-registry-1440.png` | 1440px | Populated patient registry with cards, modality counters, and quick actions. |
| 6 | `patients-delete-modal-1440.png` | 1440px | Safety-explicit patient deletion modal with prediction unlinking disclaimer. |
| 7 | `patient-detail-timeline-1440.png` | 1440px | Patient detail view with 3 quick launch buttons, clinical notes, and chronological timeline. |
| 8 | `patients-access-denied-personal-1440.png` | 1440px | Personal account attempting to access `/pages/patients.html` showing Access Restricted notice. |
| 9 | `patient-detail-access-denied-1440.png` | 1440px | Personal account attempting to access `/pages/patient-detail.html` showing Access Restricted notice. |
| 10 | `history-personal-1440.png` | 1440px | Personal user viewing "My Activity" without patient dropdown. |
| 11 | `history-doctor-patient-filter-1440.png` | 1440px | Doctor viewing "Analysis Activity" with patient selector filter dropdown. |
| 12 | `reports-workspace-1440.png` | 1440px | Reports page with modality filter, View Full Report, and Print / Save PDF triggers. |
| 13 | `profile-doctor-logout-all-1440.png` | 1440px | Profile page showing Doctor capabilities breakdown and "Sign out all devices" modal. |
| 14 | `register-doctor-mobile-390.png` | 390px | Registration with Doctor selection on 390px mobile viewport. |
| 15 | `patients-mobile-390.png` | 390px | Doctor Workspace on mobile viewport with responsive metrics strip and patient cards. |
| 16 | `patient-detail-mobile-390.png` | 390px | Patient detail view on mobile viewport showing header, launch buttons, and timeline. |
| 17 | `history-mobile-390.png` | 390px | Activity feed on mobile viewport. |

---

## 5. Parity Reconciliation Summary

| Feature Area | Legacy Reference | Batch E Implementation | Status |
|---|---|---|---|
| Account Types | Single generic form; client-side role toggle | Server-gated Doctor invite code; Personal vs Doctor cards | **BETTER** |
| Patient Registry | Plain unstyled table, basic prompt() delete | Summary strip, search/sort, rich cards, safety delete modal | **BETTER** |
| Single Patient API | In-memory array filtering from `list()` | Dedicated `GET /patients/{id}/` with role & ownership enforcement | **RESTORED & SECURED** |
| Patient Detail | Stale V2 links (`ml-analysis.html`, `dl-analysis.html`) | 3 canonical quick launch buttons (`ml`, `mammography`, `fusion`), timeline, notes | **BETTER** |
| Activity Logs | Single plain list | "My Activity" (Personal) vs "Analysis Activity" (Doctor + patient filter) | **BETTER** |
| Reports & PDF Export | "PDF export unavailable" placeholder | Report cards with direct View and browser-native Print / Save PDF | **RESTORED** |
| Device Logout | Missing / single session only | Global session invalidation (`POST /auth/logout-all/`) with confirmation | **RESTORED** |
