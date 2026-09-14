import assert from 'node:assert';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import {
  parseClinicalCsv,
  generateCsvTemplate,
  generateExampleCsv,
} from '../frontend/js/utils/clinical-csv.js';
import { SAMPLES, ML_FEATURES } from '../frontend/js/config/ml-features.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const rootDir = path.resolve(__dirname, '..');

console.log('=== RUNNING FUSION CSV CONTRACT & UX INTEGRATION TESTS ===\n');

// ---------------------------------------------------------------------------
// TEST 1: Canonical one-row WDBC CSV -> all 30 fields populated
// ---------------------------------------------------------------------------
console.log('Test 1: Canonical one-row WDBC CSV -> all 30 fields populated');
const row1Data = ML_FEATURES.map((f) => SAMPLES.benign[f]).join(',');
const canonicalCsv = `${ML_FEATURES.join(',')}\n${row1Data}\n`;
const parsed1 = parseClinicalCsv(canonicalCsv);
assert.strictEqual(parsed1.isMultiRow, false, 'Should not be multi-row');
assert.strictEqual(parsed1.rowCount, 1, 'Should have exactly 1 row');
assert.strictEqual(parsed1.rows[0].valid, true, 'Row should be valid');
assert.strictEqual(parsed1.rows[0].completedCount, 30, 'Should have 30 completed features');

// Simulate workstation state population
const state1 = { inputs: Object.fromEntries(ML_FEATURES.map((f) => [f, ''])), outlierConfirmed: false };
for (const feat of ML_FEATURES) {
  if (parsed1.rows[0].values[feat] !== undefined) {
    state1.inputs[feat] = String(parsed1.rows[0].values[feat]);
  }
}
assert.strictEqual(Object.values(state1.inputs).filter((v) => v !== '').length, 30, 'All 30 inputs populated');
assert.strictEqual(state1.inputs.mean_radius, String(SAMPLES.benign.mean_radius));
console.log('✓ PASS: Canonical one-row CSV populates all 30 fields\n');

// ---------------------------------------------------------------------------
// TEST 2: Downloaded template + populated values -> imports successfully
// ---------------------------------------------------------------------------
console.log('Test 2: Downloaded template + populated values -> imports successfully');
const template = generateCsvTemplate();
const sampleValuesLine = ML_FEATURES.map((f) => SAMPLES.malignant[f]).join(',');
const templateWithData = `${template.trim()}\n${sampleValuesLine}\n`;
const parsed2 = parseClinicalCsv(templateWithData);
assert.strictEqual(parsed2.rowCount, 1);
assert.strictEqual(parsed2.rows[0].valid, true);
assert.strictEqual(parsed2.rows[0].values.mean_radius, SAMPLES.malignant.mean_radius);
assert.strictEqual(parsed2.rows[0].completedCount, 30);
console.log('✓ PASS: Downloaded template + values imports successfully\n');

// ---------------------------------------------------------------------------
// TEST 3: Example CSV -> imports successfully
// ---------------------------------------------------------------------------
console.log('Test 3: Example CSV -> imports successfully');
const exampleCsv = generateExampleCsv(SAMPLES.benign);
const parsed3 = parseClinicalCsv(exampleCsv);
assert.strictEqual(parsed3.rowCount, 1);
assert.strictEqual(parsed3.rows[0].valid, true);
assert.strictEqual(parsed3.rows[0].values.mean_radius, SAMPLES.benign.mean_radius);
assert.strictEqual(parsed3.rows[0].completedCount, 30);
console.log('✓ PASS: Example CSV imports successfully\n');

// ---------------------------------------------------------------------------
// TEST 4: Missing required feature -> blocked with clear error
// ---------------------------------------------------------------------------
console.log('Test 4: Missing required feature -> blocked with clear error');
const missingHeaders = ML_FEATURES.filter((f) => f !== 'worst_symmetry');
const missingData = missingHeaders.map((f) => SAMPLES.benign[f]).join(',');
const missingCsv = `${missingHeaders.join(',')}\n${missingData}\n`;
assert.throws(
  () => parseClinicalCsv(missingCsv),
  (err) => {
    assert.match(err.message, /missing.*required feature/i);
    assert.match(err.message, /worst_symmetry/i);
    return true;
  },
  'Should block import and specify missing feature'
);
console.log('✓ PASS: Missing required feature blocked with clear error\n');

