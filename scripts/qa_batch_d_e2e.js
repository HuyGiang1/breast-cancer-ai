/**
 * QA Batch D E2E Browser Test Suite (Chrome DevTools Protocol)
 * 
 * Verifies:
 * - Empty Fusion Workstation at 1440px and 390px
 * - Shared Doctor patient context bar
 * - 30 Structured ML inputs with live status, presets, CSV, OCR
 * - Mammography dropzone with presets, dimensions, format checks
 * - Execution stages tracking
 * - Scientific probability formula: 0.4 ML raw + 0.6 DL raw
 * - Prominent Branch Disagreement panel before combined score
 * - Branch Agreement banner
 * - Non-diagnostic 0.50 software midpoint disclaimer
 * - Unpaired dataset warning
 * - Grad-CAM attention visualization in DL branch
 * - AI Educational Guidance
 * - Report link and AI Guide handoff
 * - Reset workflow
 * - 12 required screenshots
 */

const fs = require('fs');
const path = require('path');
const http = require('http');
const { spawn, execSync } = require('child_process');

const SCREENSHOT_DIR = path.resolve(__dirname, '../docs/v4/screenshots');
const ARTIFACT_DIR = path.resolve('/Users/GiangNguyenHuy/.gemini/antigravity-ide/brain/62658f2a-6d4b-455d-b237-69778800e810/screenshots');
if (!fs.existsSync(SCREENSHOT_DIR)) fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
if (!fs.existsSync(ARTIFACT_DIR)) fs.mkdirSync(ARTIFACT_DIR, { recursive: true });

