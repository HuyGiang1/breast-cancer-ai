import { ML_FEATURES } from '../config/ml-features.js';

/**
 * Normalizes header strings for safe comparison:
 * lowercase, trim, replace spaces and dashes with underscores.
 */
export function normalizeHeader(raw) {
  return String(raw || '')
    .trim()
    .toLowerCase()
    .replace(/[\s-]+/g, '_');
}

export const IGNORED_COLUMNS = new Set([
  'id',
  'diagnosis',
  'target',
  'label',
  'unnamed:_32',
  'unnamed_32',
]);

/**
 * Generates canonical 30-feature CSV template (headers only, no diagnosis).
 */
export function generateCsvTemplate() {
  return ML_FEATURES.join(',') + '\n';
}

/**
 * Generates a downloadable WDBC research demo CSV.
 * Contains exactly the canonical 30 WDBC features, with optional research sample ID.
 * Diagnosis is not included as a required model input.
 */
export function generateWdbcResearchDemoCsv(sampleValues, sampleId = null) {
  const headers = sampleId ? ['id', ...ML_FEATURES].join(',') : ML_FEATURES.join(',');
  const values = sampleId
    ? [sampleId, ...ML_FEATURES.map((feat) => sampleValues?.[feat] ?? 0)].join(',')
    : ML_FEATURES.map((feat) => sampleValues?.[feat] ?? 0).join(',');
  return `${headers}\n${values}\n`;
}

/**
 * Generates an example CSV with canonical benign research preset.
 * (Legacy helper preserved for backward compatibility).
 */
export function generateExampleCsv(sampleValues) {
  return generateWdbcResearchDemoCsv(sampleValues);
}

/**
 * Robust CSV line splitter supporting quoted values.
 */
export function splitCsvLine(line) {
  const entries = [];
  let current = '';
  let insideQuotes = false;

  for (let i = 0; i < line.length; i++) {
    const char = line[i];
    if (char === '"') {
      if (insideQuotes && line[i + 1] === '"') {
        current += '"';
        i++;
      } else {
        insideQuotes = !insideQuotes;
      }
    } else if (char === ',' && !insideQuotes) {
      entries.push(current.trim());
      current = '';
    } else {
      current += char;
    }
  }
  entries.push(current.trim());
  return entries;
}

/**
 * Parses CSV text and validates 30 required numerical features.
 * Returns parsed rows with row index, identifying info, values, and errors.
 */
export function parseClinicalCsv(csvText) {
  const trimmed = String(csvText || '').trim();
  if (!trimmed) {
    throw new Error('CSV file is empty. Please upload a valid CSV file.');
  }

  const lines = trimmed.split(/\r?\n/).filter((l) => l.trim().length > 0);
  if (lines.length < 2) {
    throw new Error('CSV must contain a header row and at least one data row.');
  }

  const rawHeaders = splitCsvLine(lines[0]);
  const headerMap = new Map(); // normalized -> column index
  const duplicateHeaders = [];

  rawHeaders.forEach((raw, idx) => {
    const norm = normalizeHeader(raw);
    if (!norm) return;
    if (headerMap.has(norm)) {
      duplicateHeaders.push(raw);
    } else {
      headerMap.set(norm, idx);
    }
  });

  if (duplicateHeaders.length > 0) {
    throw new Error(`Duplicate column headers detected: ${duplicateHeaders.join(', ')}`);
  }

  // Check missing required 30 features
  const missingFeatures = [];
  const featureColIndices = new Map();

  for (const feature of ML_FEATURES) {
    const normFeature = normalizeHeader(feature);
    if (headerMap.has(normFeature)) {
      featureColIndices.set(feature, headerMap.get(normFeature));
    } else {
      missingFeatures.push(feature);
    }
  }

  if (missingFeatures.length > 0) {
    throw new Error(
      `CSV is missing ${missingFeatures.length} required feature(s): ${missingFeatures.slice(0, 5).join(', ')}${missingFeatures.length > 5 ? '…' : ''}`
    );
  }

  // Check optional id column
  const idColIdx = headerMap.get('id') ?? -1;

  const parsedRows = [];

  for (let r = 1; r < lines.length; r++) {
    const cells = splitCsvLine(lines[r]);
    const rowErrors = [];
    const values = {};

    for (const feature of ML_FEATURES) {
      const colIdx = featureColIndices.get(feature);
      const rawVal = cells[colIdx];

      if (rawVal === undefined || rawVal === '') {
        rowErrors.push(`Field '${feature}' is blank.`);
        continue;
      }

      const num = Number(rawVal);
      if (Number.isNaN(num) || !Number.isFinite(num)) {
        rowErrors.push(`Field '${feature}' contains non-numeric value: "${rawVal}".`);
        continue;
      }

      if (num < 0) {
        rowErrors.push(`Field '${feature}' cannot be negative (${num}).`);
        continue;
      }

      values[feature] = num;
    }

    const rowId = idColIdx >= 0 ? cells[idColIdx] : null;

    parsedRows.push({
      rowNumber: r,
      id: rowId,
      values,
      valid: rowErrors.length === 0,
      errors: rowErrors,
      completedCount: Object.keys(values).length,
    });
  }

  return {
    isMultiRow: parsedRows.length > 1,
    rowCount: parsedRows.length,
    rows: parsedRows,
  };
}
