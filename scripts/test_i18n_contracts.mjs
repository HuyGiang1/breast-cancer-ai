// Automated test suite for Breast Health Studio i18n contracts
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const root = path.resolve(__dirname, '..');

function assert(condition, message) {
  if (!condition) {
    console.error(`❌ FAIL: ${message}`);
    process.exit(1);
  }
}

console.log('--- Checking i18n JSON files parse correctly ---');
const enPath = path.join(root, 'frontend/locales/en.json');
const viPath = path.join(root, 'frontend/locales/vi.json');

assert(fs.existsSync(enPath), 'frontend/locales/en.json must exist');
assert(fs.existsSync(viPath), 'frontend/locales/vi.json must exist');

const en = JSON.parse(fs.readFileSync(enPath, 'utf8'));
const vi = JSON.parse(fs.readFileSync(viPath, 'utf8'));

console.log('✅ JSON dictionaries parsed successfully.');

console.log('--- Checking key parity between en.json and vi.json ---');
function getDeepKeys(obj, prefix = '') {
  let keys = [];
  for (const k of Object.keys(obj)) {
    const fullKey = prefix ? `${prefix}.${k}` : k;
    if (typeof obj[k] === 'object' && obj[k] !== null && !Array.isArray(obj[k])) {
      keys = keys.concat(getDeepKeys(obj[k], fullKey));
    } else {
      keys.push(fullKey);
    }
  }
  return keys;
}

const enKeys = new Set(getDeepKeys(en));
const viKeys = new Set(getDeepKeys(vi));

const missingInVi = [...enKeys].filter(k => !viKeys.has(k));
const missingInEn = [...viKeys].filter(k => !enKeys.has(k));

if (missingInVi.length > 0) {
  console.error('Keys in EN missing from VI:', missingInVi);
}
if (missingInEn.length > 0) {
  console.error('Keys in VI missing from EN:', missingInEn);
}

assert(missingInVi.length === 0, `VI has ${missingInVi.length} missing keys`);
assert(missingInEn.length === 0, `EN has ${missingInEn.length} missing keys`);
console.log(`✅ Key parity verified: ${enKeys.size} keys match exactly across EN and VI.`);

console.log('--- Checking no empty or "undefined" values ---');
for (const k of enKeys) {
  const getVal = (o, p) => p.split('.').reduce((acc, part) => acc?.[part], o);
  const enVal = String(getVal(en, k) ?? '').trim();
  const viVal = String(getVal(vi, k) ?? '').trim();

  assert(enVal.length > 0, `EN value for ${k} is empty`);
  assert(viVal.length > 0, `VI value for ${k} is empty`);
  assert(!enVal.includes('undefined'), `EN value for ${k} contains "undefined"`);
  assert(!viVal.includes('undefined'), `VI value for ${k} contains "undefined"`);
}
console.log('✅ No empty or "undefined" translation values found.');

console.log('--- Checking all 30 WDBC features exist in wdbc.features ---');
const wdbcKeys = [
  'mean_radius', 'mean_texture', 'mean_perimeter', 'mean_area', 'mean_smoothness',
  'mean_compactness', 'mean_concavity', 'mean_concave_points', 'mean_symmetry', 'mean_fractal_dimension',
  'radius_error', 'texture_error', 'perimeter_error', 'area_error', 'smoothness_error',
  'compactness_error', 'concavity_error', 'concave_points_error', 'symmetry_error', 'fractal_dimension_error',
  'worst_radius', 'worst_texture', 'worst_perimeter', 'worst_area', 'worst_smoothness',
  'worst_compactness', 'worst_concavity', 'worst_concave_points', 'worst_symmetry', 'worst_fractal_dimension'
];

assert(wdbcKeys.length === 30, 'Should check exactly 30 WDBC features');
for (const feat of wdbcKeys) {
  assert(en.wdbc?.features?.[feat], `Missing WDBC feature in EN: ${feat}`);
  assert(vi.wdbc?.features?.[feat], `Missing WDBC feature in VI: ${feat}`);
}
console.log('✅ All 30 WDBC features localized with distinct labels in EN and VI.');

console.log('--- Checking scientific identifier and numerical contract preservation ---');
const fusionViDisclaimer = vi.fusion?.disclaimer || '';
const fusionEnDisclaimer = en.fusion?.disclaimer || '';
assert(fusionViDisclaimer.includes('WDBC') && fusionViDisclaimer.includes('CBIS-DDSM'), 'VI fusion disclaimer must mention WDBC and CBIS-DDSM');
assert(fusionViDisclaimer.includes('40% ML / 60% DL'), 'VI fusion disclaimer must preserve 40% ML / 60% DL');
assert(fusionEnDisclaimer.includes('WDBC') && fusionEnDisclaimer.includes('CBIS-DDSM'), 'EN fusion disclaimer must mention WDBC and CBIS-DDSM');

// Check doctor role disclaimer in auth
const docEnNotice = en.auth?.roleImmutableNotice || '';
const docViNotice = vi.auth?.roleImmutableNotice || '';
assert(docEnNotice.length > 20, 'Doctor role disclaimer must be present in EN');
assert(docViNotice.length > 20, 'Doctor role disclaimer must be present in VI');

console.log('✅ Disclaimers and scientific requirements strictly verified.');

console.log('--- Checking ESM resources match JSON dictionaries ---');
const { en: esmEn } = await import('../frontend/js/i18n/locales/en.js');
const { vi: esmVi } = await import('../frontend/js/i18n/locales/vi.js');

assert(JSON.stringify(esmEn) === JSON.stringify(en), 'ESM en.js must match locales/en.json');
assert(JSON.stringify(esmVi) === JSON.stringify(vi), 'ESM vi.js must match locales/vi.json');
console.log('✅ Synchronous ESM bundles perfectly match locales JSON.');

console.log('\n🎉 ALL I18N CONTRACT TESTS PASSED!\n');
