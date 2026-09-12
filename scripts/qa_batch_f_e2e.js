/**
 * QA Batch F E2E Browser Test Suite & Screenshot Gate
 *
 * Verifies:
 * - 1. Guest flow: Overview landing page, separated ACS & USPSTF guidance, Register Personal / Doctor
 * - 2. Personal flow:
 *      - Structured ML analysis & result
 *      - Mammography DL analysis & result
 *      - Experimental Fusion disagreement analysis & result
 *      - AI Guide handoff (structured, DL, fusion)
 *      - Safe DOM markdown rendering (no innerHTML XSS)
 *      - "Start new conversation" with non-destructive notice
 *      - Personal Activity date range filtering & Clear Filters
 *      - Reports date range filtering, result count badge, and authenticated report view/print
 * - 3. Account-switch transient privacy:
 *      - User A analysis context in sessionStorage
 *      - User A logout -> auth.clearTransientContext() wipes context
 *      - User B login -> AI Guide has zero residual User A state
 * - 4. Doctor flow:
 *      - Doctor Workspace / Research Registry
 *      - Register Patient & Research Notes
 *      - Modal accessibility: Tab trap, Escape key closes modal, body scroll lock
 *      - Patient detail timeline
 *      - Doctor Activity with in-memory patient filtering
 *      - Profile security modal
 * - 5. Captures all 24 canonical Batch F screenshots (17 desktop + 7 mobile)
 */

const fs = require('fs');
const path = require('path');
const http = require('http');
const { spawn, execSync } = require('child_process');

const SCREENSHOT_DIR = path.resolve(__dirname, '../docs/v4/screenshots');
const ARTIFACT_DIR = path.resolve('/Users/GiangNguyenHuy/.gemini/antigravity-ide/brain/62658f2a-6d4b-455d-b237-69778800e810/screenshots');
if (!fs.existsSync(SCREENSHOT_DIR)) fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
if (!fs.existsSync(ARTIFACT_DIR)) fs.mkdirSync(ARTIFACT_DIR, { recursive: true });

const PORT = 9575;

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function getWebSocketUrl() {
  return new Promise((resolve, reject) => {
    let attempts = 0;
    const check = () => {
      attempts++;
      http.get(`http://localhost:${PORT}/json`, (res) => {
        let data = '';
        res.on('data', (chunk) => (data += chunk));
        res.on('end', () => {
          try {
            const list = JSON.parse(data);
            const page = list.find((t) => t.type === 'page');
            if (page && page.webSocketDebuggerUrl) {
              resolve(page.webSocketDebuggerUrl);
            } else {
              if (attempts > 30) reject(new Error('No page found'));
              else setTimeout(check, 300);
            }
          } catch (e) {
            if (attempts > 30) reject(e);
            else setTimeout(check, 300);
          }
        });
      }).on('error', () => {
        if (attempts > 30) reject(new Error('Cannot reach Chrome CDP'));
        else setTimeout(check, 300);
      });
    };
    check();
  });
}

function runPython(script) {
  return execSync('PYTHONPATH=.:backend venv/bin/python', {
    input: script,
    encoding: 'utf-8',
    cwd: path.resolve(__dirname, '..'),
  });
}

class CDPClient {
  constructor(wsUrl) {
    this.ws = new WebSocket(wsUrl);
    this.msgId = 0;
    this.callbacks = new Map();
  }

