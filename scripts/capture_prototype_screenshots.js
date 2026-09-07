/**
 * Prototype Visual QA & Screenshot Capture Tool
 * Uses Chrome DevTools Protocol over native WebSocket to capture pixel-perfect responsive screenshots.
 */
const fs = require('fs');
const path = require('path');
const http = require('http');
const { spawn } = require('child_process');

const SCREENSHOT_DIR = path.resolve(__dirname, '../docs/redesign/screenshots');
if (!fs.existsSync(SCREENSHOT_DIR)) {
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
}

// Launch Headless Chrome with Remote Debugging
const chromeProc = spawn('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', [
  '--headless',
  '--remote-debugging-port=9222',
  '--hide-scrollbars',
  '--disable-gpu',
  '--no-sandbox',
  '--disable-cache',
  'http://localhost/index.html'
]);

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function getWebSocketUrl() {
  return new Promise((resolve, reject) => {
    let attempts = 0;
    const check = () => {
      attempts++;
      http.get('http://localhost:9222/json', (res) => {
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

async function capture() {
  await sleep(1500);
  const wsUrl = await getWebSocketUrl();
  console.log('Connected to Chrome DevTools Protocol at:', wsUrl);
  const client = new CDPClient(wsUrl);
  await client.ready();

  await client.send('Page.enable');
  await client.send('DOM.enable');
  await client.send('Runtime.enable');

  const targets = [
    { name: 'landing-1440.png', url: 'http://localhost/index.html', width: 1440, height: 900, mobile: false },
    { name: 'landing-390.png', url: 'http://localhost/index.html', width: 390, height: 844, mobile: true },
    { name: 'login-1440.png', url: 'http://localhost/login.html', width: 1440, height: 900, mobile: false },
    { name: 'login-390.png', url: 'http://localhost/login.html', width: 390, height: 844, mobile: true },
    { name: 'register-1440.png', url: 'http://localhost/register.html', width: 1440, height: 900, mobile: false },
    { name: 'register-390.png', url: 'http://localhost/register.html', width: 390, height: 844, mobile: true },
  ];

  for (const t of targets) {
    console.log(`Configuring viewport for ${t.name} (${t.width}x${t.height}, mobile=${t.mobile})...`);
    await client.send('Emulation.setDeviceMetricsOverride', {
      width: t.width,
      height: t.height,
      deviceScaleFactor: 1,
      mobile: t.mobile
    });

    // Clear session so guestOnly doesn't redirect
    await client.send('Runtime.evaluate', { expression: `localStorage.clear(); sessionStorage.clear();` });
    await client.send('Page.navigate', { url: t.url });
    await sleep(1200);

    // If on landing, check media integrity
    if (t.url.includes('index.html')) {
      const mediaAudit = await client.send('Runtime.evaluate', {
        expression: `
          (() => {
            const imgs = Array.from(document.querySelectorAll('img'));
            return imgs.map(img => ({
              src: img.src.split('/').slice(-2).join('/'),
              complete: img.complete,
              naturalWidth: img.naturalWidth,
              naturalHeight: img.naturalHeight
            }));
          })()
        `,
        returnByValue: true
      });
      console.log(`[Media Audit on ${t.name}]:`, JSON.stringify(mediaAudit.result.value, null, 2));
    }

    const screenshot = await client.send('Page.captureScreenshot', { format: 'png' });
    const buffer = Buffer.from(screenshot.data, 'base64');
    const dest = path.join(SCREENSHOT_DIR, t.name);
    fs.writeFileSync(dest, buffer);
    console.log(`Saved: ${dest} (${buffer.length} bytes)`);
  }

  client.close();
  chromeProc.kill();
  console.log('All prototype screenshots captured successfully.');
  process.exit(0);
}

capture().catch(err => {
  console.error('Error capturing screenshots:', err);
  chromeProc.kill();
  process.exit(1);
});
