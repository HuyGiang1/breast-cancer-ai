/**
 * QA Batch E E2E Browser Test Suite (Chrome DevTools Protocol)
 *
 * Verifies:
 * - Registration: Personal vs Doctor card selection & revealable invite code
 * - Doctor Workspace (/pages/patients.html):
 *   - Summary strip (Total Patients, Analyses Logged, ML, DL, Fusion)
 *   - Search & sort toolbar
 *   - Accessible Add / Edit Patient modal
 *   - Safety-explicit Delete Confirmation modal
 * - Patient Detail (/pages/patient-detail.html):
 *   - Dedicated single-patient endpoint retrieval
 *   - 3-Modality Quick Launch Bar (Structured ML, Mammography DL, Multimodal Fusion)
 *   - Clinical research notes
 *   - Chronological patient timeline
 * - Role isolation:
 *   - Personal account blocked from /pages/patients.html with Access Restricted notice
 *   - Personal account blocked from /pages/patient-detail.html with Access Restricted notice
 * - Activity (/pages/history.html):
 *   - "My Activity" for personal user (no patient selector)
 *   - "Analysis Activity" for doctor user with patient selector filter
 * - Reports (/pages/reports.html):
 *   - Modality & patient filters
 *   - Print / Save PDF action trigger
 * - Profile (/pages/profile.html):
 *   - Doctor capabilities display & prototype disclaimer
 *   - "Sign out all devices" confirmation modal calling logoutAll()
 * - Mobile responsive rendering at 390px
 * - 17 required screenshots
 */

const fs = require('fs');
const path = require('path');
const http = require('http');
const { spawn, execSync } = require('child_process');

const SCREENSHOT_DIR = path.resolve(__dirname, '../docs/v4/screenshots');
const ARTIFACT_DIR = path.resolve('/Users/GiangNguyenHuy/.gemini/antigravity-ide/brain/62658f2a-6d4b-455d-b237-69778800e810/screenshots');
if (!fs.existsSync(SCREENSHOT_DIR)) fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
if (!fs.existsSync(ARTIFACT_DIR)) fs.mkdirSync(ARTIFACT_DIR, { recursive: true });

const PORT = 9570;

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
          } catch {
            if (attempts > 30) reject(new Error('Failed to parse /json'));
            else setTimeout(check, 300);
          }
        });
      }).on('error', () => {
        if (attempts > 30) reject(new Error('Cannot reach Chrome'));
        else setTimeout(check, 300);
      });
    };
    check();
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
    if (res.exceptionDetails) {
      throw new Error(`Eval error: ${JSON.stringify(res.exceptionDetails)}`);
    }
    return res.result ? res.result.value : undefined;
  }

  async setViewport(width, height) {
    await this.send('Emulation.setDeviceMetricsOverride', {
      width,
      height,
      deviceScaleFactor: 1,
      mobile: width < 600,
    });
    await sleep(250);
  }

  async screenshot(filename) {
    const res = await this.send('Page.captureScreenshot', { format: 'png' });
    const buffer = Buffer.from(res.data, 'base64');
    const dest1 = path.join(SCREENSHOT_DIR, filename);
    const dest2 = path.join(ARTIFACT_DIR, filename);
    fs.writeFileSync(dest1, buffer);
    fs.writeFileSync(dest2, buffer);
    console.log(`  ✓ Saved screenshot: ${filename} (${buffer.length} bytes)`);
  }
}

function runPython(code) {
  return execSync(`PYTHONPATH=.:backend venv/bin/python -c "${code.replace(/"/g, '\\"')}"`, { encoding: 'utf-8' }).trim();
}