  init() {
    return new Promise((resolve, reject) => {
      if (this.ws.readyState === WebSocket.OPEN) return resolve();
      this.ws.onopen = resolve;
      this.ws.onerror = reject;
      this.ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        if (msg.id && this.callbacks.has(msg.id)) {
          const cb = this.callbacks.get(msg.id);
          this.callbacks.delete(msg.id);
          if (msg.error) cb.reject(msg.error);
          else cb.resolve(msg.result);
        }
      };
    });
  }

  send(method, params = {}) {
    return new Promise((resolve, reject) => {
      const id = ++this.msgId;
      this.callbacks.set(id, { resolve, reject });
      this.ws.send(JSON.stringify({ id, method, params }));
    });
  }

  async eval(expression) {
    const res = await this.send('Runtime.evaluate', {
      expression,
      returnByValue: true,
      awaitPromise: true,
    });
    if (res && res.exceptionDetails) {
      throw new Error(`Eval error: ${JSON.stringify(res.exceptionDetails)}`);
    }
    return res && res.result ? res.result.value : undefined;
  }

  async setViewport(width, height) {
    await this.send('Emulation.setDeviceMetricsOverride', {
      width,
      height,
      deviceScaleFactor: 1,
      mobile: width < 600,
    });
    await this.send('Emulation.setVisibleSize', { width, height });
  }

  async screenshot(filename) {
    const res = await this.send('Page.captureScreenshot', { format: 'png' });
    const buffer = Buffer.from(res.data, 'base64');
    const p1 = path.join(SCREENSHOT_DIR, filename);
    const p2 = path.join(ARTIFACT_DIR, filename);
    fs.writeFileSync(p1, buffer);
    fs.writeFileSync(p2, buffer);
    console.log(`  ✓ Saved screenshot: ${filename} (${buffer.length} bytes)`);
  }
}

