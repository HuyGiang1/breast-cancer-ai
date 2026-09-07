/**
 * Automated Browser Cache & Auth Navigation Test
 * Simulates normal user returning navigation across:
 * Landing -> Sign In -> Create Account -> Sign In
 * Validates V3 DOM markers, absence of legacy V2 artifacts, and URL cleanup.
 */
const fs = require('fs');
const path = require('path');
const http = require('http');
const { spawn } = require('child_process');

const SCREENSHOT_DIR = path.resolve(__dirname, '../docs/redesign/screenshots');
if (!fs.existsSync(SCREENSHOT_DIR)) {
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
}

const PORT = 9444;

// Launch Headless Chrome (normal disk cache, simulating real user returning)
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

async function runTest() {
  await sleep(1500);
  const wsUrl = await getWebSocketUrl();
  console.log('Connected to Chrome DevTools Protocol at:', wsUrl);
  const client = new CDPClient(wsUrl);
  await client.ready();

  await client.send('Page.enable');
  await client.send('DOM.enable');
  await client.send('Runtime.enable');

  await client.send('Emulation.setDeviceMetricsOverride', {
    width: 1440,
    height: 900,
    deviceScaleFactor: 1,
    mobile: false
  });

  const failures = [];

  async function evalExpression(expr) {
    const res = await client.send('Runtime.evaluate', {
      expression: expr,
      returnByValue: true
    });
    return res.result.value;
  }

  async function captureScreenshot(filename) {
    const screenshot = await client.send('Page.captureScreenshot', { format: 'png' });
    const buffer = Buffer.from(screenshot.data, 'base64');
    const dest = path.join(SCREENSHOT_DIR, filename);
    fs.writeFileSync(dest, buffer);
    console.log(`Saved screenshot: ${dest} (${buffer.length} bytes)`);
  }

  console.log('\n--- STEP 1: Navigate to Landing page ---');
  await client.send('Page.navigate', { url: 'http://localhost/index.html' });
  await sleep(1500);

  const landingTitle = await evalExpression('document.title');
  console.log('Landing title:', landingTitle);

  console.log('\n--- STEP 2: Click "Sign In" link on Landing ---');
  const signInClicked = await evalExpression(`
    (() => {
      const link = document.querySelector('a[href*="login.html"]');
      if (link) {
        link.click();
        return true;
      }
      return false;
    })()
  `);
  if (!signInClicked) throw new Error('Could not find Sign In link on landing page.');
  await sleep(1500);

  console.log('\n--- STEP 3: Assert V3 Login Page ---');
  const loginAudit = await evalExpression(`
    (() => {
      const text = document.body.innerText;
      const html = document.body.innerHTML;
      return {
        url: window.location.href,
        pathname: window.location.pathname,
        search: window.location.search,
        title: document.title,
        hasBreastHealthStudio: text.includes('Breast Health Studio'),
        hasWelcomeBack: text.includes('Welcome back'),
        hasContinueWithGoogle: text.includes('Continue with Google'),
        hasOldBranding: text.includes('BC BreastCare AI') || html.includes('BC <span>BreastCare AI</span>'),
        hasBackToHomepage: text.includes('Back to homepage'),
        hasLegacyWorkspace: text.includes('RESEARCH WORKSPACE'),
        h1: document.querySelector('h1')?.innerText
      };
    })()
  `);
  console.log('Login Audit:', JSON.stringify(loginAudit, null, 2));

  if (!loginAudit.hasBreastHealthStudio || !loginAudit.hasWelcomeBack || !loginAudit.hasContinueWithGoogle) {
    failures.push('Login page missing expected V3 markers');
  }
  if (loginAudit.hasOldBranding || loginAudit.hasBackToHomepage || loginAudit.hasLegacyWorkspace) {
    failures.push('Login page contains legacy V2 artifacts');
  }
  if (loginAudit.search.includes('v=')) {
    failures.push(`Login page URL was not cleaned: ${loginAudit.url}`);
  }

  await captureScreenshot('auth-navigation-login-1440.png');

  console.log('\n--- STEP 4: Click "Create account" link on Login ---');
  const createAccountClicked = await evalExpression(`
    (() => {
      const link = document.querySelector('a[href*="register.html"]');
      if (link) {
        link.click();
        return true;
      }
      return false;
    })()
  `);
  if (!createAccountClicked) throw new Error('Could not find Create account link on login page.');
  await sleep(1500);

  console.log('\n--- STEP 5: Assert V3 Register Page ---');
  const registerAudit = await evalExpression(`
    (() => {
      const text = document.body.innerText;
      const html = document.body.innerHTML;
      return {
        url: window.location.href,
        pathname: window.location.pathname,
        search: window.location.search,
        title: document.title,
        hasBreastHealthStudio: text.includes('Breast Health Studio'),
        hasCreateAccount: text.includes('Create your account') || text.includes('Create account'),
        hasContinueWithGoogle: text.includes('Continue with Google'),
        hasOldBranding: text.includes('BC BreastCare AI') || html.includes('BC <span>BreastCare AI</span>'),
        hasBackToHomepage: text.includes('Back to homepage'),
        hasLegacyWorkspace: text.includes('RESEARCH WORKSPACE'),
        h1: document.querySelector('h1')?.innerText
      };
    })()
  `);
  console.log('Register Audit:', JSON.stringify(registerAudit, null, 2));

  if (!registerAudit.hasBreastHealthStudio || !registerAudit.hasCreateAccount || !registerAudit.hasContinueWithGoogle) {
    failures.push('Register page missing expected V3 markers');
  }
  if (registerAudit.hasOldBranding || registerAudit.hasBackToHomepage || registerAudit.hasLegacyWorkspace) {
    failures.push('Register page contains legacy V2 artifacts');
  }
  if (registerAudit.search.includes('v=')) {
    failures.push(`Register page URL was not cleaned: ${registerAudit.url}`);
  }

  await captureScreenshot('auth-navigation-register-1440.png');

  console.log('\n--- STEP 6: Click "Sign in" link on Register ---');
  const signInFromRegisterClicked = await evalExpression(`
    (() => {
      const link = document.querySelector('a[href*="login.html"]');
      if (link) {
        link.click();
        return true;
      }
      return false;
    })()
  `);
  if (!signInFromRegisterClicked) throw new Error('Could not find Sign in link on register page.');
  await sleep(1500);

  console.log('\n--- STEP 7: Assert V3 Login Page Again ---');
  const returnLoginAudit = await evalExpression(`
    (() => {
      const text = document.body.innerText;
      return {
        url: window.location.href,
        pathname: window.location.pathname,
        search: window.location.search,
        title: document.title,
        hasBreastHealthStudio: text.includes('Breast Health Studio'),
        hasWelcomeBack: text.includes('Welcome back'),
        hasContinueWithGoogle: text.includes('Continue with Google'),
        hasOldBranding: text.includes('BC BreastCare AI'),
        hasBackToHomepage: text.includes('Back to homepage')
      };
    })()
  `);
  console.log('Return Login Audit:', JSON.stringify(returnLoginAudit, null, 2));

  if (!returnLoginAudit.hasBreastHealthStudio || !returnLoginAudit.hasWelcomeBack || !returnLoginAudit.hasContinueWithGoogle) {
    failures.push('Return Login page missing expected V3 markers');
  }
  if (returnLoginAudit.hasOldBranding || returnLoginAudit.hasBackToHomepage) {
    failures.push('Return Login page contains legacy V2 artifacts');
  }
  if (returnLoginAudit.search.includes('v=')) {
    failures.push(`Return Login page URL was not cleaned: ${returnLoginAudit.url}`);
  }

  client.close();
  chromeProc.kill();

  if (failures.length > 0) {
    console.error('\nFAILED CHECKS:\n', failures.join('\n'));
    process.exit(1);
  } else {
    console.log('\nALL AUTH NAVIGATION & CACHE INVALIDATION CHECKS PASSED SUCCESSFULLY!');
    process.exit(0);
  }
}

runTest().catch(err => {
  console.error('Test execution error:', err);
  chromeProc.kill();
  process.exit(1);
});