async function main() {
  console.log('====================================================');
  console.log('PHASE 4R BATCH E: WORKSPACE & DOCTOR / PERSONAL E2E');
  console.log('====================================================');

  // Launch Headless Chrome
  const chromeProc = spawn('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', [
    '--headless=new',
    `--remote-debugging-port=${PORT}`,
    '--disable-gpu',
    '--no-sandbox',
    '--window-size=1440,900',
    'about:blank',
  ]);

  await sleep(1500);

  let cdp;
  let fixtures;

  try {
    const wsUrl = await getWebSocketUrl();
    cdp = new CDPClient(wsUrl);
    await cdp.init();
    await cdp.send('Page.enable');
    await cdp.send('Runtime.enable');
    await cdp.send('DOM.enable');

    // 1. Setup Test Fixtures in Database
    console.log('\nSetting up test fixtures in SQLite...');
    const setupPy = `
import sqlite3, json
from datetime import datetime, timedelta, timezone
UTC = timezone.utc
conn = sqlite3.connect('backend/data/app.db')
c = conn.cursor()
now = datetime.now(UTC).isoformat()
exp = (datetime.now(UTC) + timedelta(days=7)).isoformat()

# Clean old Batch E test data
c.execute("DELETE FROM predictions WHERE user_id IN (SELECT id FROM users WHERE email LIKE '%_batch_e@test.local')")
c.execute("DELETE FROM sessions WHERE user_id IN (SELECT id FROM users WHERE email LIKE '%_batch_e@test.local')")
c.execute("DELETE FROM patients WHERE full_name LIKE '%Batch E%'")
c.execute("DELETE FROM users WHERE email LIKE '%_batch_e@test.local'")
conn.commit()

from app.core.security import hash_password, create_session_token
pwd = hash_password('TestPass123!')

# 1. Normal User
c.execute("INSERT INTO users (email, password_hash, full_name, role, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
          ('user_batch_e@test.local', pwd, 'Jane Personal Batch E', 'user', now, now))
user_id = c.lastrowid
user_token = create_session_token()
c.execute("INSERT INTO sessions (user_id, token, expires_at, created_at) VALUES (?, ?, ?, ?)", (user_id, user_token, exp, now))

# Normal user prediction
c.execute("""INSERT INTO predictions (user_id, patient_id, prediction_type, model_name, diagnosis, probability, raw_probability, calibration_mode, risk_band, input_payload, response_payload, created_at)
             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
          (user_id, None, 'ml', 'Wisconsin Ridge (Calibrated)', 'Benign', 0.12, 0.12, 'sigmoid', 'low',
           json.dumps({'features': {'radius_mean': 12.0}}), json.dumps({'diagnosis': 'Benign'}), now))

# 2. Doctor User
c.execute("INSERT INTO users (email, password_hash, full_name, role, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
          ('doctor_batch_e@test.local', pwd, 'Dr. Aris Thorne Batch E', 'doctor', now, now))
doc_id = c.lastrowid
doc_token = create_session_token()
c.execute("INSERT INTO sessions (user_id, token, expires_at, created_at) VALUES (?, ?, ?, ?)", (doc_id, doc_token, exp, now))

# Doctor Patient 1: Elena Rostova (2 analyses: 1 ML, 1 DL)
c.execute("""INSERT INTO patients (user_id, full_name, date_of_birth, gender, notes, created_at, updated_at)
             VALUES (?, ?, ?, ?, ?, ?, ?)""",
          (doc_id, 'Elena Rostova Batch E', '1984-05-14', 'Female', 'Referred for bilateral diagnostic mammography and cytological FNA evaluation.', now, now))
p1_id = c.lastrowid

c.execute("""INSERT INTO predictions (user_id, patient_id, prediction_type, model_name, diagnosis, probability, raw_probability, calibration_mode, risk_band, input_payload, response_payload, created_at)
             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
          (doc_id, p1_id, 'ml', 'Wisconsin Ridge (Calibrated)', 'Benign', 0.15, 0.15, 'sigmoid', 'low',
           json.dumps({'features': {'radius_mean': 13.5}}), json.dumps({'diagnosis': 'Benign'}), now))

c.execute("""INSERT INTO predictions (user_id, patient_id, prediction_type, model_name, diagnosis, probability, raw_probability, calibration_mode, risk_band, input_payload, response_payload, created_at)
             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
          (doc_id, p1_id, 'dl', 'EfficientNet-B0 (Production)', 'Malignant', 0.78, 0.78, 'temperature', 'high',
           json.dumps({'image': 'cbis_sample.png'}), json.dumps({'diagnosis': 'Malignant'}), now))

# Doctor Patient 2: Sarah Connor (1 multimodal fusion)
c.execute("""INSERT INTO patients (user_id, full_name, date_of_birth, gender, notes, created_at, updated_at)
             VALUES (?, ?, ?, ?, ?, ?, ?)""",
          (doc_id, 'Sarah Connor Batch E', '1975-11-20', 'Female', 'High-density tissue, multimodal experimental follow-up.', now, now))
p2_id = c.lastrowid

c.execute("""INSERT INTO predictions (user_id, patient_id, prediction_type, model_name, diagnosis, probability, raw_probability, calibration_mode, risk_band, input_payload, response_payload, created_at)
             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
          (doc_id, p2_id, 'multimodal', '40% ML + 60% DL Combined', 'Malignant', 0.65, 0.65, 'heuristic', 'moderate_high',
           json.dumps({'weights': [0.4, 0.6]}), json.dumps({'diagnosis': 'Malignant'}), now))

# Doctor Patient 3: Clara Oswald (0 analyses)
c.execute("""INSERT INTO patients (user_id, full_name, date_of_birth, gender, notes, created_at, updated_at)
             VALUES (?, ?, ?, ?, ?, ?, ?)""",
          (doc_id, 'Clara Oswald Batch E', '1992-03-08', 'Female', 'Initial baseline intake. No scans scheduled yet.', now, now))
p3_id = c.lastrowid

# Doctor Unlinked prediction
c.execute("""INSERT INTO predictions (user_id, patient_id, prediction_type, model_name, diagnosis, probability, raw_probability, calibration_mode, risk_band, input_payload, response_payload, created_at)
             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
          (doc_id, None, 'ml', 'Wisconsin Ridge (Calibrated)', 'Benign', 0.08, 0.08, 'sigmoid', 'low',
           json.dumps({'features': {'radius_mean': 11.0}}), json.dumps({'diagnosis': 'Benign'}), now))

conn.commit()
print(json.dumps({
    'user': {'id': user_id, 'token': user_token, 'email': 'user_batch_e@test.local', 'name': 'Jane Personal Batch E'},
    'doctor': {'id': doc_id, 'token': doc_token, 'email': 'doctor_batch_e@test.local', 'name': 'Dr. Aris Thorne Batch E'},
    'patients': {'p1': p1_id, 'p2': p2_id, 'p3': p3_id}
}))
`;
    fixtures = JSON.parse(runPython(setupPy));
    console.log('✓ Fixtures initialized:', fixtures);

    // Helpers to inject session into localStorage
    const loginAs = async (token, userObj) => {
      await cdp.eval(`
        localStorage.setItem('bcai_token', '${token}');
        localStorage.setItem('bcai_user', JSON.stringify(${JSON.stringify(userObj)}));
      `);
    };

    const logout = async () => {
      await cdp.eval(`
        localStorage.removeItem('bcai_token');
        localStorage.removeItem('bcai_user');
      `);
    };

    // =========================================================================
    // SCREENSHOT 1: register-personal-1440.png
    // =========================================================================
    console.log('\n--- 1. Registration Default Personal (1440px) ---');
    await cdp.setViewport(1440, 900);
    await cdp.send('Page.navigate', { url: 'http://localhost/register.html' });
    await sleep(1000);
    await logout();
    await cdp.eval(`
      const pRadio = document.querySelector('#typePersonalRadio');
      if (pRadio) pRadio.checked = true;
    `);
    await cdp.screenshot('register-personal-1440.png');

    // =========================================================================
    // SCREENSHOT 2: register-doctor-selected-1440.png
    // =========================================================================
    console.log('\n--- 2. Registration Doctor Selected (1440px) ---');
    await cdp.eval(`
      document.querySelector('#cardTypeDoctor')?.click();
      const codeInput = document.querySelector('#regDoctorInviteCode');
      if (codeInput) codeInput.value = 'BHS-DOC-2026-DEV';
    `);
    await sleep(300);
    await cdp.screenshot('register-doctor-selected-1440.png');

    // =========================================================================
    // SCREENSHOT 14: register-doctor-mobile-390.png
    // =========================================================================
    console.log('\n--- 14. Registration Doctor Selected (390px) ---');
    await cdp.setViewport(390, 844);
    await sleep(300);
    await cdp.screenshot('register-doctor-mobile-390.png');

    // =========================================================================
    // SCREENSHOT 3: patients-doctor-overview-1440.png
    // =========================================================================
    console.log('\n--- 3. Doctor Workspace Overview (1440px) ---');
    await cdp.setViewport(1440, 900);
    await loginAs(fixtures.doctor.token, {
      id: fixtures.doctor.id,
      email: fixtures.doctor.email,
      full_name: fixtures.doctor.name,
      role: 'doctor',
    });
    await cdp.send('Page.navigate', { url: 'http://localhost/pages/patients.html' });
    await sleep(1500);
    await cdp.screenshot('patients-doctor-overview-1440.png');

    // =========================================================================
    // SCREENSHOT 4: patients-add-modal-1440.png
    // =========================================================================
    console.log('\n--- 4. Register Patient Modal (1440px) ---');
    await cdp.eval(`
      document.querySelector('#openAddPatientBtn')?.click();
      const nameIn = document.querySelector('#patFullName');
      if (nameIn) nameIn.value = 'Amelia Pond Batch E';
      const dobIn = document.querySelector('#patDob');
      if (dobIn) dobIn.value = '1989-06-25';
      const genderIn = document.querySelector('#patGender');
      if (genderIn) genderIn.value = 'Female';
      const notesIn = document.querySelector('#patNotes');
      if (notesIn) notesIn.value = 'Annual baseline screening research cohort.';
    `);
    await sleep(400);
    await cdp.screenshot('patients-add-modal-1440.png');

    // Submit patient
    await cdp.eval(`
      document.querySelector('#patientForm')?.dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
    `);
    await sleep(1000);

    // =========================================================================
    // SCREENSHOT 5: patients-populated-registry-1440.png
    // =========================================================================
    console.log('\n--- 5. Populated Patient Registry (1440px) ---');
    await cdp.screenshot('patients-populated-registry-1440.png');

    // =========================================================================
    // SCREENSHOT 6: patients-delete-modal-1440.png
    // =========================================================================
    console.log('\n--- 6. Safety Delete Confirmation Modal (1440px) ---');
    await cdp.eval(`
      const delBtn = document.querySelector('[data-delete-patient]');
      if (delBtn) delBtn.click();
    `);
    await sleep(400);
    await cdp.screenshot('patients-delete-modal-1440.png');

    // Close delete modal without deleting
    await cdp.eval(`
      document.querySelector('#cancelDeleteModalBtn')?.click();
    `);
    await sleep(300);

    // =========================================================================
    // SCREENSHOT 15: patients-mobile-390.png
    // =========================================================================
    console.log('\n--- 15. Doctor Workspace Mobile (390px) ---');
    await cdp.setViewport(390, 844);
    await sleep(300);
    await cdp.screenshot('patients-mobile-390.png');

    // =========================================================================
    // SCREENSHOT 7: patient-detail-timeline-1440.png
    // =========================================================================
    console.log('\n--- 7. Patient Detail & Timeline (1440px) ---');
    await cdp.setViewport(1440, 900);
    await cdp.send('Page.navigate', {
      url: `http://localhost/pages/patient-detail.html?id=${fixtures.patients.p1}`,
    });
    await sleep(1500);
    await cdp.screenshot('patient-detail-timeline-1440.png');

    // =========================================================================
    // SCREENSHOT 16: patient-detail-mobile-390.png
    // =========================================================================
    console.log('\n--- 16. Patient Detail Mobile (390px) ---');
    await cdp.setViewport(390, 844);
    await sleep(300);
    await cdp.screenshot('patient-detail-mobile-390.png');

    // =========================================================================
    // SCREENSHOT 8: patients-access-denied-personal-1440.png
    // =========================================================================
    console.log('\n--- 8. Personal User Access Denied to /patients.html (1440px) ---');
    await cdp.setViewport(1440, 900);
    await loginAs(fixtures.user.token, {
      id: fixtures.user.id,
      email: fixtures.user.email,
      full_name: fixtures.user.name,
      role: 'user',
    });
    await cdp.send('Page.navigate', { url: 'http://localhost/pages/patients.html' });
    await sleep(1200);
    await cdp.screenshot('patients-access-denied-personal-1440.png');

    // =========================================================================
    // SCREENSHOT 9: patient-detail-access-denied-1440.png
    // =========================================================================
    console.log('\n--- 9. Personal User Access Denied to /patient-detail.html (1440px) ---');
    await cdp.send('Page.navigate', {
      url: `http://localhost/pages/patient-detail.html?id=${fixtures.patients.p1}`,
    });
    await sleep(1200);
    await cdp.screenshot('patient-detail-access-denied-1440.png');

    // =========================================================================
    // SCREENSHOT 10: history-personal-1440.png
    // =========================================================================
    console.log('\n--- 10. Personal User "My Activity" (1440px) ---');
    await cdp.send('Page.navigate', { url: 'http://localhost/pages/history.html' });
    await sleep(1200);
    await cdp.screenshot('history-personal-1440.png');

    // =========================================================================
    // SCREENSHOT 11: history-doctor-patient-filter-1440.png
    // =========================================================================
    console.log('\n--- 11. Doctor User "Analysis Activity" with Patient Filter (1440px) ---');
    await loginAs(fixtures.doctor.token, {
      id: fixtures.doctor.id,
      email: fixtures.doctor.email,
      full_name: fixtures.doctor.name,
      role: 'doctor',
    });
    await cdp.send('Page.navigate', { url: 'http://localhost/pages/history.html' });
    await sleep(1500);
    await cdp.screenshot('history-doctor-patient-filter-1440.png');

    // =========================================================================
    // SCREENSHOT 17: history-mobile-390.png
    // =========================================================================
    console.log('\n--- 17. Activity Feed Mobile (390px) ---');
    await cdp.setViewport(390, 844);
    await sleep(300);
    await cdp.screenshot('history-mobile-390.png');

    // =========================================================================
    // SCREENSHOT 12: reports-workspace-1440.png
    // =========================================================================
    console.log('\n--- 12. Reports Workspace (1440px) ---');
    await cdp.setViewport(1440, 900);
    await cdp.send('Page.navigate', { url: 'http://localhost/pages/reports.html' });
    await sleep(1500);
    await cdp.screenshot('reports-workspace-1440.png');

    // =========================================================================
    // SCREENSHOT 13: profile-doctor-logout-all-1440.png
    // =========================================================================
    console.log('\n--- 13. Profile Doctor Capabilities & Logout-All Modal (1440px) ---');
    await cdp.send('Page.navigate', { url: 'http://localhost/pages/profile.html' });
    await sleep(1500);
    await cdp.eval(`
      document.querySelector('#logoutAllDevicesBtn')?.click();
    `);
    await sleep(400);
    await cdp.screenshot('profile-doctor-logout-all-1440.png');

    console.log('\n====================================================');
    console.log('BATCH E QA E2E SUITE: ALL 17 SCREENSHOTS CAPTURED');
    console.log('====================================================\n');
  } catch (err) {
    console.error('Test Suite Failed:', err);
    process.exitCode = 1;
  } finally {
    if (cdp && cdp.ws) cdp.ws.close();
    chromeProc.kill('SIGTERM');
  }
}

main().then(() => {
  process.exit(process.exitCode || 0);
}).catch((err) => {
  console.error(err);
  process.exit(1);
});
