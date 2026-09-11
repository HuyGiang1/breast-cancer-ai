import assert from 'node:assert';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const rootDir = path.resolve(__dirname, '..');

console.log('Running test_dl_frontend_contract.js...');

// 1. Verify demo assets exist and have nonzero size
const benignAsset = path.join(rootDir, 'frontend/assets/demo-images/demo-benign-mammogram.png');
const malignantAsset = path.join(rootDir, 'frontend/assets/demo-images/demo-malignant-mammogram.png');

assert.strictEqual(fs.existsSync(benignAsset), true, 'demo-benign-mammogram.png must exist');
assert.strictEqual(fs.existsSync(malignantAsset), true, 'demo-malignant-mammogram.png must exist');
assert.ok(fs.statSync(benignAsset).size > 10000, 'benign asset size must be > 10KB');
assert.ok(fs.statSync(malignantAsset).size > 10000, 'malignant asset size must be > 10KB');

// 2. Verify prediction.service.js defaults and parameters
const servicePath = path.join(rootDir, 'frontend/js/services/prediction.service.js');
const serviceCode = fs.readFileSync(servicePath, 'utf8');

assert.ok(
  serviceCode.includes('includeExplanation=true'),
  'predictionService.dl must default includeExplanation=true'
);
assert.ok(
  serviceCode.includes('include_explanation:includeExplanation'),
  'predictionService.dl must map includeExplanation to query parameter include_explanation'
);

// 3. Verify dl-analysis.js passes includeExplanation: true explicitly
const pagePath = path.join(rootDir, 'frontend/js/pages/dl-analysis.js');
const pageCode = fs.readFileSync(pagePath, 'utf8');

assert.ok(
  pageCode.includes('predictionService.dl'),
  'dl-analysis.js must call predictionService.dl'
);
assert.ok(
  pageCode.includes('includeExplanation: true'),
  'dl-analysis.js must explicitly specify includeExplanation: true'
);
assert.ok(
  pageCode.includes('patientId: state.selectedPatientId'),
  'dl-analysis.js must pass patientId from state'
);

// 4. Verify no legacy models or fake contour logic in dl-analysis.js
assert.strictEqual(pageCode.includes('ResNet'), false, 'dl-analysis.js must not reference legacy ResNet');
assert.strictEqual(pageCode.includes('CustomCNN'), false, 'dl-analysis.js must not reference legacy CustomCNN');
assert.strictEqual(pageCode.includes('lesion_contours'), false, 'dl-analysis.js must not reference fake lesion contours');

// 5. Verify safety language in dl-analysis.js
assert.ok(
  pageCode.includes('Grad-CAM shows coarse model-attention regions'),
  'dl-analysis.js must include required safety disclaimer'
);
assert.strictEqual(
  pageCode.includes('Tumor location'),
  false,
  'Forbidden term "Tumor location" must not exist in dl-analysis.js'
);
assert.strictEqual(
  pageCode.includes('Detected lesion'),
  false,
  'Forbidden term "Detected lesion" must not exist in dl-analysis.js'
);
assert.strictEqual(
  pageCode.includes('AI found tumor here'),
  false,
  'Forbidden term "AI found tumor here" must not exist in dl-analysis.js'
);

console.log('✓ All DL frontend contract checks passed successfully.');
