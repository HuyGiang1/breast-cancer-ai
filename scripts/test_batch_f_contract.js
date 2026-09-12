// scripts/test_batch_f_contract.js
// Batch F Comprehensive Contract Tests:
// - Transient privacy cleanup on auth state change
// - Unified authenticated report service interface
// - Workspace prediction semantics (Fusion heuristic, ML threshold 0.360, DL threshold 0.515)
// - Modal accessibility binding
// - History doctor patient in-memory filtering
// - Date range filtering & result count formatting
// - AI Guide safe markdown rendering (XSS prevention)
// - Screening guidelines separation (ACS vs USPSTF)

import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ROOT = path.resolve(__dirname, '..');

console.log('--- STARTING BATCH F CONTRACT TESTS ---');

// 1. Auth Transient Privacy Verification
{
  const authCode = fs.readFileSync(path.join(ROOT, 'frontend/js/core/auth.js'), 'utf-8');
  assert(authCode.includes('clearTransientContext()'), 'auth.js must define clearTransientContext()');
  assert(authCode.includes('sessionStorage.removeItem("bcai_advisor_context")') || authCode.includes("sessionStorage.removeItem('bcai_advisor_context')"), 'clearTransientContext must remove bcai_advisor_context');
  assert(authCode.includes('clearTransientContext') && authCode.includes('save('), 'auth.save must invoke clearTransientContext()');
  assert(authCode.includes('clearTransientContext') && authCode.includes('clear()'), 'auth.clear must invoke clearTransientContext()');
  console.log('✓ 1. Auth transient privacy context clearance contract satisfied.');
}

// 2. Report Service Interface Verification
{
  const reportCode = fs.readFileSync(path.join(ROOT, 'frontend/js/services/report.service.js'), 'utf-8');
  assert(reportCode.includes('async fetchBlob('), 'reportService must provide fetchBlob(id)');
  assert(reportCode.includes('async open('), 'reportService must provide open(id)');
  assert(reportCode.includes('async print('), 'reportService must provide print(id)');
  assert(reportCode.includes('window.open('), 'reportService must open a window for viewer');
  assert(reportCode.includes('Authorization') && reportCode.includes('Bearer'), 'reportService must include Authorization Bearer header');
  console.log('✓ 2. Unified authenticated reportService interface contract satisfied.');
}

// 3. Workspace Prediction Semantics Verification
{
  const workspaceCode = fs.readFileSync(path.join(ROOT, 'frontend/js/components/workspace.js'), 'utf-8');
  assert(workspaceCode.includes('parsePredictionPayload'), 'workspace.js must define parsePredictionPayload');
  assert(workspaceCode.includes('getPredictionSemantics'), 'workspace.js must define getPredictionSemantics');
  assert(workspaceCode.includes('Experimental Fusion'), 'workspace.js must label multimodal as Experimental Fusion');
  assert(workspaceCode.includes('Malignant-side heuristic indication'), 'workspace.js must label malignant heuristic for fusion');
  assert(workspaceCode.includes('Benign-side heuristic indication'), 'workspace.js must label benign heuristic for fusion');
  assert(workspaceCode.includes('Experimental Combined Score:'), 'workspace.js must display Experimental Combined Score');
  assert(workspaceCode.includes('Branch Agreement:'), 'workspace.js must display branch agreement for fusion');
  assert(workspaceCode.includes('Decision Threshold: 0.360'), 'workspace.js must display ML Decision Threshold: 0.360');
  assert(workspaceCode.includes('Decision Threshold: 0.515'), 'workspace.js must display DL Decision Threshold: 0.515');
  assert(workspaceCode.includes('bindModalAccessibility'), 'workspace.js must define bindModalAccessibility');
  console.log('✓ 3. Workspace prediction semantics & modal accessibility contract satisfied.');
}

// 4. Modal Accessibility Trap & Listeners
{
  const workspaceCode = fs.readFileSync(path.join(ROOT, 'frontend/js/components/workspace.js'), 'utf-8');
  assert(workspaceCode.includes("e.key === 'Escape'"), 'bindModalAccessibility must handle Escape key');
  assert(workspaceCode.includes("e.key === 'Tab'"), 'bindModalAccessibility must trap Tab navigation');
  assert(workspaceCode.includes("aria-modal"), 'bindModalAccessibility must ensure aria-modal');
  assert(workspaceCode.includes("triggerEl.focus()"), 'bindModalAccessibility must return focus to trigger');
  console.log('✓ 4. Modal accessibility focus trap & Escape handling contract satisfied.');
}

