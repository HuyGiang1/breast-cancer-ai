import assert from 'node:assert';
import {
  parseClinicalCsv,
  generateCsvTemplate,
  generateExampleCsv,
  normalizeHeader,
} from '../frontend/js/utils/clinical-csv.js';
import { SAMPLES, ML_FEATURES } from '../frontend/js/config/ml-features.js';

console.log('Running test_clinical_csv.js...');

// 1. Template generation
const template = generateCsvTemplate();
assert.strictEqual(template.trim().split(',').length, 30);
assert.strictEqual(template.startsWith('mean_radius,mean_texture'), true);

// 2. Example CSV generation
const example = generateExampleCsv(SAMPLES.benign);
const parsedExample = parseClinicalCsv(example);
assert.strictEqual(parsedExample.rowCount, 1);
assert.strictEqual(parsedExample.rows[0].valid, true);
assert.strictEqual(parsedExample.rows[0].values.mean_radius, 13.54);

// 3. Valid snake_case 30-column CSV with CRLF
const sampleLine = ML_FEATURES.map((f) => SAMPLES.benign[f]).join(',');
const snakeCsv = `${ML_FEATURES.join(',')}\r\n${sampleLine}\r\n`;
const parsedSnake = parseClinicalCsv(snakeCsv);
assert.strictEqual(parsedSnake.rowCount, 1);
assert.strictEqual(parsedSnake.rows[0].valid, true);

// 4. Valid space-name WDBC headers with ignored id, diagnosis, target
const spaceHeaders = ML_FEATURES.map((f) => f.replace(/_/g, ' '));
const allHeaders = ['id', 'diagnosis', ...spaceHeaders, 'target', 'Unnamed: 32'];
const dataRow = ['842302', 'M', ...ML_FEATURES.map((f) => SAMPLES.malignant[f]), '1', ''];
const spaceCsv = `${allHeaders.join(',')}\n${dataRow.join(',')}\n`;
const parsedSpace = parseClinicalCsv(spaceCsv);
assert.strictEqual(parsedSpace.rowCount, 1);
assert.strictEqual(parsedSpace.rows[0].valid, true);
assert.strictEqual(parsedSpace.rows[0].id, '842302');
assert.strictEqual(parsedSpace.rows[0].values.mean_radius, 17.99);

// 5. Multiple rows detection
const multiCsv = `${ML_FEATURES.join(',')}\n${sampleLine}\n${ML_FEATURES.map((f) => SAMPLES.malignant[f]).join(',')}\n`;
const parsedMulti = parseClinicalCsv(multiCsv);
assert.strictEqual(parsedMulti.isMultiRow, true);
assert.strictEqual(parsedMulti.rowCount, 2);
assert.strictEqual(parsedMulti.rows[0].valid, true);
assert.strictEqual(parsedMulti.rows[1].valid, true);

// 6. Missing feature error
assert.throws(() => {
  parseClinicalCsv('mean_radius,mean_texture\n14.0,20.0');
}, /missing/i);

// 7. Duplicate alias mapping error
assert.throws(() => {
  parseClinicalCsv(`mean_radius,mean radius,${ML_FEATURES.slice(1).join(',')}\n1,2,...`);
}, /duplicate/i);

// 8. Non-numeric cell
const nonNumRow = [...ML_FEATURES.map((f) => SAMPLES.benign[f])];
nonNumRow[0] = 'not_a_number';
const nonNumCsv = `${ML_FEATURES.join(',')}\n${nonNumRow.join(',')}`;
const parsedNonNum = parseClinicalCsv(nonNumCsv);
assert.strictEqual(parsedNonNum.rows[0].valid, false);
assert.match(parsedNonNum.rows[0].errors[0], /non-numeric/i);

// 9. Negative number
const negRow = [...ML_FEATURES.map((f) => SAMPLES.benign[f])];
negRow[0] = '-12.5';
const negCsv = `${ML_FEATURES.join(',')}\n${negRow.join(',')}`;
const parsedNeg = parseClinicalCsv(negCsv);
assert.strictEqual(parsedNeg.rows[0].valid, false);
assert.match(parsedNeg.rows[0].errors[0], /negative/i);

// 10. Empty cell
const emptyCellRow = [...ML_FEATURES.map((f) => SAMPLES.benign[f])];
emptyCellRow[0] = '';
const emptyCellCsv = `${ML_FEATURES.join(',')}\n${emptyCellRow.join(',')}`;
const parsedEmptyCell = parseClinicalCsv(emptyCellCsv);
assert.strictEqual(parsedEmptyCell.rows[0].valid, false);
assert.match(parsedEmptyCell.rows[0].errors[0], /blank/i);

// 11. Quoted values
const quotedRow = ML_FEATURES.map((f) => `"${SAMPLES.benign[f]}"`).join(',');
const quotedCsv = `${ML_FEATURES.join(',')}\n${quotedRow}\n`;
const parsedQuoted = parseClinicalCsv(quotedCsv);
assert.strictEqual(parsedQuoted.rows[0].valid, true);
assert.strictEqual(parsedQuoted.rows[0].values.mean_radius, 13.54);

console.log('ALL CSV PARSING AND VALIDATION TESTS PASSED!');
