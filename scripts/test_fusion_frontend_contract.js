import assert from 'node:assert';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const rootDir = path.resolve(__dirname, '..');

console.log('Running test_fusion_frontend_contract.js...');

// 1. Verify prediction.service.js defaults and parameters for multimodal
const servicePath = path.join(rootDir, 'frontend/js/services/prediction.service.js');
const serviceCode = fs.readFileSync(servicePath, 'utf8');

assert.ok(
  serviceCode.includes('includeExplanation=true'),
  'predictionService.multimodal must support and default includeExplanation=true'
);
assert.ok(
  serviceCode.includes("body.append('include_explanation'"),
  'predictionService.multimodal must append include_explanation to FormData'
);
assert.strictEqual(
  serviceCode.includes("body.append('include_explanation','false')"),
  false,
  'predictionService.multimodal must NOT hardcode include_explanation to false'
);

// 2. Verify multimodal.js passes includeExplanation: true explicitly
const pagePath = path.join(rootDir, 'frontend/js/pages/multimodal.js');
const pageCode = fs.readFileSync(pagePath, 'utf8');

assert.ok(
  pageCode.includes('predictionService.multimodal'),
  'multimodal.js must call predictionService.multimodal'
);
assert.ok(
  pageCode.includes('includeExplanation: true'),
  'multimodal.js must explicitly specify includeExplanation: true'
);

// 3. Verify canonical combined_malignant_score is used as primary UI value
assert.ok(
  pageCode.includes('combined_malignant_score'),
  'multimodal.js must use combined_malignant_score as canonical field'
);
assert.ok(
  pageCode.includes('combinedScore'),
  'multimodal.js must track combinedScore'
);

// 4. Verify formula breakdown strictly uses raw ML and raw DL
assert.ok(
  pageCode.includes('mlRaw * 0.4'),
  'multimodal.js formula must multiply raw ML by 0.4'
);
assert.ok(
  pageCode.includes('dlRaw * 0.6'),
  'multimodal.js formula must multiply raw DL by 0.6'
);
assert.ok(
  pageCode.includes('0.40') && pageCode.includes('0.60'),
  'multimodal.js must display 0.40 and 0.60 weights in formula visualizer'
);

// 5. Verify 0.50 software decision midpoint disclaimer
assert.ok(
  pageCode.includes('0.50 is the software decision midpoint for this experimental combination and has not been validated as a clinical threshold'),
  'multimodal.js must include exact 0.50 software decision midpoint disclaimer'
);

// 6. Verify unpaired dataset scientific limitation
assert.ok(
  pageCode.includes('WDBC and CBIS-DDSM observations are not paired from the same individuals'),
  'multimodal.js must include canonical unpaired dataset limitation warning'
);

// 7. Verify branch disagreement and agreement panels
assert.ok(
  pageCode.includes('Branch Disagreement'),
  'multimodal.js must render prominent Branch Disagreement when branches differ'
);
assert.ok(
  pageCode.includes('Branch Agreement'),
  'multimodal.js must render Branch Agreement banner when branches match'
);

// 8. Verify advisor handoff structured context
assert.ok(
  pageCode.includes('bcai_advisor_context'),
  'multimodal.js must use bcai_advisor_context sessionStorage key'
);
assert.ok(
  pageCode.includes("analysis_type: 'fusion'"),
  'multimodal.js must set analysis_type to fusion in advisor handoff'
);

// 9. Verify report action
assert.ok(
  pageCode.includes('/predictions/${res.id}/report/') || pageCode.includes('reportService.open'),
  'multimodal.js must provide link or service action to view analysis report'
);

console.log('PASS: test_fusion_frontend_contract.js passed all contract assertions.');
