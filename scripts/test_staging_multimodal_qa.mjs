import { spawn } from 'child_process';

const chromePath = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const port = 9223;

const chrome = spawn(chromePath, [
  '--headless=new',
  `--remote-debugging-port=${port}`,
  '--no-first-run',
  '--no-default-browser-check',
  '--user-data-dir=/tmp/chrome-staging-multimodal-' + Date.now(),
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

  const consoleLogs = [];
  const consoleErrors = [];

  ws.addEventListener('message', (event) => {
    const msg = JSON.parse(event.data.toString());
    if (msg.method === 'Runtime.consoleAPICalled') {
      const text = msg.params.args.map(a => a.value || JSON.stringify(a)).join(' ');
      if (msg.params.type === 'error') {
        consoleErrors.push(text);
      } else {
        consoleLogs.push(`[${msg.params.type}] ${text}`);
      }
    }
  });

  await send('Page.enable');
  await send('Runtime.enable');
  await send('Log.enable');

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

  // Wait for initial render
  await new Promise(r => setTimeout(r, 4000));

  // --- DESKTOP VIEWPORT TEST (1280x800) ---
  console.log('\n--- TESTING DESKTOP VIEWPORT (1280x800) ---');
  await send('Emulation.setDeviceMetricsOverride', {
    width: 1280,
    height: 800,
    deviceScaleFactor: 1,
    mobile: false
  });

  const desktopEval = await send('Runtime.evaluate', {
    expression: `(() => {
      const branch1 = document.querySelector('#fusionStructuredBranch');
      const branch1Title = branch1?.querySelector('.fusion-branch-title')?.textContent?.trim();
      const manualBtn = document.querySelector('#branch1ManualBtn')?.textContent?.trim();
      const csvBtn = document.querySelector('#openCsvModalBtn')?.textContent?.trim();
      const ocrBtn = document.querySelector('#openOcrModalBtn')?.textContent?.trim();
      const presets = Array.from(document.querySelectorAll('.fusion-toolbar button')).map(b => b.textContent.trim());
      const hasClinicalFeaturesBranch = !!document.querySelector('#clinicalFeaturesBranch, .clinical-features-branch');
      const unpairedBanner = document.querySelector('.fusion-unpaired-banner')?.textContent?.trim();

      return {
        hasBranch1: !!branch1,
        branch1Title,
        manualBtn,
        csvBtn,
        ocrBtn,
        presets,
        hasClinicalFeaturesBranch,
        hasUnpairedBanner: !!unpairedBanner,
      };
    })()`,
    returnByValue: true
  });

  console.log('Desktop Branch 1 Structure:', JSON.stringify(desktopEval.result.value, null, 2));

  // Open CSV Modal
  await send('Runtime.evaluate', {
    expression: `document.querySelector('#openCsvModalBtn')?.click()`
  });
  await new Promise(r => setTimeout(r, 600));

  const modalEval = await send('Runtime.evaluate', {
    expression: `(() => {
      const modal = document.querySelector('#modalBackdrop');
      const title = modal?.querySelector('.v2-modal-title')?.textContent?.trim();
      const desc = modal?.querySelector('.v2-modal-desc')?.textContent?.trim();
      const triggerBtn = modal?.querySelector('#csvFileTriggerBtn')?.textContent?.trim();
      const templateBtn = modal?.querySelector('#downloadCsvTemplateBtn')?.textContent?.trim();
      const exampleBtn = modal?.querySelector('#downloadExampleCsvBtn')?.textContent?.trim();
      const text = modal?.innerText || '';
      const mentionsRequired30 = text.includes('30 WDBC feature columns');
      const mentionsOptionalId = text.includes('id');
      const mentionsIgnored = text.includes('diagnosis');
      const mentionsUnpaired = text.includes('Unpaired Dataset Notice');

      return {
        modalVisible: !!modal,
        title,
        desc,
        triggerBtn,
        templateBtn,
        exampleBtn,
        mentionsRequired30,
        mentionsOptionalId,
        mentionsIgnored,
        mentionsUnpaired
      };
    })()`,
    returnByValue: true
  });

  console.log('CSV Modal Content:', JSON.stringify(modalEval.result.value, null, 2));

  // --- TEST INTERACTIVE ONE-ROW CSV IMPORT ---
  console.log('\n--- TESTING INTERACTIVE ONE-ROW CSV IMPORT ---');
  const oneRowImportResult = await send('Runtime.evaluate', {
    expression: `(async () => {
      // Open modal
      document.querySelector('#openCsvModalBtn')?.click();
      await new Promise(r => setTimeout(r, 200));

      // Construct canonical 1-row CSV using exact canonical features
      const features = [
        "mean_radius","mean_texture","mean_perimeter","mean_area","mean_smoothness",
        "mean_compactness","mean_concavity","mean_concave_points","mean_symmetry","mean_fractal_dimension",
        "radius_error","texture_error","perimeter_error","area_error","smoothness_error",
        "compactness_error","concavity_error","concave_points_error","symmetry_error","fractal_dimension_error",
        "worst_radius","worst_texture","worst_perimeter","worst_area","worst_smoothness",
        "worst_compactness","worst_concavity","worst_concave_points","worst_symmetry","worst_fractal_dimension"
      ];
      const benignVals = [
        13.54, 14.36, 87.46, 566.3, 0.09779, 0.08129, 0.06664, 0.04781, 0.1885, 0.05766,
        0.2699, 0.7886, 2.058, 23.56, 0.008462, 0.0146, 0.02387, 0.01315, 0.0198, 0.0023,
        15.11, 19.26, 99.7, 711.2, 0.144, 0.1773, 0.239, 0.1288, 0.2977, 0.07259
      ];
      const csvText = features.join(',') + "\\n" + benignVals.join(',');

      // Dispatch file on csvFileInput
      const fileInput = document.querySelector('#csvFileInput');
      const file = new File([csvText], 'test_single.csv', { type: 'text/csv' });
      await fileInput.onchange({ target: { files: [file] } });

      await new Promise(r => setTimeout(r, 600));

      const modalOpen = !!document.querySelector('#modalBackdrop');
      const notifText = document.querySelector('#branch1NotificationMsg')?.textContent?.trim();
      const qualityText = document.querySelector('.fusion-quality-pill')?.textContent?.trim();
      const meanRadiusVal = document.querySelector('input[data-feature="mean_radius"]')?.value;

      return {
        modalClosed: !modalOpen,
        notifText,
        qualityText,
        meanRadiusVal
      };
    })()`,
    awaitPromise: true,
    returnByValue: true
  });
  console.log('One-Row Import Evaluation:', JSON.stringify(oneRowImportResult.result.value, null, 2));

  if (!oneRowImportResult.result.value.modalClosed) {
    throw new Error('Modal should be closed after 1-row valid CSV import');
  }
  if (!oneRowImportResult.result.value.notifText?.includes('1 valid WDBC observation loaded.')) {
    throw new Error('Notification must state 1 valid WDBC observation loaded.');
  }
  if (!oneRowImportResult.result.value.qualityText?.includes('30 / 30 Features Completed')) {
    throw new Error('Quality pill must show 30 / 30 Features Completed');
  }
  if (oneRowImportResult.result.value.meanRadiusVal !== '13.54') {
    throw new Error('mean_radius input not populated correctly: ' + oneRowImportResult.result.value.meanRadiusVal);
  }

  // --- TEST INTERACTIVE MULTI-ROW CSV IMPORT & SELECTION ---
  console.log('\n--- TESTING INTERACTIVE MULTI-ROW CSV IMPORT ---');
  const multiRowImportResult = await send('Runtime.evaluate', {
    expression: `(async () => {
      // Open modal
      document.querySelector('#openCsvModalBtn')?.click();
      await new Promise(r => setTimeout(r, 200));

      const features = [
        "id",
        "mean_radius","mean_texture","mean_perimeter","mean_area","mean_smoothness",
        "mean_compactness","mean_concavity","mean_concave_points","mean_symmetry","mean_fractal_dimension",
        "radius_error","texture_error","perimeter_error","area_error","smoothness_error",
        "compactness_error","concavity_error","concave_points_error","symmetry_error","fractal_dimension_error",
        "worst_radius","worst_texture","worst_perimeter","worst_area","worst_smoothness",
        "worst_compactness","worst_concavity","worst_concave_points","worst_symmetry","worst_fractal_dimension"
      ];
      const row1 = [
        "8510426",
        13.54, 14.36, 87.46, 566.3, 0.09779, 0.08129, 0.06664, 0.04781, 0.1885, 0.05766,
        0.2699, 0.7886, 2.058, 23.56, 0.008462, 0.0146, 0.02387, 0.01315, 0.0198, 0.0023,
        15.11, 19.26, 99.7, 711.2, 0.144, 0.1773, 0.239, 0.1288, 0.2977, 0.07259
      ];
      const row2 = [
        "842302",
        17.99, 10.38, 122.8, 1001.0, 0.1184, 0.2776, 0.3001, 0.1471, 0.2419, 0.07871,
        1.095, 0.9053, 8.589, 153.4, 0.006399, 0.04904, 0.05373, 0.01587, 0.03003, 0.006193,
        25.38, 17.33, 184.6, 2019.0, 0.1622, 0.6656, 0.7119, 0.2654, 0.4601, 0.1189
      ];
      const csvText = features.join(',') + "\\n" + row1.join(',') + "\\n" + row2.join(',');

      const fileInput = document.querySelector('#csvFileInput');
      const file = new File([csvText], 'test_multi.csv', { type: 'text/csv' });
      await fileInput.onchange({ target: { files: [file] } });

      await new Promise(r => setTimeout(r, 600));

      const modalTitle = document.querySelector('.v2-modal-title')?.textContent?.trim();
      const rowsDetected = document.body.innerText.includes('Multiple WDBC Observations Detected (2 rows)');
      const loadBtnDisabledBefore = document.querySelector('#btnLoadSelectedCsvRow')?.disabled;

      // Select row index 1 (row 2: malignant #842302)
      const radio2 = document.querySelector('#csvRowRadio_1');
      radio2?.click();
      radio2?.dispatchEvent(new Event('change', { bubbles: true }));
      await new Promise(r => setTimeout(r, 200));

      const loadBtnDisabledAfter = document.querySelector('#btnLoadSelectedCsvRow')?.disabled;

      // Click Import Selected Observation
      document.querySelector('#btnLoadSelectedCsvRow')?.click();
      await new Promise(r => setTimeout(r, 600));

      const modalOpenAfter = !!document.querySelector('#modalBackdrop');
      const meanRadiusValAfter = document.querySelector('input[data-feature="mean_radius"]')?.value;
      const notifTextAfter = document.querySelector('#branch1NotificationMsg')?.textContent?.trim();

      return {
        modalTitle,
        rowsDetected,
        loadBtnDisabledBefore,
        loadBtnDisabledAfter,
        modalOpenAfter,
        meanRadiusValAfter,
        notifTextAfter
      };
    })()`,
    awaitPromise: true,
    returnByValue: true
  });
  console.log('Multi-Row Import Evaluation:', JSON.stringify(multiRowImportResult.result.value, null, 2));

  if (!multiRowImportResult.result.value.rowsDetected) {
    throw new Error('Multi-row modal did not show Multiple WDBC Observations Detected (2 rows)');
  }
  if (!multiRowImportResult.result.value.loadBtnDisabledBefore) {
    throw new Error('Load button must be disabled before deliberate row selection');
  }
  if (multiRowImportResult.result.value.loadBtnDisabledAfter !== false) {
    throw new Error('Load button must be enabled after selecting a valid row');
  }
  if (multiRowImportResult.result.value.modalOpenAfter) {
    throw new Error('Modal should be closed after importing selected observation');
  }
  if (multiRowImportResult.result.value.meanRadiusValAfter !== '17.99') {
    throw new Error('Selected row values not imported properly (expected 17.99, got ' + multiRowImportResult.result.value.meanRadiusValAfter + ')');
  }

  // --- MOBILE VIEWPORT TEST (390x844) ---
  console.log('\n--- TESTING MOBILE VIEWPORT (390x844) ---');
  await send('Emulation.setDeviceMetricsOverride', {
    width: 390,
    height: 844,
    deviceScaleFactor: 2,
    mobile: true
  });

  const mobileEval = await send('Runtime.evaluate', {
    expression: `(() => {
      const branch1 = document.querySelector('#fusionStructuredBranch');
      const csvBtn = document.querySelector('#openCsvModalBtn');
      const rect = branch1?.getBoundingClientRect();
      const csvRect = csvBtn?.getBoundingClientRect();

      return {
        branch1Width: rect?.width,
        csvBtnVisible: csvRect?.width > 0 && csvRect?.height > 0,
      };
    })()`,
    returnByValue: true
  });
  console.log('Mobile Layout Check:', JSON.stringify(mobileEval.result.value, null, 2));

  console.log('\n--- CONSOLE ERRORS CAPTURED ---');
  console.log(consoleErrors.length === 0 ? '0 CONSOLE ERRORS (CLEAN)' : consoleErrors.join('\n'));

  // Assertions
  if (desktopEval.result.value.branch1Title !== 'Structured FNA Cytology Branch') {
    throw new Error('Branch 1 title mismatch');
  }
  if (desktopEval.result.value.csvBtn !== 'Import WDBC CSV') {
    throw new Error('CSV button text mismatch');
  }
  if (desktopEval.result.value.manualBtn !== 'Manual Entry') {
    throw new Error('Manual Entry button text mismatch');
  }
  if (desktopEval.result.value.hasClinicalFeaturesBranch) {
    throw new Error('Must NOT have separate Clinical Features section/branch');
  }
  if (modalEval.result.value.title !== 'Import WDBC FNA Features CSV') {
    throw new Error('Modal title mismatch: ' + modalEval.result.value.title);
  }
  if (!modalEval.result.value.mentionsRequired30) {
    throw new Error('Modal does not mention required 30 features');
  }
  if (!modalEval.result.value.mentionsUnpaired) {
    throw new Error('Modal does not mention unpaired dataset notice');
  }
  if (consoleErrors.length > 0) {
    throw new Error('Console errors encountered: ' + consoleErrors.join(', '));
  }

  console.log('\nALL BROWSER QA CHECKS PASSED ON LIVE STAGING!');
} finally {
  chrome.kill();
}
