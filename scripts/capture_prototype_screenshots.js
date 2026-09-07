/**
 * Prototype Visual QA Capture Tool
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

// 1. Launch Headless Chrome with Remote Debugging
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
              if (attempts > 20) reject(new Error('No page found'));
              else setTimeout(check, 200);
            }
          } catch (e) {
            if (attempts > 20) reject(e);
            else setTimeout(check, 200);
          }
        });
      }).on('error', () => {
        if (attempts > 20) reject(new Error('Connection failed'));
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
    { name: 'landing-1440.png', width: 1440, height: 900, mobile: false },
    { name: 'landing-1280.png', width: 1280, height: 800, mobile: false },
    { name: 'landing-768.png', width: 768, height: 1024, mobile: true },
    { name: 'landing-390.png', width: 390, height: 844, mobile: true }
  ];

  for (const t of targets) {
    console.log(`Configuring viewport for ${t.name} (${t.width}x${t.height}, mobile=${t.mobile})...`);
    await client.send('Emulation.setDeviceMetricsOverride', {
      width: t.width,
      height: t.height,
      deviceScaleFactor: 1,
      mobile: t.mobile
    });
    await client.send('Page.navigate', { url: 'http://localhost/index.html' });
    await sleep(1000);

    const screenshot = await client.send('Page.captureScreenshot', { format: 'png' });
    const buffer = Buffer.from(screenshot.data, 'base64');
    const dest = path.join(SCREENSHOT_DIR, t.name);
    fs.writeFileSync(dest, buffer);
    console.log(`Saved: ${dest} (${buffer.length} bytes)`);
  }

  // Mega-menu Analyze (1440 viewport)
  console.log('Capturing mega-menu-analyze.png...');
  await client.send('Emulation.setDeviceMetricsOverride', { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });
  await client.send('Page.navigate', { url: 'http://localhost/index.html' });
  await sleep(800);
  const evalAnalyze = await client.send('Runtime.evaluate', {
    expression: `
      document.querySelectorAll('.studio-mega-menu').forEach(el => el.classList.remove('is-open'));
      const menu = document.querySelector('.mega-menu-analyze');
      if (menu) menu.classList.add('is-open');
      menu ? menu.className : 'NOT_FOUND';
    `
  });
  console.log('Analyze menu class:', evalAnalyze);
  await sleep(500);
  const analyzeShot = await client.send('Page.captureScreenshot', { format: 'png' });
  fs.writeFileSync(path.join(SCREENSHOT_DIR, 'mega-menu-analyze.png'), Buffer.from(analyzeShot.data, 'base64'));
  console.log('Saved: mega-menu-analyze.png');

  // Mega-menu Learn (1440 viewport)
  console.log('Capturing mega-menu-learn.png...');
  await client.send('Page.navigate', { url: 'http://localhost/index.html' });
  await sleep(800);
  const evalLearn = await client.send('Runtime.evaluate', {
    expression: `
      document.querySelectorAll('.studio-mega-menu').forEach(el => el.classList.remove('is-open'));
      const menu = document.querySelector('.mega-menu-learn');
      if (menu) menu.classList.add('is-open');
      menu ? menu.className : 'NOT_FOUND';
    `
  });
  console.log('Learn menu class:', evalLearn);
  await sleep(500);
  const learnShot = await client.send('Page.captureScreenshot', { format: 'png' });
  fs.writeFileSync(path.join(SCREENSHOT_DIR, 'mega-menu-learn.png'), Buffer.from(learnShot.data, 'base64'));
  console.log('Saved: mega-menu-learn.png');

  client.close();
  chromeProc.kill();
  console.log('Screenshot generation complete.');
  process.exit(0);
}

capture().catch(err => {
  console.error('Error capturing screenshots:', err);
  chromeProc.kill();
  process.exit(1);
});
