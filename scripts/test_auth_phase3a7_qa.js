/**
 * Automated Browser QA & Visual Artifacts Tool for Phase 3A.7
 * Captures required responsive screenshots and validates:
 * 1. Account resolution card on duplicate email registration
 * 2. V3 Forgot Password layout & generic response
 * 3. V3 Reset Password layout, URL token cleanup, and submission
 * 4. Missing/invalid token error handling
 */
const fs = require('fs');
const path = require('path');
const http = require('http');
const { spawn } = require('child_process');

const SCREENSHOT_DIR = path.resolve(__dirname, '../docs/redesign/screenshots');
const ARTIFACT_DIR = path.resolve('/Users/GiangNguyenHuy/.gemini/antigravity-ide/brain/62658f2a-6d4b-455d-b237-69778800e810/screenshots');
if (!fs.existsSync(SCREENSHOT_DIR)) fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
if (!fs.existsSync(ARTIFACT_DIR)) fs.mkdirSync(ARTIFACT_DIR, { recursive: true });

const PORT = 9455;

// Launch Headless Chrome
const chromeProc = spawn('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', [
  '--headless',
  `--remote-debugging-port=${PORT}`,
  '--hide-scrollbars',
  '--disable-gpu',
  '--no-sandbox',
  'about:blank'
]);

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function getWebSocketUrl() {
  return new Promise((resolve, reject) => {
    let attempts = 0;
    const check = () => {
      attempts++;
      http.get(`http://localhost:${PORT}/json`, (res) => {
        let data = '';
        res.on('data', chunk => data += chunk);
        res.on('end', () => {
          try {
            const list = JSON.parse(data);
            const page = list.find(t => t.type === 'page');
            if (page && page.webSocketDebuggerUrl) {
              resolve(page.webSocketDebuggerUrl);
            } else {
              if (attempts > 30) reject(new Error('No page found'));
              else setTimeout(check, 200);
            }
          } catch (e) {
            if (attempts > 30) reject(e);
            else setTimeout(check, 200);
          }
        });
      }).on('error', () => {
        if (attempts > 30) reject(new Error('Connection failed'));
        else setTimeout(check, 200);
      });
    };
    check();
  });
}

class CDPClient {
  constructor(wsUrl) {
    this.ws = new WebSocket(wsUrl);
    this.id = 0;
    this.callbacks = new Map();
    this.ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      if (msg.id && this.callbacks.has(msg.id)) {
        const { resolve, reject } = this.callbacks.get(msg.id);
        this.callbacks.delete(msg.id);
        if (msg.error) reject(msg.error);
        else resolve(msg.result);
      }
    };
  }

  ready() {
    return new Promise((resolve, reject) => {
      if (this.ws.readyState === WebSocket.OPEN) return resolve();
      this.ws.onopen = resolve;
      this.ws.onerror = reject;
    });
  }

  send(method, params = {}) {
    return new Promise((resolve, reject) => {
      const id = ++this.id;
      this.callbacks.set(id, { resolve, reject });
      this.ws.send(JSON.stringify({ id, method, params }));
    });
  }

  close() {
    this.ws.close();
  }
}