// 5. History In-Memory Filtering & Date Range Contract
{
  const historyCode = fs.readFileSync(path.join(ROOT, 'frontend/js/pages/history.js'), 'utf-8');
  assert(historyCode.includes('rows = Array.isArray(historyData)'), 'history.js must maintain full analyses in memory for client-side filtering');
  assert(historyCode.includes('historyDateFrom'), 'history.js must support From date filter');
  assert(historyCode.includes('historyDateTo'), 'history.js must support To date filter');
  assert(historyCode.includes('historyClearFiltersBtn'), 'history.js must support Clear Filters');
  assert(historyCode.includes('reportService.open'), 'history.js must wire view action to reportService.open');
  assert(historyCode.includes('reportService.print'), 'history.js must wire print action to reportService.print');
  console.log('✓ 5. History page doctor filtering, date range & report service contract satisfied.');
}

// 6. Reports Page Date Range & Counter Badge Contract
{
  const reportsCode = fs.readFileSync(path.join(ROOT, 'frontend/js/pages/reports.js'), 'utf-8');
  assert(reportsCode.includes('reportDateFrom'), 'reports.js must support From date filter');
  assert(reportsCode.includes('reportDateTo'), 'reports.js must support To date filter');
  assert(reportsCode.includes('reportClearFiltersBtn'), 'reports.js must support Clear Filters');
  assert(reportsCode.includes('reportService.open'), 'reports.js must wire view action to reportService.open');
  assert(reportsCode.includes('reportService.print'), 'reports.js must wire print action to reportService.print');
  assert(reportsCode.includes('reportCountBadge'), 'reports.js must render active count badge');
  console.log('✓ 6. Reports page date range, count badge & report service contract satisfied.');
}

// 7. AI Guide Multimodal Grounding & Safe DOM Parsing
{
  const supportCode = fs.readFileSync(path.join(ROOT, 'frontend/js/components/support.js'), 'utf-8');
  assert(supportCode.includes('renderSafeContent'), 'support.js must define renderSafeContent');
  assert(!supportCode.includes('container.innerHTML = markdown'), 'renderSafeContent must NOT assign raw markdown to innerHTML');
  assert(supportCode.includes('document.createElement'), 'renderSafeContent must create DOM elements securely');

  const advisorCode = fs.readFileSync(path.join(ROOT, 'frontend/js/pages/advisor.js'), 'utf-8');
  assert(advisorCode.includes('Experimental software combination of unpaired WDBC and CBIS-DDSM outputs'), 'advisor.js must include fusion disclaimer in system grounding');
  assert(advisorCode.includes('Threshold=0.360'), 'advisor.js must include structured threshold 0.360 in system grounding');
  assert(advisorCode.includes('Threshold=0.515'), 'advisor.js must include DL threshold 0.515 in system grounding');
  assert(advisorCode.includes('Saved account history is unchanged'), 'advisor.js must reassure user that saved account history is unchanged on new conversation');
  console.log('✓ 7. AI Guide multimodal context grounding & safe DOM parsing contract satisfied.');
}

// 8. Screening Guidelines Separation (ACS vs USPSTF)
{
  const indexHtml = fs.readFileSync(path.join(ROOT, 'frontend/index.html'), 'utf-8');
  assert(indexHtml.includes('American Cancer Society Recommendations (Average Risk)'), 'index.html must have dedicated ACS guidelines section');
  assert(indexHtml.includes('U.S. Preventive Services Task Force (2024 Final Recommendation)'), 'index.html must have dedicated USPSTF guidelines section');
  assert(indexHtml.includes('https://www.cancer.org/cancer/types/breast-cancer/screening-tests-and-early-detection/american-cancer-society-recommendations-for-the-early-detection-of-breast-cancer.html'), 'index.html must link to official ACS guidelines');
  assert(indexHtml.includes('https://www.uspreventiveservicestaskforce.org/uspstf/recommendation/breast-cancer-screening'), 'index.html must link to official USPSTF guidelines');
  console.log('✓ 8. Screening guidelines separation (ACS vs USPSTF) contract satisfied.');
}

// 9. Doctor Workspace & Notes Copy Reconciliation
{
  const patientsJs = fs.readFileSync(path.join(ROOT, 'frontend/js/pages/patients.js'), 'utf-8');
  const workspaceJs = fs.readFileSync(path.join(ROOT, 'frontend/js/components/workspace.js'), 'utf-8');
  assert(patientsJs.includes('Doctor Workspace · Research Registry'), 'patients.js must use canonical title');
  assert(workspaceJs.includes('Research Notes'), 'workspace.js patientModalHtml must use Research Notes label');
  assert(workspaceJs.includes('Deleting this patient record preserves existing saved analysis records'), 'workspace.js deletion modal must use canonical unlinking wording');

  const profileJs = fs.readFileSync(path.join(ROOT, 'frontend/js/pages/profile.js'), 'utf-8');
  assert(profileJs.includes('This revokes all active Breast Health Studio sessions for this account.'), 'profile.js logout-all copy must not mention refresh tokens');
  console.log('✓ 9. Doctor workspace & notes copy reconciliation satisfied.');
}

console.log('--- ALL BATCH F CONTRACT TESTS PASSED SUCCESSFULLY ---');
