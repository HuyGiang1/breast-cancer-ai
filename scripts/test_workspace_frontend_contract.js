import assert from 'node:assert';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const rootDir = path.resolve(__dirname, '..');

console.log('Running test_workspace_frontend_contract.js...');

// 1. Verify auth.service.js has logoutAll
const authServicePath = path.join(rootDir, 'frontend/js/services/auth.service.js');
const authServiceCode = fs.readFileSync(authServicePath, 'utf8');
assert.ok(
  authServiceCode.includes('logoutAll:'),
  'authService must implement logoutAll method'
);
assert.ok(
  authServiceCode.includes('/auth/logout-all/'),
  'authService.logoutAll must call /auth/logout-all/'
);

// 2. Verify patient.service.js has get(id)
const patientServicePath = path.join(rootDir, 'frontend/js/services/patient.service.js');
const patientServiceCode = fs.readFileSync(patientServicePath, 'utf8');
assert.ok(
  patientServiceCode.includes('get: (id)'),
  'patientService must implement get(id) method'
);
assert.ok(
  patientServiceCode.includes('/patients/'),
  'patientService.get must request /patients/{id}/'
);

// 3. Verify guards.js has requireDoctor
const guardsPath = path.join(rootDir, 'frontend/js/core/guards.js');
const guardsCode = fs.readFileSync(guardsPath, 'utf8');
assert.ok(
  guardsCode.includes('requireDoctor'),
  'guards.js must export requireDoctor'
);

// 4. Verify register.html & register.js account type & invite code
const regHtmlPath = path.join(rootDir, 'frontend/register.html');
const regHtmlCode = fs.readFileSync(regHtmlPath, 'utf8');
assert.ok(
  regHtmlCode.includes('name="account_type"'),
  'register.html must have account_type selection'
);
assert.ok(
  regHtmlCode.includes('id="regDoctorInviteCode"'),
  'register.html must have doctor invite code input'
);

const regJsPath = path.join(rootDir, 'frontend/js/pages/register.js');
const regJsCode = fs.readFileSync(regJsPath, 'utf8');
assert.ok(
  regJsCode.includes('doctor_invite_code'),
  'register.js must handle doctor_invite_code'
);
assert.ok(
  regJsCode.includes('account_type'),
  'register.js must pass account_type in registration payload'
);

// 5. Verify workspace.js components
const wsCompPath = path.join(rootDir, 'frontend/js/components/workspace.js');
const wsCompCode = fs.readFileSync(wsCompPath, 'utf8');
assert.ok(
  wsCompCode.includes('patientModalHtml'),
  'workspace.js must export patientModalHtml'
);
assert.ok(
  wsCompCode.includes('deleteConfirmModalHtml'),
  'workspace.js must export deleteConfirmModalHtml'
);
assert.ok(
  wsCompCode.includes('preserved in system logs'),
  'deleteConfirmModalHtml must explicitly state that predictions are preserved'
);
assert.ok(
  wsCompCode.includes('accessRestrictedHtml'),
  'workspace.js must export accessRestrictedHtml'
);

// 6. Verify patients.js (Doctor Workspace)
const patientsPath = path.join(rootDir, 'frontend/js/pages/patients.js');
const patientsCode = fs.readFileSync(patientsPath, 'utf8');
assert.ok(
  patientsCode.includes("user?.role !== 'doctor'"),
  'patients.js must guard against non-doctor accounts'
);
assert.ok(
  patientsCode.includes('workspaceMetrics'),
  'patients.js must render workspace metrics strip'
);
assert.ok(
  patientsCode.includes('deleteConfirmModalHtml'),
  'patients.js must use safety delete confirmation modal'
);

// 7. Verify patient-detail.js
const patientDetailPath = path.join(rootDir, 'frontend/js/pages/patient-detail.js');
const patientDetailCode = fs.readFileSync(patientDetailPath, 'utf8');
assert.ok(
  patientDetailCode.includes('patientService.get'),
  'patient-detail.js must fetch single patient using patientService.get'
);
assert.ok(
  patientDetailCode.includes('ml-analysis.html?patient_id='),
  'patient-detail.js must link to ml-analysis with patient_id'
);
assert.ok(
  patientDetailCode.includes('dl-analysis.html?patient_id='),
  'patient-detail.js must link to dl-analysis with patient_id'
);
assert.ok(
  patientDetailCode.includes('multimodal.html?patient_id='),
  'patient-detail.js must link to multimodal with patient_id'
);
assert.ok(
  patientDetailCode.includes('timelineEntryHtml'),
  'patient-detail.js must render patient timeline entries'
);

// 8. Verify history.js (Activity)
const historyPath = path.join(rootDir, 'frontend/js/pages/history.js');
const historyCode = fs.readFileSync(historyPath, 'utf8');
assert.ok(
  historyCode.includes("isDoctor ? 'Analysis Activity' : 'My Activity'"),
  'history.js must differentiate Personal vs Doctor activity headings'
);
assert.ok(
  historyCode.includes('historyPatientSelect'),
  'history.js must include patient filter for doctor accounts'
);

// 9. Verify reports.js
const reportsPath = path.join(rootDir, 'frontend/js/pages/reports.js');
const reportsCode = fs.readFileSync(reportsPath, 'utf8');
assert.ok(
  reportsCode.includes('reportCardHtml'),
  'reports.js must render report cards'
);
assert.ok(
  reportsCode.includes('reportModalitySelect'),
  'reports.js must filter reports by modality'
);

// 10. Verify profile.js
const profilePath = path.join(rootDir, 'frontend/js/pages/profile.js');
const profileCode = fs.readFileSync(profilePath, 'utf8');
assert.ok(
  profileCode.includes('Account Type &amp; Capabilities'),
  'profile.js must show Account Type and capabilities'
);
assert.ok(
  profileCode.includes('logoutAllDevicesBtn'),
  'profile.js must include Sign out all devices trigger'
);
assert.ok(
  profileCode.includes('authService.logoutAll()'),
  'profile.js must call authService.logoutAll()'
);

// 11. Verify shell.js role awareness
const shellPath = path.join(rootDir, 'frontend/js/components/shell.js');
const shellCode = fs.readFileSync(shellPath, 'utf8');
assert.ok(
  shellCode.includes("isDoctor ?"),
  'shell.js must check isDoctor for workspace navigation link'
);

console.log('test_workspace_frontend_contract.js: ALL 11 CHECKS PASSED');