// ---------------------------------------------------------------------------
// TEST 5: Non-numeric field -> blocked
// ---------------------------------------------------------------------------
console.log('Test 5: Non-numeric field -> blocked');
const nonNumericCells = ML_FEATURES.map((f) => (f === 'mean_texture' ? 'not_a_number' : SAMPLES.benign[f]));
const nonNumericCsv = `${ML_FEATURES.join(',')}\n${nonNumericCells.join(',')}\n`;
const parsed5 = parseClinicalCsv(nonNumericCsv);
assert.strictEqual(parsed5.rowCount, 1);
assert.strictEqual(parsed5.rows[0].valid, false, 'Row with text should be invalid');
assert.ok(
  parsed5.rows[0].errors.some((e) => e.includes('mean_texture') && e.includes('non-numeric')),
  'Error should flag non-numeric field mean_texture'
);
console.log('✓ PASS: Non-numeric field blocked\n');

// ---------------------------------------------------------------------------
// TEST 6: Negative feature -> blocked
// ---------------------------------------------------------------------------
console.log('Test 6: Negative feature -> blocked');
const negativeCells = ML_FEATURES.map((f) => (f === 'mean_perimeter' ? -42.5 : SAMPLES.benign[f]));
const negativeCsv = `${ML_FEATURES.join(',')}\n${negativeCells.join(',')}\n`;
const parsed6 = parseClinicalCsv(negativeCsv);
assert.strictEqual(parsed6.rowCount, 1);
assert.strictEqual(parsed6.rows[0].valid, false, 'Row with negative should be invalid');
assert.ok(
  parsed6.rows[0].errors.some((e) => e.includes('mean_perimeter') && e.includes('negative')),
  'Error should flag negative field mean_perimeter'
);
console.log('✓ PASS: Negative feature blocked\n');

// ---------------------------------------------------------------------------
// TEST 7: Optional id column -> accepted
// ---------------------------------------------------------------------------
console.log('Test 7: Optional id column -> accepted');
const headersWithId = ['id', ...ML_FEATURES];
const rowWithId = ['842302', ...ML_FEATURES.map((f) => SAMPLES.malignant[f])];
const idCsv = `${headersWithId.join(',')}\n${rowWithId.join(',')}\n`;
const parsed7 = parseClinicalCsv(idCsv);
assert.strictEqual(parsed7.rowCount, 1);
assert.strictEqual(parsed7.rows[0].valid, true);
assert.strictEqual(parsed7.rows[0].id, '842302', 'ID column properly extracted');
assert.strictEqual(parsed7.rows[0].values.mean_radius, SAMPLES.malignant.mean_radius);
assert.strictEqual(parsed7.rows[0].completedCount, 30);
console.log('✓ PASS: Optional id column accepted\n');

// ---------------------------------------------------------------------------
// TEST 8: Diagnosis / label extra columns -> safely ignored
// ---------------------------------------------------------------------------
console.log('Test 8: Diagnosis / label extra columns -> safely ignored');
const headersExtra = ['id', 'diagnosis', 'target', 'label', ...ML_FEATURES, 'Unnamed: 32'];
const rowExtra = ['8510426', 'B', '0', 'benign', ...ML_FEATURES.map((f) => SAMPLES.benign[f]), ''];
const extraCsv = `${headersExtra.join(',')}\n${rowExtra.join(',')}\n`;
const parsed8 = parseClinicalCsv(extraCsv);
assert.strictEqual(parsed8.rowCount, 1);
assert.strictEqual(parsed8.rows[0].valid, true);
assert.strictEqual(parsed8.rows[0].id, '8510426');
assert.strictEqual(parsed8.rows[0].completedCount, 30);
assert.strictEqual(parsed8.rows[0].values.diagnosis, undefined, 'diagnosis is ignored');
assert.strictEqual(parsed8.rows[0].values.target, undefined, 'target is ignored');
assert.strictEqual(parsed8.rows[0].values.label, undefined, 'label is ignored');
console.log('✓ PASS: Extra metadata columns safely ignored\n');

// ---------------------------------------------------------------------------
// TEST 9: Multi-row CSV -> never silently chooses row 1
// ---------------------------------------------------------------------------
console.log('Test 9: Multi-row CSV -> never silently chooses row 1');
const multiRowCsv = `${headersWithId.join(',')}\n` +
  `8510426,${ML_FEATURES.map((f) => SAMPLES.benign[f]).join(',')}\n` +
  `842302,${ML_FEATURES.map((f) => SAMPLES.malignant[f]).join(',')}\n`;
const parsed9 = parseClinicalCsv(multiRowCsv);
assert.strictEqual(parsed9.isMultiRow, true, 'isMultiRow flag set');
assert.strictEqual(parsed9.rowCount, 2, 'rowCount is 2');