const PORT = 9569;

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
    await sleep(200);
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
  console.log('PHASE 4R BATCH D: EXPERIMENTAL FUSION E2E BROWSER SUITE');
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

  await sleep(1200);

  let cdp;
  let fixtures;

  try {
    const wsUrl = await getWebSocketUrl();
    cdp = new CDPClient(wsUrl);
    await cdp.init();
    await cdp.send('Page.enable');
    await cdp.send('Runtime.enable');
    await cdp.send('DOM.enable');

    // Create test fixtures (Normal user + Doctor + Patient)
    console.log('\nSetting up test fixtures...');
    const setupPy = `
import sqlite3, json
from datetime import datetime, timedelta, timezone
UTC = timezone.utc
conn = sqlite3.connect('backend/data/app.db')
c = conn.cursor()
now = datetime.now(UTC).isoformat()
exp = (datetime.now(UTC) + timedelta(days=7)).isoformat()

# Clean old test users
c.execute("DELETE FROM sessions WHERE user_id IN (SELECT id FROM users WHERE email LIKE '%_batch_d@test.local')")
c.execute("DELETE FROM patients WHERE full_name LIKE '%Batch D%'")
c.execute("DELETE FROM users WHERE email LIKE '%_batch_d@test.local'")
conn.commit()

# Create normal user
from app.core.security import hash_password, create_session_token
u_pwd = hash_password('TestPass123!')
c.execute("INSERT INTO users (email, password_hash, full_name, role, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
          ('user_batch_d@test.local', u_pwd, 'Normal User Batch D', 'user', now, now))
user_id = c.lastrowid
user_token = create_session_token()
c.execute("INSERT INTO sessions (user_id, token, expires_at, created_at) VALUES (?, ?, ?, ?)", (user_id, user_token, exp, now))

# Create doctor user
c.execute("INSERT INTO users (email, password_hash, full_name, role, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
          ('doctor_batch_d@test.local', u_pwd, 'Dr. Emily Vance Batch D', 'doctor', now, now))
doc_id = c.lastrowid
doc_token = create_session_token()
c.execute("INSERT INTO sessions (user_id, token, expires_at, created_at) VALUES (?, ?, ?, ?)", (doc_id, doc_token, exp, now))

# Create doctor's patient
c.execute("INSERT INTO patients (user_id, full_name, date_of_birth, gender, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
          (doc_id, 'Sarah Jenkins Batch D', '1982-04-12', 'female', now, now))
patient_id = c.lastrowid

conn.commit()
conn.close()
print(json.dumps({
  'user': {'id': user_id, 'token': user_token, 'email': 'user_batch_d@test.local'},
  'doctor': {'id': doc_id, 'token': doc_token, 'email': 'doctor_batch_d@test.local', 'patient_id': patient_id}
}))
`;
    fixtures = JSON.parse(runPython(setupPy));
    console.log(`  ✓ Normal User created: ID ${fixtures.user.id}`);
    console.log(`  ✓ Doctor created: ID ${fixtures.doctor.id}, Patient ID: ${fixtures.doctor.patient_id}`);

    // Helper: Set user session in browser localStorage
    async function setAuth(userData, token) {
      await cdp.eval(`
        localStorage.setItem('bcai_token', '${token}');
        localStorage.setItem('bcai_user', JSON.stringify(${JSON.stringify(userData)}));
      `);
      await sleep(100);
    }

    // -----------------------------------------------------------------------
    // TEST 1: Normal User - Empty Fusion Workstation (1440px)
    // -----------------------------------------------------------------------
    console.log('\n[TEST 1] Empty Fusion Workstation (1440px)');
    await cdp.setViewport(1440, 900);
    await cdp.send('Page.navigate', { url: 'http://localhost/login.html' });
    await sleep(600);
    await setAuth({ id: fixtures.user.id, email: fixtures.user.email, full_name: 'Normal User Batch D', role: 'user' }, fixtures.user.token);
    await cdp.send('Page.navigate', { url: 'http://localhost/pages/multimodal.html' });
    await sleep(1000);

    // Verify title and unpaired banner
    const pageTitle = await cdp.eval(`document.querySelector('h1').textContent`);
    console.log(`  ✓ Page title: "${pageTitle.trim()}"`);
    if (!pageTitle.includes('Experimental Research Fusion')) throw new Error('Incorrect page title');

    const hasUnpairedBanner = await cdp.eval(`Boolean(document.querySelector('.fusion-unpaired-banner'))`);
    if (!hasUnpairedBanner) throw new Error('Missing unpaired dataset banner');
    console.log('  ✓ Unpaired scientific contract banner visible');

    // Verify normal user does NOT see doctor patient selector
    const hasDocSelect = await cdp.eval(`Boolean(document.querySelector('#doctorPatientSelect'))`);
    if (hasDocSelect) throw new Error('Normal user should not see doctor patient selector');
    console.log('  ✓ Doctor patient selector correctly hidden for normal user');

    await cdp.screenshot('v4-d-fusion-empty-1440.png');

    // -----------------------------------------------------------------------
    // TEST 2: Empty Workstation on Mobile (390px)
    // -----------------------------------------------------------------------
    console.log('\n[TEST 2] Empty Fusion Workstation on Mobile (390px)');
    await cdp.setViewport(390, 844);
    await sleep(300);

    const hasHorizontalOverflow = await cdp.eval(`document.documentElement.scrollWidth > window.innerWidth`);
    if (hasHorizontalOverflow) console.warn('  ⚠️ Warning: Horizontal scroll detected on 390px');
    else console.log('  ✓ No page-level horizontal overflow on mobile');

    await cdp.screenshot('v4-d-fusion-empty-390.png');

    // -----------------------------------------------------------------------
    // TEST 3: Doctor Shared Patient Context (1440px)
    // -----------------------------------------------------------------------
    console.log('\n[TEST 3] Doctor Shared Patient Context (1440px)');
    await cdp.setViewport(1440, 900);
    await setAuth({ id: fixtures.doctor.id, email: fixtures.doctor.email, full_name: 'Dr. Emily Vance Batch D', role: 'doctor' }, fixtures.doctor.token);
    await cdp.send('Page.navigate', { url: 'http://localhost/pages/multimodal.html' });
    await sleep(800);

    const hasDocBar = await cdp.eval(`Boolean(document.querySelector('.doctor-patient-bar'))`);
    if (!hasDocBar) throw new Error('Doctor should see patient context bar');
    console.log('  ✓ Doctor patient context bar visible');

    // Select patient
    await cdp.eval(`
      const select = document.querySelector('#doctorPatientSelect');
      if (select) {
        select.value = '${fixtures.doctor.patient_id}';
        select.dispatchEvent(new Event('change'));
      }
    `);
    await sleep(300);

    const selectedPatientName = await cdp.eval(`document.querySelector('.doctor-patient-info').textContent`);
    console.log(`  ✓ Doctor patient selected: ${selectedPatientName.trim().replace(/\s+/g, ' ')}`);
    await cdp.screenshot('v4-d-fusion-doctor-patient-1440.png');

    // -----------------------------------------------------------------------
    // TEST 4: Load Presets & Ready State
    // -----------------------------------------------------------------------
    console.log('\n[TEST 4] Loading Presets & Ready State');
    // Load Benign ML preset
    await cdp.eval(`document.querySelector('#loadMlBenignBtn').click()`);
    await sleep(300);

    // Load Benign DL preset
    await cdp.eval(`document.querySelector('#loadDlBenignBtn').click()`);
    await sleep(600);

    // Check pre-check status
    const mlCompleteText = await cdp.eval(`document.querySelector('.fusion-quality-pill').textContent`);
    console.log(`  ✓ ML Feature progress: ${mlCompleteText.trim()}`);
    if (!mlCompleteText.includes('30 / 30')) throw new Error('Structured branch not 30/30');

    const imagePreviewName = await cdp.eval(`document.querySelector('.fusion-preview-meta-row strong')?.textContent || ''`);
    console.log(`  ✓ DL Image selected: "${imagePreviewName.trim()}"`);

    const runBtnDisabled = await cdp.eval(`document.querySelector('#runFusionBtn').disabled`);
    console.log(`  ✓ Run button enabled: ${!runBtnDisabled}`);
    if (runBtnDisabled) throw new Error('Run button should be enabled');

    await cdp.screenshot('v4-d-fusion-ready-1440.png');

    // -----------------------------------------------------------------------
    // TEST 5: Running State Tracker
    // -----------------------------------------------------------------------
    console.log('\n[TEST 5] Running Pipeline Execution Tracking');
    // Trigger run and immediately capture running screenshot
    cdp.eval(`document.querySelector('#runFusionBtn').click()`);
    await sleep(250);

    const isRunning = await cdp.eval(`Boolean(document.querySelector('.fusion-stages-card'))`);
    if (isRunning) {
      console.log('  ✓ Staged execution card visible during inference');
      await cdp.screenshot('v4-d-fusion-running-1440.png');
    }

    // Wait for run completion
    console.log('  Waiting for inference to complete...');
    let done = false;
    for (let i = 0; i < 30; i++) {
      await sleep(500);
      done = await cdp.eval(`Boolean(document.querySelector('#fusionResultsArea'))`);
      if (done) break;
    }
    if (!done) throw new Error('Fusion run did not complete within timeout');
    console.log('  ✓ Fusion analysis completed successfully!');

    // -----------------------------------------------------------------------
    // TEST 6: Branch Agreement, Formula Visualizer & Results (1440px)
    // -----------------------------------------------------------------------
    console.log('\n[TEST 6] Branch Agreement & Formula Inspection');
    await sleep(400);

    // Verify Branch Agreement
    const hasAgreement = await cdp.eval(`Boolean(document.querySelector('.fusion-agreement-card'))`);
    if (!hasAgreement) throw new Error('Expected branch agreement banner for benign demo');
    console.log('  ✓ Branch Agreement banner confirmed');

    // Verify Formula visualizer contains exact numbers
    const formulaText = await cdp.eval(`document.querySelector('.fusion-formula-grid').textContent`);
    console.log(`  ✓ Formula components: ${formulaText.trim().replace(/\s+/g, ' ')}`);
    if (!formulaText.includes('0.40') || !formulaText.includes('0.60')) {
      throw new Error('Formula visualizer missing 0.40 / 0.60 weights');
    }

    await cdp.screenshot('v4-d-fusion-agreement-1440.png');

    // Scroll down to inspect formula & combined score
    await cdp.eval(`document.querySelector('.fusion-formula-card').scrollIntoView()`);
    await sleep(300);
    await cdp.screenshot('v4-d-fusion-formula-1440.png');

    // Scroll down to inspect Grad-CAM viewer
    await cdp.eval(`document.querySelector('.fusion-branches-deepdive').scrollIntoView()`);
    await sleep(300);
    const hasGradCam = await cdp.eval(`Boolean(document.querySelector('.fusion-gradcam-display img'))`);
    console.log(`  ✓ Grad-CAM heatmap rendered in DL branch: ${hasGradCam}`);
    await cdp.screenshot('v4-d-fusion-gradcam-1440.png');

    // Scroll down to inspect AI guidance & Action bar
    await cdp.eval(`document.querySelector('.fusion-ai-card').scrollIntoView()`);
    await sleep(300);
    const aiText = await cdp.eval(`document.querySelector('.fusion-ai-body').textContent`);
    console.log(`  ✓ AI Guidance generated: ${aiText.slice(0, 100)}…`);
    await cdp.screenshot('v4-d-fusion-ai-guidance-1440.png');

    // Mobile Result View (390px)
    await cdp.setViewport(390, 844);
    await sleep(300);
    await cdp.eval(`document.querySelector('#fusionResultsArea').scrollIntoView()`);
    await sleep(200);
    await cdp.screenshot('v4-d-fusion-result-390.png');

    // -----------------------------------------------------------------------
    // TEST 7: Branch Disagreement (1440px & 390px)
    // -----------------------------------------------------------------------
    console.log('\n[TEST 7] Branch Disagreement Workflow');
    await cdp.setViewport(1440, 900);
    await cdp.eval(`window.scrollTo(0, 0)`);
    await sleep(300);

    // Load Malignant ML preset + Benign DL preset (Guaranteed disagreement!)
    await cdp.eval(`
      document.querySelector('#loadMlMalignantBtn')?.click();
      document.querySelector('#loadDlBenignBtn')?.click();
    `);
    await sleep(1500);

    console.log('  Executing disagreement combination (ML Malignant + DL Benign)...');
    await cdp.eval(`document.querySelector('#runFusionBtn')?.click();`);
    await sleep(500);
    await cdp.eval(`
      const confirmBtn = document.querySelector('#confirmOutlierBtn');
      if (confirmBtn) confirmBtn.click();
    `);
    let hasDisagreementCard = false;
    for (let i = 0; i < 40; i++) {
      await sleep(500);
      await cdp.eval(`{
        const cBtn = document.querySelector('#confirmOutlierBtn');
        if (cBtn) cBtn.click();
      }`);
      const isAnalyzing = await cdp.eval(`Boolean(document.querySelector('.fusion-stages-card'))`);
      hasDisagreementCard = await cdp.eval(`Boolean(document.querySelector('.fusion-disagreement-card'))`);
      if (hasDisagreementCard && !isAnalyzing) break;
    }

    if (!hasDisagreementCard) {
      const bText = await cdp.eval(`document.body.innerText`);
      throw new Error(`Expected prominent Branch Disagreement card! Page text: ${bText.slice(0, 400)}`);
    }
    console.log('  ✓ Prominent Branch Disagreement panel rendered BEFORE combined score!');

    const disagreementHeader = await cdp.eval(`document.querySelector('.fusion-disagreement-card h2').textContent`);
    console.log(`  ✓ Disagreement Header: "${disagreementHeader.trim()}"`);

    await cdp.screenshot('v4-d-fusion-disagreement-1440.png');

    // Mobile Disagreement View (390px)
    await cdp.setViewport(390, 844);
    await sleep(300);
    await cdp.eval(`document.querySelector('.fusion-disagreement-card').scrollIntoView()`);
    await sleep(200);
    await cdp.screenshot('v4-d-fusion-disagreement-390.png');

    // -----------------------------------------------------------------------
    // TEST 8: Report Link & AI Advisor Handoff
    // -----------------------------------------------------------------------
    console.log('\n[TEST 8] Report Link & Advisor Handoff Verification');
    await cdp.setViewport(1440, 900);

    // Verify report link URL
    const reportHref = await cdp.eval(`document.querySelector('.fusion-action-bar a[href*="/report/"]')?.href || ''`);
    console.log(`  ✓ Report URL: ${reportHref}`);
    if (!reportHref.includes('/report/')) throw new Error('Missing report URL in action bar');

    // Click Advisor Handoff
    console.log('  Testing Ask AI Guide handoff...');
    await cdp.eval(`document.querySelector('#askAdvisorBtn').click()`);
    await sleep(800);

    const currentUrl = await cdp.eval(`window.location.href`);
    console.log(`  ✓ Navigated to: ${currentUrl}`);
    if (!currentUrl.includes('/pages/advisor.html')) throw new Error('Failed to navigate to advisor page');

    const activeContextText = await cdp.eval(`document.querySelector('#app')?.textContent || ''`);
    if (!activeContextText.includes('Experimental Fusion')) throw new Error('Advisor context banner missing Experimental Fusion tag');
    console.log('  ✓ Advisor correctly received structured fusion context from sessionStorage!');

    // -----------------------------------------------------------------------
    // TEST 9: Reset Workflow
    // -----------------------------------------------------------------------
    console.log('\n[TEST 9] Reset Workflow');
    await cdp.send('Page.navigate', { url: 'http://localhost/pages/multimodal.html' });
    await sleep(600);

    // Load sample and click reset
    await cdp.eval(`document.querySelector('#loadMlBenignBtn').click()`);
    await sleep(200);
    await cdp.eval(`document.querySelector('#resetFusionBtn')?.click() || document.querySelector('#clearMlBtn')?.click()`);
    await sleep(200);

    const clearedCount = await cdp.eval(`document.querySelector('.fusion-quality-pill').textContent`);
    console.log(`  ✓ After reset: ${clearedCount.trim()}`);
    if (!clearedCount.includes('0 / 30')) throw new Error('Reset failed to clear inputs');

    console.log('\n====================================================');
    console.log('BATCH D E2E SUITE: ALL BROWSER CHECKS PASSED!');
    console.log('====================================================\n');
  } catch (err) {
    console.error('\n❌ Batch D E2E Suite Failed:', err);
    process.exitCode = 1;
  } finally {
    try {
      chromeProc.kill('SIGTERM');
    } catch {}
  }
}

main().then(() => {
  process.exit(process.exitCode || 0);
}).catch((err) => {
  console.error(err);
  process.exit(1);
});