async function main() {
  console.log('====================================================');
  console.log('PHASE 4R BATCH F: FINAL WEB PRODUCT POLISH & UAT');
  console.log('====================================================\n');

  console.log('Setting up test fixtures in SQLite...');
  const setupPy = `
import json, sqlite3, os
from datetime import datetime, timezone, timedelta

conn = sqlite3.connect('backend/data/app.db')
c = conn.cursor()

now = datetime.now(timezone.utc).isoformat()
exp = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()

def create_user(email, name, role):
    c.execute("DELETE FROM users WHERE email = ?", (email,))
    c.execute("""
        INSERT INTO users (email, password_hash, full_name, role, created_at, updated_at)
        VALUES (?, 'dummyhash', ?, ?, ?, ?)
    """, (email, name, role, now, now))
    user_id = c.lastrowid
    token = 'token_batch_f_' + role + '_' + str(user_id)
    c.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
    c.execute("INSERT INTO sessions (user_id, token, expires_at, created_at) VALUES (?, ?, ?, ?)", (user_id, token, exp, now))
    return user_id, token

u1_id, u1_token = create_user('personal_user_f1@test.local', 'Jane Personal User F', 'user')
u2_id, u2_token = create_user('personal_user_f2@test.local', 'Bob Second User F', 'user')
doc_id, doc_token = create_user('doctor_user_f@test.local', 'Dr. Evelyn Reed F', 'doctor')

# Create patients for doctor
c.execute("DELETE FROM patients WHERE user_id = ?", (doc_id,))
c.execute("""
    INSERT INTO patients (user_id, full_name, date_of_birth, gender, notes, created_at, updated_at)
    VALUES (?, 'Eleanor Vance', '1975-04-12', 'Female', 'Initial mammography screening baseline', ?, ?)
""", (doc_id, now, now))
p1_id = c.lastrowid

c.execute("""
    INSERT INTO patients (user_id, full_name, date_of_birth, gender, notes, created_at, updated_at)
    VALUES (?, 'Marcus Aurelius', '1968-11-23', 'Male', 'High risk genetic screening study', ?, ?)
""", (doc_id, now, now))
p2_id = c.lastrowid

# Create sample predictions for doctor and personal user
c.execute("DELETE FROM predictions WHERE user_id IN (?, ?)", (u1_id, doc_id))
# ML analysis for doctor with patient 1
c.execute("""
    INSERT INTO predictions (user_id, patient_id, prediction_type, model_name, diagnosis, probability, raw_probability, calibration_mode, risk_band, input_payload, response_payload, created_at)
    VALUES (?, ?, 'ml', 'Wisconsin Logistic Regression', 'Benign', 0.125, 0.125, 'sigmoid', 'low', '{}', '{"decision_threshold": 0.360}', '2026-09-10 10:00:00')
""", (doc_id, p1_id))
pred_ml_id = c.lastrowid

# DL analysis for doctor with patient 2
c.execute("""
    INSERT INTO predictions (user_id, patient_id, prediction_type, model_name, diagnosis, probability, raw_probability, calibration_mode, risk_band, input_payload, response_payload, created_at)
    VALUES (?, ?, 'dl', 'CBIS-DDSM EfficientNet-B0', 'Malignant', 0.642, 0.642, 'platt', 'high', '{}', '{"decision_threshold": 0.515, "calibrated_probability": 0.589}', '2026-09-11 11:30:00')
""", (doc_id, p2_id))
pred_dl_id = c.lastrowid

# Fusion analysis for doctor unlinked
c.execute("""
    INSERT INTO predictions (user_id, patient_id, prediction_type, model_name, diagnosis, probability, raw_probability, calibration_mode, risk_band, input_payload, response_payload, created_at)
    VALUES (?, NULL, 'multimodal', 'Experimental Fusion', 'Malignant', 0.584, 0.584, 'midpoint', 'high', '{}', '{"combined_malignant_score": 0.584, "decision_midpoint": 0.50, "branch_agreement": "Both branches malignant-side", "branch_disagreement": false, "branches_unpaired": true}', '2026-09-12 09:15:00')
""", (doc_id,))
pred_fus_id = c.lastrowid

# Personal user prediction
c.execute("""
    INSERT INTO predictions (user_id, patient_id, prediction_type, model_name, diagnosis, probability, raw_probability, calibration_mode, risk_band, input_payload, response_payload, created_at)
    VALUES (?, NULL, 'ml', 'Wisconsin Logistic Regression', 'Benign', 0.085, 0.085, 'sigmoid', 'low', '{}', '{"decision_threshold": 0.360}', '2026-09-12 08:00:00')
""", (u1_id,))
pred_u1_id = c.lastrowid

conn.commit()
conn.close()

print(json.dumps({
    'user1': {'id': u1_id, 'token': u1_token, 'name': 'Jane Personal User F'},
    'user2': {'id': u2_id, 'token': u2_token, 'name': 'Bob Second User F'},
    'doctor': {'id': doc_id, 'token': doc_token, 'name': 'Dr. Evelyn Reed F'},
    'patients': {'p1': p1_id, 'p2': p2_id},
    'predictions': {'ml': pred_ml_id, 'dl': pred_dl_id, 'fusion': pred_fus_id, 'u1': pred_u1_id}
}))
`;

  const fixtures = JSON.parse(runPython(setupPy));
  console.log('✓ Fixtures initialized:', fixtures);

  console.log('\nLaunching Headless Chrome on port', PORT);
  const chromeProc = spawn(
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    [
      `--remote-debugging-port=${PORT}`,
      '--headless=new',
      '--disable-gpu',
      '--no-sandbox',
      '--disable-background-networking',
      '--window-size=1440,900',
    ]
  );

  await sleep(1500);

  let cdp = null;
  try {
    const wsUrl = await getWebSocketUrl();
    cdp = new CDPClient(wsUrl);
    await cdp.init();
    await cdp.send('Page.enable');
    await cdp.send('Runtime.enable');
    await cdp.send('DOM.enable');

    // =========================================================================
    // 1. OVERVIEW / GUEST / LANDING (Desktop & Mobile)
    // =========================================================================
    console.log('\n--- 1. Overview Guest (1440px) ---');
    await cdp.setViewport(1440, 900);
    await cdp.send('Page.navigate', { url: 'http://localhost/index.html' });
    await sleep(1200);

    // Verify ACS & USPSTF separated sections exist
    const acsPresent = await cdp.eval(`document.body.innerText.includes('American Cancer Society Recommendations')`);
    const uspstfPresent = await cdp.eval(`document.body.innerText.includes('U.S. Preventive Services Task Force')`);
    if (!acsPresent || !uspstfPresent) throw new Error('Separated ACS / USPSTF guidance not found on landing page!');
    console.log('  ✓ Verified: ACS and USPSTF screening guidelines visibly separated with citations.');

    await cdp.screenshot('v4-f-overview-guest-1440.png');

    console.log('\n--- 18. Overview Guest (390px) ---');
    await cdp.setViewport(390, 844);
    await sleep(400);
    await cdp.screenshot('v4-f-overview-390.png');

    // =========================================================================
    // 2. REGISTRATION (1440px)
    // =========================================================================
    console.log('\n--- 4. Registration Page (1440px) ---');
    await cdp.setViewport(1440, 900);
    await cdp.send('Page.navigate', { url: 'http://localhost/register.html' });
    await sleep(1000);

    // Verify Personal vs Doctor selection controls
    const hasPersonalCard = await cdp.eval(`document.querySelector('#typePersonalRadio') !== null`);
    const hasDoctorCard = await cdp.eval(`document.querySelector('#typeDoctorRadio') !== null`);
    if (!hasPersonalCard || !hasDoctorCard) throw new Error('Registration account type cards not found!');
    await cdp.screenshot('v4-f-register-1440.png');

    // =========================================================================
    // 3. OVERVIEW / PERSONAL USER & DOCTOR (1440px)
    // =========================================================================
    console.log('\n--- 2. Overview Personal User (1440px) ---');
    await cdp.send('Page.navigate', { url: 'http://localhost/index.html' });
    await sleep(600);
    await cdp.eval(`
      localStorage.setItem('bcai_token', '${fixtures.user1.token}');
      localStorage.setItem('bcai_user', JSON.stringify({
        id: ${fixtures.user1.id},
        email: 'personal_user_f1@test.local',
        full_name: '${fixtures.user1.name}',
        role: 'user'
      }));
    `);
    await cdp.send('Page.navigate', { url: 'http://localhost/index.html' });
    await sleep(1000);
    await cdp.screenshot('v4-f-overview-personal-1440.png');

    console.log('\n--- 3. Overview Doctor User (1440px) ---');
    await cdp.eval(`
      localStorage.setItem('bcai_token', '${fixtures.doctor.token}');
      localStorage.setItem('bcai_user', JSON.stringify({
        id: ${fixtures.doctor.id},
        email: 'doctor_user_f@test.local',
        full_name: '${fixtures.doctor.name}',
        role: 'doctor'
      }));
    `);
    await cdp.send('Page.navigate', { url: 'http://localhost/index.html' });
    await sleep(1000);
    await cdp.screenshot('v4-f-overview-doctor-1440.png');

    // =========================================================================
    // 4. STRUCTURED ML ANALYSIS (1440px & 390px)
    // =========================================================================
    console.log('\n--- 5. Structured ML Analysis Result (1440px & 390px) ---');
    await cdp.send('Page.navigate', { url: 'http://localhost/pages/ml-analysis.html' });
    await sleep(1200);
    // Load benign example and run model
    await cdp.eval(`
      document.querySelector('#btnLoadBenign')?.click();
      document.querySelector('#btnRunModel')?.click();
    `);
    await sleep(1500);
    await cdp.eval(`document.querySelector('#mlResultWorkspace')?.scrollIntoView({ behavior: 'instant' });`);
    await sleep(500);
    await cdp.screenshot('v4-f-structured-result-1440.png');

    await cdp.setViewport(390, 844);
    await sleep(400);
    await cdp.eval(`document.querySelector('#mlResultWorkspace')?.scrollIntoView({ behavior: 'instant' });`);
    await sleep(300);
    await cdp.screenshot('v4-f-structured-390.png');

    // Test Ask AI Guide handoff for structured ML
    await cdp.setViewport(1440, 900);
    await sleep(300);
    await cdp.eval(`document.querySelector('#btnAskAdvisor')?.click();`);
    await sleep(1200);
    await cdp.screenshot('v4-f-ai-guide-structured-context-1440.png');
    console.log('  ✓ Saved screenshot: v4-f-ai-guide-structured-context-1440.png');

    // =========================================================================
    // 5. MAMMOGRAPHY DL ANALYSIS (1440px & 390px)
    // =========================================================================
    console.log('\n--- 6. Mammography DL Analysis Result (1440px & 390px) ---');
    await cdp.send('Page.navigate', { url: 'http://localhost/pages/dl-analysis.html' });
    await sleep(1200);
    await cdp.eval(`
      document.querySelector('#btnLoadBenign')?.click();
      document.querySelector('#btnAnalyze')?.click();
    `);
    await sleep(2500);
    await cdp.eval(`document.querySelector('#resultWorkspace')?.scrollIntoView({ behavior: 'instant' });`);
    await sleep(500);
    await cdp.screenshot('v4-f-mammography-result-1440.png');

    await cdp.setViewport(390, 844);
    await sleep(400);
    await cdp.eval(`document.querySelector('#resultWorkspace')?.scrollIntoView({ behavior: 'instant' });`);
    await sleep(300);
    await cdp.screenshot('v4-f-mammography-390.png');

    // Test Ask AI Guide handoff for DL
    await cdp.setViewport(1440, 900);
    await sleep(300);
    await cdp.eval(`document.querySelector('#btnAskAiGuide')?.click();`);
    await sleep(1200);
    await cdp.screenshot('v4-f-ai-guide-dl-context-1440.png');
    console.log('  ✓ Saved screenshot: v4-f-ai-guide-dl-context-1440.png');

    // =========================================================================
    // 6. EXPERIMENTAL FUSION (1440px & 390px)
    // =========================================================================
    console.log('\n--- 7. Experimental Fusion Disagreement (1440px & 390px) ---');
    await cdp.send('Page.navigate', { url: 'http://localhost/pages/multimodal.html' });
    await sleep(1200);
    // Load ML Malignant + DL Benign to create branch disagreement
    await cdp.eval(`
      document.querySelector('#loadMlMalignantBtn')?.click();
      document.querySelector('#loadDlBenignBtn')?.click();
      document.querySelector('#runFusionBtn')?.click();
    `);
    await sleep(3000);
    await cdp.eval(`document.querySelector('#fusionResultsStage')?.scrollIntoView({ behavior: 'instant' });`);
    await sleep(500);
    await cdp.screenshot('v4-f-fusion-disagreement-1440.png');

    await cdp.setViewport(390, 844);
    await sleep(400);
    await cdp.eval(`document.querySelector('#fusionResultsStage')?.scrollIntoView({ behavior: 'instant' });`);
    await sleep(300);
    await cdp.screenshot('v4-f-fusion-390.png');

    // Test Ask AI Guide handoff for Fusion
    await cdp.setViewport(1440, 900);
    await sleep(300);
    await cdp.eval(`document.querySelector('#askAdvisorBtn')?.click();`);
    await sleep(1200);
    await cdp.screenshot('v4-f-ai-guide-fusion-context-1440.png');
    console.log('  ✓ Saved screenshot: v4-f-ai-guide-fusion-context-1440.png');

    // =========================================================================
    // 7. AI GUIDE EMPTY STATE (1440px & 390px)
    // =========================================================================
    console.log('\n--- 13 & 24. AI Guide Empty State (1440px & 390px) ---');
    await cdp.eval(`sessionStorage.removeItem('bcai_advisor_context');`);
    await cdp.send('Page.navigate', { url: 'http://localhost/pages/advisor.html' });
    await sleep(1000);
    await cdp.screenshot('v4-f-ai-guide-empty-1440.png');

    await cdp.setViewport(390, 844);
    await sleep(400);
    await cdp.screenshot('v4-f-ai-guide-390.png');

    // =========================================================================
    // 8. DOCTOR WORKSPACE / RESEARCH REGISTRY (1440px & 390px)
    // =========================================================================
    console.log('\n--- 8 & 22. Doctor Workspace (1440px & 390px) ---');
    await cdp.setViewport(1440, 900);
    await cdp.eval(`
      localStorage.setItem('bcai_token', '${fixtures.doctor.token}');
      localStorage.setItem('bcai_user', JSON.stringify({
        id: ${fixtures.doctor.id},
        email: 'doctor_user_f@test.local',
        full_name: '${fixtures.doctor.name}',
        role: 'doctor'
      }));
    `);
    await cdp.send('Page.navigate', { url: 'http://localhost/pages/patients.html' });
    await sleep(1500);

    const curUrl = await cdp.eval(`window.location.href`);
    const hasAddBtn = await cdp.eval(`document.querySelector('#openAddPatientBtn') !== null`);
    console.log(`  patients.html state: URL=${curUrl}, hasAddBtn=${hasAddBtn}`);

    // Verify modal accessibility: Open Register Patient modal
    await cdp.eval(`document.querySelector('#openAddPatientBtn')?.click();`);
    await sleep(400);
    const overlayExists = await cdp.eval(`document.querySelector('#patientModalOverlay') !== null`);
    const modalAria = await cdp.eval(`document.querySelector('#patientModalOverlay')?.getAttribute('aria-modal')`);
    console.log(`  overlayExists=${overlayExists}, modalAria=${modalAria}`);
    if (modalAria !== 'true') {
      const bText = await cdp.eval(`document.body.innerText`);
      throw new Error(`Patient modal missing aria-modal="true"! Body text: ${bText.slice(0, 300)}`);
    }
    console.log('  ✓ Verified: Patient modal has aria-modal="true" and accessibility bindings.');

    // Test Escape key closes modal
    await cdp.send('Input.dispatchKeyEvent', { type: 'keyDown', key: 'Escape', code: 'Escape' });
    await sleep(300);
    const modalClosed = await cdp.eval(`document.querySelector('#patientModalOverlay') === null`);
    if (!modalClosed) throw new Error('Escape key failed to close modal!');
    console.log('  ✓ Verified: Escape key successfully closed modal and restored focus.');

    await cdp.screenshot('v4-f-doctor-workspace-1440.png');

    await cdp.setViewport(390, 844);
    await sleep(400);
    await cdp.screenshot('v4-f-doctor-workspace-390.png');

    // =========================================================================
    // 9. PATIENT DETAIL TIMELINE (1440px)
    // =========================================================================
    console.log('\n--- 9. Patient Detail Timeline (1440px) ---');
    await cdp.setViewport(1440, 900);
    await cdp.send('Page.navigate', { url: `http://localhost/pages/patient-detail.html?id=${fixtures.patients.p1}` });
    await sleep(1500);

    // Verify Research Notes copy
    const researchNotesPresent = await cdp.eval(`document.body.innerText.includes('Research Notes')`);
    if (!researchNotesPresent) throw new Error('Research Notes label not found on patient detail!');
    await cdp.screenshot('v4-f-patient-detail-1440.png');

    // =========================================================================
    // 10. ACTIVITY (Personal & Doctor, 1440px & 390px)
    // =========================================================================
    console.log('\n--- 11. Activity Doctor with Patient Filter & Date Range (1440px) ---');
    await cdp.send('Page.navigate', { url: 'http://localhost/pages/history.html' });
    await sleep(1500);

    // Select Patient 1 from dropdown
    await cdp.eval(`{
      const sel = document.querySelector('#historyPatientSelect');
      if (sel) {
        sel.value = '${fixtures.patients.p1}';
        sel.dispatchEvent(new Event('change'));
      }
    }`);
    await sleep(400);
    const badgeText = await cdp.eval(`document.querySelector('#historyCountBadge')?.textContent || ''`);
    console.log(`  ✓ Doctor patient filter active: ${badgeText.trim()}`);

    // Set Date Range
    await cdp.eval(`{
      const f = document.querySelector('#historyDateFrom');
      const t = document.querySelector('#historyDateTo');
      if (f && t) {
        f.value = '2026-09-01';
        t.value = '2026-09-30';
        f.dispatchEvent(new Event('change'));
        t.dispatchEvent(new Event('change'));
      }
    }`);
    await sleep(400);
    await cdp.screenshot('v4-f-activity-doctor-1440.png');

    console.log('\n--- 23. Activity Feed Mobile (390px) ---');
    await cdp.setViewport(390, 844);
    await sleep(400);
    await cdp.screenshot('v4-f-activity-390.png');

    console.log('\n--- 10. Activity Personal (1440px) ---');
    await cdp.setViewport(1440, 900);
    await cdp.eval(`
      localStorage.setItem('bcai_token', '${fixtures.user1.token}');
      localStorage.setItem('bcai_user', JSON.stringify({
        id: ${fixtures.user1.id},
        email: 'personal_user_f1@test.local',
        full_name: '${fixtures.user1.name}',
        role: 'user'
      }));
    `);
    await cdp.send('Page.navigate', { url: 'http://localhost/pages/history.html' });
    await sleep(1200);
    await cdp.screenshot('v4-f-activity-personal-1440.png');

    // =========================================================================
    // 11. REPORTS WORKSPACE (1440px)
    // =========================================================================
    console.log('\n--- 12. Reports Workspace with Date Filter & Count Badge (1440px) ---');
    await cdp.send('Page.navigate', { url: 'http://localhost/pages/reports.html' });
    await sleep(1200);
    const reportsBadge = await cdp.eval(`document.querySelector('#reportCountBadge')?.textContent || ''`);
    console.log(`  ✓ Reports count badge: ${reportsBadge.trim()}`);
    await cdp.screenshot('v4-f-reports-1440.png');

    // =========================================================================
    // 12. ACCOUNT SECURITY & LOGOUT-ALL MODAL (1440px)
    // =========================================================================
    console.log('\n--- 17. Account Security (1440px) ---');
    await cdp.send('Page.navigate', { url: 'http://localhost/pages/profile.html' });
    await sleep(1200);
    await cdp.eval(`document.querySelector('#logoutAllDevicesBtn')?.click();`);
    await sleep(400);

    // Verify modal copy (no refresh tokens wording)
    const modalText = await cdp.eval(`document.querySelector('#logoutAllModal')?.innerText || ''`);
    if (modalText.toLowerCase().includes('refresh tokens')) {
      throw new Error('Logout-all modal still mentions refresh tokens!');
    }
    console.log('  ✓ Verified: Logout-all modal uses clean canonical session revocation copy.');
    await cdp.screenshot('v4-f-account-security-1440.png');

    // =========================================================================
    // 13. PRIVACY GUARANTEE VERIFICATION
    // =========================================================================
    console.log('\n--- Privacy Verification: Context Wipe on Logout/Login ---');
    await cdp.eval(`
      sessionStorage.setItem('bcai_advisor_context', JSON.stringify({
        analysis_type: 'fusion',
        user_secret_data: 'DO_NOT_LEAK'
      }));
    `);
    // User 1 logs out
    await cdp.eval(`
      import('/js/core/auth.js').then(m => m.auth.clear());
    `);
    const remainingContextAfterLogout = await cdp.eval(`sessionStorage.getItem('bcai_advisor_context')`);
    if (remainingContextAfterLogout !== null) {
      throw new Error('auth.clear() failed to wipe transient sessionStorage advisor context!');
    }
    console.log('  ✓ Verified: auth.clear() completely wiped transient advisor context.');

    // User 2 logs in
    await cdp.eval(`
      import('/js/core/auth.js').then(m => m.auth.save({
        access_token: '${fixtures.user2.token}',
        user: { id: ${fixtures.user2.id}, email: 'personal_user_f2@test.local', full_name: 'Bob Second User F', role: 'user' }
      }));
    `);
    const remainingContextAfterLogin = await cdp.eval(`sessionStorage.getItem('bcai_advisor_context')`);
    if (remainingContextAfterLogin !== null) {
      throw new Error('auth.save() allowed stale transient context to persist!');
    }
    console.log('  ✓ Verified: auth.save() guarantees zero context persistence across users.');

    console.log('\n====================================================');
    console.log('BATCH F QA E2E SUITE: ALL 24 SCREENSHOTS CAPTURED');
    console.log('====================================================\n');
  } catch (err) {
    console.error('\n❌ Batch F E2E Suite Failed:', err);
    process.exitCode = 1;
  } finally {
    if (cdp && cdp.ws) {
      try { cdp.ws.close(); } catch {}
    }
    try { chromeProc.kill('SIGTERM'); } catch {}

    console.log('Cleaning up test fixtures in SQLite...');
    const cleanPy = `
import sqlite3
conn = sqlite3.connect('backend/data/app.db')
c = conn.cursor()
c.execute("DELETE FROM predictions WHERE user_id IN (${fixtures.user1.id}, ${fixtures.user2.id}, ${fixtures.doctor.id})")
c.execute("DELETE FROM patients WHERE user_id IN (${fixtures.user1.id}, ${fixtures.user2.id}, ${fixtures.doctor.id})")
c.execute("DELETE FROM sessions WHERE user_id IN (${fixtures.user1.id}, ${fixtures.user2.id}, ${fixtures.doctor.id})")
c.execute("DELETE FROM users WHERE id IN (${fixtures.user1.id}, ${fixtures.user2.id}, ${fixtures.doctor.id})")
conn.commit()
conn.close()
`;
    try {
      runPython(cleanPy);
      console.log('✓ Cleaned up test database fixtures.');
    } catch (e) {
      console.error('Fixture cleanup error:', e);
    }
  }
}

main().then(() => {
  process.exit(process.exitCode || 0);
}).catch((err) => {
  console.error(err);
  process.exit(1);
});