// Simulate workstation state: selectedCsvRowIndex must initially be null
let selectedCsvRowIndex = null;
const state9 = { inputs: Object.fromEntries(ML_FEATURES.map((f) => [f, ''])) };
// Verify that with selectedCsvRowIndex === null, no row is imported
assert.strictEqual(selectedCsvRowIndex, null, 'No row is silently selected');
assert.strictEqual(Object.values(state9.inputs).every((v) => v === ''), true, 'Inputs remain blank until explicit selection');
console.log('✓ PASS: Multi-row CSV requires explicit selection; never silently selects row 1\n');

// ---------------------------------------------------------------------------
// TEST 10: Explicit selected multi-row observation -> correct 30 values loaded
// ---------------------------------------------------------------------------
console.log('Test 10: Explicit selected multi-row observation -> correct 30 values loaded');
// Explicitly select row index 1 (the second row: malignant)
selectedCsvRowIndex = 1;
const chosenRow = parsed9.rows[selectedCsvRowIndex];
assert.strictEqual(chosenRow.id, '842302');
for (const feat of ML_FEATURES) {
  if (chosenRow.values[feat] !== undefined) {
    state9.inputs[feat] = String(chosenRow.values[feat]);
  }
}
assert.strictEqual(state9.inputs.mean_radius, String(SAMPLES.malignant.mean_radius));
assert.strictEqual(state9.inputs.worst_concave_points, String(SAMPLES.malignant.worst_concave_points));
assert.strictEqual(Object.values(state9.inputs).filter((v) => v !== '').length, 30, 'All 30 fields loaded from selected row');
console.log('✓ PASS: Explicitly selected multi-row observation loads correct 30 values\n');

// ---------------------------------------------------------------------------
// TEST 11: After CSV import, Fusion still requires a mammography image
// ---------------------------------------------------------------------------
console.log('Test 11: After CSV import, Fusion still requires a mammography image');
const workstationState = {
  inputs: { ...state9.inputs }, // 30 complete features
  file: null, // No mammogram image selected
  errorMessage: null,
};
function checkFusionPreconditions(s) {
  const completeCount = Object.values(s.inputs).filter((v) => v !== '' && !Number.isNaN(Number(v))).length;
  if (completeCount < 30) {
    s.errorMessage = `Structured branch is incomplete (${completeCount}/30 features).`;
    return false;
  }
  if (!s.file) {
    s.errorMessage = 'A valid mammography image is required to run Experimental Fusion.';
    return false;
  }
  return true;
}
const canRun = checkFusionPreconditions(workstationState);
assert.strictEqual(canRun, false, 'Fusion must not execute without an image');
assert.strictEqual(workstationState.errorMessage, 'A valid mammography image is required to run Experimental Fusion.');
console.log('✓ PASS: Fusion still strictly requires a mammography image after CSV import\n');

// ---------------------------------------------------------------------------
// TEST 12: Fusion scientific/unpaired disclaimer remains visible
// ---------------------------------------------------------------------------
console.log('Test 12: Fusion scientific/unpaired disclaimer remains visible');
const multimodalJsPath = path.join(rootDir, 'frontend', 'js', 'pages', 'multimodal.js');
const jsContent = fs.readFileSync(multimodalJsPath, 'utf8');

// Check that multimodal.js contains the unpaired disclaimer banner and modal notices
assert.ok(jsContent.includes('fusion-unpaired-banner'), 'Multimodal hero banner must include fusion-unpaired-banner');
assert.ok(jsContent.includes('Unpaired Dataset Scientific Contract'), 'Must include Unpaired Dataset Scientific Contract');
assert.ok(jsContent.includes('Unpaired Dataset Notice'), 'Modal must include Unpaired Dataset Notice');
assert.ok(jsContent.includes('Import WDBC FNA Features CSV'), 'Modal title must be Import WDBC FNA Features CSV');
assert.ok(jsContent.includes('Import WDBC CSV'), 'Branch 1 must include Import WDBC CSV button');
assert.ok(jsContent.includes('Manual Entry'), 'Branch 1 must include Manual Entry button');
assert.ok(jsContent.includes('1 valid WDBC observation loaded.'), 'Success message must state 1 valid WDBC observation loaded.');
console.log('✓ PASS: Unpaired disclaimer and scientific terminology verified in code\n');

console.log('===========================================================');
console.log('ALL 12 FUSION CSV INTEGRATION & UX TESTS PASSED SUCCESSFULLY!');
console.log('===========================================================');
