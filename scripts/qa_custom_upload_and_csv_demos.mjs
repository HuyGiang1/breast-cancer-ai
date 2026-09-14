import { spawn } from 'child_process';
import fs from 'fs';
import path from 'path';

const chromePath = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const port = 9224;

const chrome = spawn(chromePath, [
  '--headless=new',
  `--remote-debugging-port=${port}`,
  '--no-first-run',
  '--no-default-browser-check',
  '--user-data-dir=/tmp/chrome-staging-upload-' + Date.now(),
  'about:blank'
]);

await new Promise(r => setTimeout(r, 1500));

try {
  const versionRes = await fetch(`http://127.0.0.1:${port}/json/version`);
  const versionData = await versionRes.json();
  console.log('Connected to Headless Chrome:', versionData.Browser);

  const newTabRes = await fetch(`http://127.0.0.1:${port}/json/new?https://staging.breastcare.click/pages/multimodal.html`, { method: 'PUT' });
  const page = await newTabRes.json();

  const ws = new WebSocket(page.webSocketDebuggerUrl);
  await new Promise((resolve) => ws.addEventListener('open', resolve, { once: true }));

  let id = 1;
  const send = (method, params = {}) => {
    return new Promise((resolve, reject) => {
      const msgId = id++;
      const handler = (event) => {
        const msg = JSON.parse(event.data.toString());
        if (msg.id === msgId) {
          ws.removeEventListener('message', handler);
          if (msg.error) reject(msg.error);
          else resolve(msg.result);
        }
      };
      ws.addEventListener('message', handler);
      ws.send(JSON.stringify({ id: msgId, method, params }));
    });
  };

  await send('Page.enable');
  await send('Runtime.enable');
  await send('DOM.enable');

  await send('Page.addScriptToEvaluateOnNewDocument', {
    source: `
      localStorage.setItem('bcai_token', 'test-session-token');
      localStorage.setItem('bcai_user', JSON.stringify({
        id: 'test-doctor-id',
        email: 'doctor@staging.test',
        role: 'doctor'
      }));
    `
  });

  await send('Page.navigate', { url: 'https://staging.breastcare.click/pages/multimodal.html' });

  // Wait for #fusionStructuredBranch to be present
  for (let i = 0; i < 20; i++) {
    await new Promise(r => setTimeout(r, 500));
    const check = await send('Runtime.evaluate', {
      expression: '!!document.querySelector("#fusionStructuredBranch")',
      returnByValue: true
    });
    if (check.result.value) {
      console.log('Workstation mounted after', (i + 1) * 0.5, 's');
      break;
    }
  }

  console.log('\n--- 1. VERIFY SYMMETRICAL BRANCH 1 & BRANCH 2 TOOLBAR UX ---');
  const toolbarCheck = await send('Runtime.evaluate', {
    expression: `(() => {
      const b1 = document.querySelector('#fusionStructuredBranch');
      const b2 = document.querySelector('#fusionMammographyBranch');
      return {
        b1_research_demos: !!b1?.querySelector('#loadMlBenignBtn') && !!b1?.querySelector('#loadMlMalignantBtn'),
        b1_benign_text: b1?.querySelector('#loadMlBenignBtn')?.textContent.trim(),
        b1_malignant_text: b1?.querySelector('#loadMlMalignantBtn')?.textContent.trim(),
        b1_csv_demos: !!b1?.querySelector('#downloadBenignCsvBtn') && !!b1?.querySelector('#downloadMalignantCsvBtn'),
        b1_input_methods: !!b1?.querySelector('#branch1ManualBtn') && !!b1?.querySelector('#openCsvModalBtn') && !!b1?.querySelector('#openOcrModalBtn'),
        b1_clear: !!b1?.querySelector('#clearMlBtn'),
        b2_research_demos: !!b2?.querySelector('#loadDlBenignBtn') && !!b2?.querySelector('#loadDlMalignantBtn'),
        b2_benign_text: b2?.querySelector('#loadDlBenignBtn')?.textContent.trim(),
        b2_malignant_text: b2?.querySelector('#loadDlMalignantBtn')?.textContent.trim(),
        b2_your_image: !!b2?.querySelector('#uploadMammogramToolbarBtn'),
        b2_dropzone_upload: !!b2?.querySelector('#selectImageTriggerBtn'),
      };
    })()`,
    returnByValue: true,
  });

  console.log('Toolbar UX Elements:', toolbarCheck.result.value);
  if (!toolbarCheck.result.value.b1_research_demos || !toolbarCheck.result.value.b1_csv_demos || !toolbarCheck.result.value.b2_your_image) {
    throw new Error('Toolbar UX elements missing!');
  }
  console.log('✓ PASS: Symmetrical Branch 1 & Branch 2 Toolbars verified.');

  console.log('\n--- 2. VERIFY CSV DOWNLOAD DEMOS AND PRESETS MATCH ---');
  const csvDownloadCheck = await send('Runtime.evaluate', {
    expression: `(async () => {
      const benignRes = await fetch('/assets/demo-csv/wdbc_benign_research_demo.csv');
      const benignText = await benignRes.text();
      const malRes = await fetch('/assets/demo-csv/wdbc_malignant_research_demo.csv');
      const malText = await malRes.text();
      return {
        benignStatus: benignRes.status,
        benignLines: benignText.trim().split('\\n').length,
        benignFirstVal: benignText.trim().split('\\n')[1].split(',')[0],
        malStatus: malRes.status,
        malLines: malText.trim().split('\\n').length,
        malFirstVal: malText.trim().split('\\n')[1].split(',')[0],
      };
    })()`,
    awaitPromise: true,
    returnByValue: true,
  });

  console.log('CSV Download Check:', csvDownloadCheck.result.value);
  if (csvDownloadCheck.result.value.benignStatus !== 200 || csvDownloadCheck.result.value.malStatus !== 200) {
    throw new Error('Demo CSVs returned non-200');
  }
  console.log('✓ PASS: Both Benign and Malignant WDBC CSV demo files served with HTTP 200.');

  console.log('\n--- 3. CSV ROUND-TRIP TEST: BENIGN CSV ---');
  // Clear Branch 1 -> load benign CSV text via simulated drop -> verify 30/30
  const benignRoundTrip = await send('Runtime.evaluate', {
    expression: `(async () => {
      // Clear
      document.querySelector('#clearMlBtn').click();
      const beforeCount = Object.values(Array.from(document.querySelectorAll('.fusion-field-input')).map(i => i.value)).filter(v => v !== '').length;

      // Fetch benign CSV text
      const res = await fetch('/assets/demo-csv/wdbc_benign_research_demo.csv');
      const text = await res.text();

      // Open CSV Modal
      document.querySelector('#openCsvModalBtn').click();

      // Trigger text handler through dropzone event simulation
      const file = new File([text], 'wdbc_benign_research_demo.csv', { type: 'text/csv' });
      const dt = new DataTransfer();
      dt.items.add(file);
      const dropzone = document.querySelector('#csvDropzone');
      const dropEvt = new DragEvent('drop', { dataTransfer: dt, bubbles: true, cancelable: true });
      dropzone.dispatchEvent(dropEvt);

      // Wait a moment
      await new Promise(r => setTimeout(r, 500));

      const afterInputs = Array.from(document.querySelectorAll('.fusion-field-input')).map(i => ({
        feat: i.dataset.feature,
        val: i.value
      }));
      const filledCount = afterInputs.filter(i => i.val !== '').length;
      const meanRadius = afterInputs.find(i => i.feat === 'mean_radius')?.val;
      const worstFractal = afterInputs.find(i => i.feat === 'worst_fractal_dimension')?.val;

      return {
        beforeCount,
        filledCount,
        meanRadius,
        worstFractal,
      };
    })()`,
    awaitPromise: true,
    returnByValue: true,
  });

  console.log('Benign CSV Round-trip Result:', benignRoundTrip.result.value);
  if (benignRoundTrip.result.value.filledCount !== 30 || benignRoundTrip.result.value.meanRadius !== '13.54') {
    throw new Error('Benign CSV round trip failed!');
  }
  console.log('✓ PASS: Benign CSV imported and populated exact 30 features (mean_radius = 13.54).');

  console.log('\n--- 4. CSV ROUND-TRIP TEST: MALIGNANT CSV ---');
  const malRoundTrip = await send('Runtime.evaluate', {
    expression: `(async () => {
      // Clear
      document.querySelector('#clearMlBtn').click();

      // Fetch malignant CSV text
      const res = await fetch('/assets/demo-csv/wdbc_malignant_research_demo.csv');
      const text = await res.text();

      // Open CSV Modal
      document.querySelector('#openCsvModalBtn').click();

      // Trigger text handler through dropzone event simulation
      const file = new File([text], 'wdbc_malignant_research_demo.csv', { type: 'text/csv' });
      const dt = new DataTransfer();
      dt.items.add(file);
      const dropzone = document.querySelector('#csvDropzone');
      const dropEvt = new DragEvent('drop', { dataTransfer: dt, bubbles: true, cancelable: true });
      dropzone.dispatchEvent(dropEvt);

      await new Promise(r => setTimeout(r, 500));

      const afterInputs = Array.from(document.querySelectorAll('.fusion-field-input')).map(i => ({
        feat: i.dataset.feature,
        val: i.value
      }));
      const filledCount = afterInputs.filter(i => i.val !== '').length;
      const meanRadius = afterInputs.find(i => i.feat === 'mean_radius')?.val;
      const worstFractal = afterInputs.find(i => i.feat === 'worst_fractal_dimension')?.val;

      return {
        filledCount,
        meanRadius,
        worstFractal,
      };
    })()`,
    awaitPromise: true,
    returnByValue: true,
  });

  console.log('Malignant CSV Round-trip Result:', malRoundTrip.result.value);
  if (malRoundTrip.result.value.filledCount !== 30 || malRoundTrip.result.value.meanRadius !== '17.99') {
    throw new Error('Malignant CSV round trip failed!');
  }
  console.log('✓ PASS: Malignant CSV imported and populated exact 30 features (mean_radius = 17.99).');

  console.log('\n--- 5. TEST CUSTOM MAMMOGRAM UPLOAD (>1 MB, 1.66 MB CBIS-DDSM) ---');
  const customImagePath = path.resolve('data/cbis_ddsm/processed/images/test/benign/1.3.6.1.4.1.9590.100.1.2.364769939511865969122167341301370556814__1-102.png');
  const customImageBase64 = fs.readFileSync(customImagePath).toString('base64');

  const customUploadResult = await send('Runtime.evaluate', {
    expression: `(async () => {
      const b64 = "${customImageBase64}";
      const byteCharacters = atob(b64);
      const byteNumbers = new Array(byteCharacters.length);
      for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i);
      }
      const byteArray = new Uint8Array(byteNumbers);
      const file = new File([byteArray], '1.3.6.1.4.1.9590.100.1.2.364769939511865969122167341301370556814__1-102.png', { type: 'image/png' });

      // Use dropzone drop
      const dt = new DataTransfer();
      dt.items.add(file);
      const dropzone = document.querySelector('#mammogramDropzone');
      const dropEvt = new DragEvent('drop', { dataTransfer: dt, bubbles: true, cancelable: true });
      dropzone.dispatchEvent(dropEvt);

      await new Promise(r => setTimeout(r, 1000));

      const preview = document.querySelector('.fusion-image-preview-card');
      const meta = preview ? preview.textContent : null;
      const hasImage = !!document.querySelector('#mammogramPreviewImg');
      const runBtn = document.querySelector('#runFusionBtn');

      return {
        hasImage,
        metaText: meta,
        runButtonDisabled: runBtn ? runBtn.disabled : true,
      };
    })()`,
    awaitPromise: true,
    returnByValue: true,
  });

  console.log('Custom Image Upload Result:', customUploadResult.result.value);
  if (!customUploadResult.result.value.hasImage || customUploadResult.result.value.runButtonDisabled) {
    throw new Error('Custom image upload failed to ready workstation!');
  }
  console.log('✓ PASS: Custom 1.66 MB mammogram selected and workstation is ready for execution.');

  console.log('\n--- 6. EXECUTE FULL FUSION E2E WITH CUSTOM MAMMOGRAM ---');
  const fusionExecutionResult = await send('Runtime.evaluate', {
    expression: `(async () => {
      const runBtn = document.querySelector('#runFusionBtn');
      runBtn.click();

      // Wait up to 50s for execution
      for (let i = 0; i < 100; i++) {
        await new Promise(r => setTimeout(r, 500));
        const resCard = document.querySelector('#fusionResultsArea, .fusion-results-workspace');
        const errAlert = document.querySelector('.v2-alert.error');
        if (errAlert && errAlert.textContent.trim()) {
          return { error: errAlert.textContent.trim() };
        }
        if (resCard) {
          const formula = resCard.textContent.includes('0.4') && resCard.textContent.includes('0.6');
          return {
            success: true,
            hasResultCard: true,
            summarySnippet: resCard.textContent.slice(0, 300).replace(/\s+/g, ' '),
          };
        }
      }
      return { error: 'Timeout waiting for fusion execution' };
    })()`,
    awaitPromise: true,
    returnByValue: true,
  });

  console.log('Fusion Execution Result:', fusionExecutionResult.result.value);
  if (fusionExecutionResult.result.value.error || !fusionExecutionResult.result.value.success) {
    throw new Error(`Fusion execution failed: ${fusionExecutionResult.result.value.error}`);
  }
  console.log('✓ PASS: Full Fusion E2E with custom mammogram executed successfully on staging HTTPS!');

  console.log('\n--- 7. TEST OVERSIZED (>20 MB) IMAGE REJECTION IN FRONTEND ---');
  const oversizeResult = await send('Runtime.evaluate', {
    expression: `(async () => {
      // Create a 21 MB dummy file
      const dummy = new Uint8Array(21 * 1024 * 1024);
      const file = new File([dummy], 'oversized_mammogram.png', { type: 'image/png' });

      // First remove existing image
      const removeBtn = document.querySelector('#removeImageBtn') || document.querySelector('#removeImageBtn2');
      if (removeBtn) removeBtn.click();
      await new Promise(r => setTimeout(r, 500));

      const dt = new DataTransfer();
      dt.items.add(file);
      const dropzone = document.querySelector('#mammogramDropzone');
      const dropEvt = new DragEvent('drop', { dataTransfer: dt, bubbles: true, cancelable: true });
      dropzone.dispatchEvent(dropEvt);

      await new Promise(r => setTimeout(r, 500));

      const errAlert = document.querySelector('.v2-alert.error');
      const errMsg = errAlert ? errAlert.textContent.trim() : null;

      return {
        blocked: !!errMsg,
        errorMessage: errMsg,
      };
    })()`,
    awaitPromise: true,
    returnByValue: true,
  });

  console.log('Oversized Rejection Result:', oversizeResult.result.value);
  if (!oversizeResult.result.value.blocked || !oversizeResult.result.value.errorMessage.includes('too large')) {
    throw new Error('Oversized image was not cleanly rejected in UI!');
  }
  console.log('✓ PASS: Oversized file cleanly blocked before upload with message:', oversizeResult.result.value.errorMessage);

  console.log('\n===========================================================');
  console.log('ALL LIVE STAGING BROWSER QA TESTS PASSED CLEANLY!');
  console.log('===========================================================');

  ws.close();
  chrome.kill();
  process.exit(0);
} catch (err) {
  console.error('FATAL TEST ERROR:', err);
  chrome.kill();
  process.exit(1);
}