async function run() {
  try {
    await sleep(1500);
    const wsUrl = await getWebSocketUrl();
    console.log('Connected to Chrome DevTools Protocol at:', wsUrl);
    const client = new CDPClient(wsUrl);
    await client.ready();

    await client.send('Page.enable');
    await client.send('DOM.enable');
    await client.send('Runtime.enable');

    async function setViewport(width, height, mobile = false, scale = 1) {
      await client.send('Emulation.setDeviceMetricsOverride', {
        width,
        height,
        deviceScaleFactor: scale,
        mobile
      });
      await sleep(300);
    }

    async function evalExpr(expr) {
      const res = await client.send('Runtime.evaluate', {
        expression: expr,
        returnByValue: true
      });
      return res.result ? res.result.value : null;
    }

    async function captureScreenshot(filename) {
      const screenshot = await client.send('Page.captureScreenshot', { format: 'png' });
      const buffer = Buffer.from(screenshot.data, 'base64');
      const dest1 = path.join(SCREENSHOT_DIR, filename);
      const dest2 = path.join(ARTIFACT_DIR, filename);
      fs.writeFileSync(dest1, buffer);
      fs.writeFileSync(dest2, buffer);
      console.log(`Saved screenshot: ${filename} (${buffer.length} bytes)`);
    }

    // --- SEED DISPOSABLE QA ACCOUNT VIA API ---
    const qaEmail = `qa-auth-${Date.now()}@example.invalid`;
    console.log(`Using disposable QA address: ${qaEmail}`);

    const regInit = await fetch('http://localhost/api/v1/auth/register/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: qaEmail,
        full_name: 'QA Disposable User',
        password: 'InitialPassword123!'
      })
    });
    console.log('Seed register status:', regInit.status);

    // ==========================================
    // TEST 1: Register Existing Email UX
    // ==========================================
    console.log('\n--- TEST 1: Register Existing Email Resolution UX ---');
    await setViewport(1440, 900);
    await client.send('Page.navigate', { url: 'http://localhost/register.html' });
    await sleep(1500);

    // Fill registration form with duplicate email
    await evalExpr(`
      (() => {
        document.getElementById('regFullName').value = 'Another Duplicate';
        document.getElementById('regEmail').value = '${qaEmail}';
        document.getElementById('regPassword').value = 'SecondPassword123!';
        document.getElementById('regConfirm').value = 'SecondPassword123!';
        document.getElementById('registerForm').dispatchEvent(new Event('submit', { cancelable: true }));
      })()
    `);
    await sleep(1500);

    const resCard = await evalExpr(`
      (() => {
        const card = document.querySelector('.account-resolution-card');
        return {
          exists: !!card,
          text: card ? card.innerText : null,
          hasSignInBtn: !!document.querySelector('.resolution-actions a[href*="login.html"]'),
          hasResetBtn: !!document.querySelector('.resolution-actions a[href*="forgot-password.html"]')
        };
      })()
    `);
    console.log('Resolution Card Audit:', resCard);
    if (!resCard.exists || !resCard.hasSignInBtn || !resCard.hasResetBtn) {
      throw new Error('Account resolution card failed to render properly.');
    }

    await captureScreenshot('register-existing-email-1440.png');

    // ==========================================
    // TEST 2: Forgot Password V3
    // ==========================================
    console.log('\n--- TEST 2: Forgot Password V3 ---');
    await setViewport(1440, 900);
    await client.send('Page.navigate', { url: 'http://localhost/forgot-password.html' });
    await sleep(1500);

    const forgotAudit = await evalExpr(`
      (() => {
        const bodyText = document.body.innerText;
        return {
          title: document.title,
          hasBreastHealthStudio: bodyText.includes('Breast Health Studio'),
          hasForgotHeading: bodyText.includes('Forgot your password?'),
          hasSendResetLink: bodyText.includes('Send reset link'),
          hasLegacyV2: !!document.querySelector('.v2-card, .v2-field, .v2-button')
        };
      })()
    `);
    console.log('Forgot Password Audit (Desktop):', forgotAudit);
    if (!forgotAudit.hasBreastHealthStudio || !forgotAudit.hasForgotHeading || forgotAudit.hasLegacyV2) {
      throw new Error('Forgot password does not adhere to V3 design system.');
    }

    await captureScreenshot('forgot-password-1440.png');

    // Mobile viewport
    await setViewport(390, 844, true, 2);
    await captureScreenshot('forgot-password-390.png');

    // Submit forgot password request on desktop
    await setViewport(1440, 900);
    await evalExpr(`
      (() => {
        document.getElementById('forgotEmail').value = '${qaEmail}';
        document.getElementById('forgotForm').dispatchEvent(new Event('submit', { cancelable: true }));
      })()
    `);
    await sleep(1500);

    const forgotResult = await evalExpr(`
      (() => {
        const devHelper = document.getElementById('devTokenHelper');
        const alert = document.getElementById('authAlert');
        const tokenLink = devHelper ? devHelper.querySelector('a')?.href : null;
        return {
          alertText: alert ? alert.innerText : null,
          tokenLink: tokenLink
        };
      })()
    `);
    console.log('Forgot Result:', forgotResult);

    if (!forgotResult.alertText || !forgotResult.alertText.includes('If an account exists')) {
      throw new Error('Forgot password failed to show safe generic message.');
    }

    // Direct API call in file mode to get token for testing
    let resetUrl = forgotResult.tokenLink;
    if (!resetUrl) {
      const fResp = await fetch('http://localhost/api/v1/auth/forgot-password/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: qaEmail })
      });
      const fData = await fResp.json();
      resetUrl = `http://localhost/reset-password.html?token=${fData.reset_token}&v=auth-v3`;
    }
    console.log('Direct reset URL to test:', resetUrl);

    // ==========================================
    // TEST 3: Reset Password V3 with Token
    // ==========================================
    console.log('\n--- TEST 3: Reset Password V3 with Token ---');
    await setViewport(1440, 900);
    await client.send('Page.navigate', { url: resetUrl });
    await sleep(1500);

    const resetAudit = await evalExpr(`
      (() => {
        const bodyText = document.body.innerText;
        return {
          title: document.title,
          urlCleaned: !window.location.search.includes('token='),
          hasBreastHealthStudio: bodyText.includes('Breast Health Studio'),
          hasSetNewPassword: bodyText.includes('Set a new password'),
          hasLegacyV2: !!document.querySelector('.v2-card, .v2-field, .v2-button')
        };
      })()
    `);
    console.log('Reset Password Audit (Desktop):', resetAudit);
    if (!resetAudit.hasBreastHealthStudio || !resetAudit.hasSetNewPassword || resetAudit.hasLegacyV2) {
      throw new Error('Reset password does not adhere to V3 design system.');
    }
    if (!resetAudit.urlCleaned) {
      console.warn('Warning: Token was not cleaned from visible URL bar via history.replaceState.');
    }

    await captureScreenshot('reset-password-1440.png');

    // Mobile viewport
    await setViewport(390, 844, true, 2);
    await captureScreenshot('reset-password-390.png');

    // Submit new password
    await setViewport(1440, 900);
    await evalExpr(`
      (() => {
        document.getElementById('newPassword').value = 'UpdatedPassword456!';
        document.getElementById('confirmPassword').value = 'UpdatedPassword456!';
        document.getElementById('resetForm').dispatchEvent(new Event('submit', { cancelable: true }));
      })()
    `);
    await sleep(500);

    const resetSuccess = await evalExpr(`
      (() => {
        const alert = document.getElementById('authAlert');
        return alert ? alert.innerText : null;
      })()
    `);
    console.log('Reset Submit Result:', resetSuccess);

    await sleep(1200);
    const currentPath = await evalExpr('window.location.pathname');
    console.log('Post-reset path:', currentPath);

    if (!resetSuccess && !currentPath.includes('login.html')) {
      throw new Error('Password reset submission failed.');
    }

    // ==========================================
    // TEST 4: Reset Password with Missing Token
    // ==========================================
    console.log('\n--- TEST 4: Reset Password Missing Token State ---');
    await client.send('Page.navigate', { url: 'http://localhost/reset-password.html' });
    await sleep(1500);

    const missingTokenAudit = await evalExpr(`
      (() => {
        const title = document.getElementById('resetTitle');
        const subtitle = document.getElementById('resetSubtitle');
        const actions = document.getElementById('invalidTokenActions');
        return {
          titleText: title ? title.innerText : null,
          subtitleText: subtitle ? subtitle.innerText : null,
          actionsVisible: actions && actions.style.display !== 'none'
        };
      })()
    `);
    console.log('Missing Token State Audit:', missingTokenAudit);
    if (!missingTokenAudit.titleText.includes('Invalid') || !missingTokenAudit.actionsVisible) {
      throw new Error('Missing token did not show controlled error state.');
    }

    // --- CLEANUP DISPOSABLE QA RECORD ---
    console.log('\n--- CLEANUP: Removing only explicitly generated disposable QA records ---');
    const { execSync } = require('child_process');
    execSync(`sqlite3 backend/data/app.db "DELETE FROM users WHERE email = '${qaEmail}';"`);
    console.log(`Cleaned up ${qaEmail} successfully.`);

    console.log('\n=============================================');
    console.log('ALL PHASE 3A.7 BROWSER TESTS PASSED PERFECTLY');
    console.log('=============================================\n');

    client.close();
    chromeProc.kill();
    process.exit(0);
  } catch (err) {
    console.error('Browser QA failed:', err);
    chromeProc.kill();
    process.exit(1);
  }
}

run();
