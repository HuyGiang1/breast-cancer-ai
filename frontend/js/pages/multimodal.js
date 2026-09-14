import { mountShell } from '../components/shell.js';
import { predictionService } from '../services/prediction.service.js';
import { patientService } from '../services/patient.service.js';
import { reportService } from '../services/report.service.js';
import { bindModalAccessibility } from '../components/workspace.js';
import { auth } from '../core/auth.js';
import {
  ML_GROUPS,
  ML_FEATURES,
  featureLabel,
  SAMPLES,
  GROUP_DESCRIPTIONS,
  WDBC_DEVELOPMENT_REFERENCE,
} from '../config/ml-features.js';
import {
  parseClinicalCsv,
  generateCsvTemplate,
  generateExampleCsv,
  generateWdbcResearchDemoCsv,
} from '../utils/clinical-csv.js';
import { featureSection, resultCard, collectFeatures } from '../components/analysis.js';

mountShell('Experimental Research Fusion');

const app = document.querySelector('#app');
const currentUser = auth.user();
const isDoctor = currentUser?.role === 'doctor';

const urlParams = new URLSearchParams(window.location.search);
const initialPatientId = urlParams.get('patient_id') || '';

// Internal Workstation State
const state = {
  // Structured ML Branch State
  inputs: Object.fromEntries(ML_FEATURES.map((f) => [f, ''])),
  outlierConfirmed: false,
  activeMlGroupTab: 'all',
  branch1InputMode: 'manual', // 'manual' | 'csv'
  branch1Notification: null, // { type: 'success'|'error', message: string } | null

  // Mammography DL Branch State
  file: null,
  objectUrl: null,
  previewMetadata: null, // { name, size, type, width, height }
  isPreset: false,
  presetType: null, // 'benign' | 'malignant'
  gradcamViewMode: 'side-by-side', // 'side-by-side' | 'original' | 'gradcam'

  // Shared Patient Context (Doctor Only)
  selectedPatientId: isDoctor && initialPatientId ? initialPatientId : '',
  patients: [],

  // Execution & Progress State
  isAnalyzing: false,
  stage: 'idle', // 'idle' | 'validating' | 'ml' | 'dl' | 'gradcam' | 'combining' | 'ai' | 'saving' | 'done' | 'error'
  result: null,
  errorMessage: null,

  // UI Modals
  modal: null, // 'csv' | 'ocr' | 'outlier' | null
  modalData: null,
  selectedCsvRowIndex: null,
  csvError: null,
  differsExpanded: false,
};

// Cleanup blob URLs to avoid memory leaks
function cleanupObjectUrl() {
  if (state.objectUrl) {
    URL.revokeObjectURL(state.objectUrl);
    state.objectUrl = null;
  }
}

// Helper: Escape HTML
function esc(str) {
  return String(str ?? '').replace(/[&<>"']/g, (c) => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;',
  }[c]));
}

// Format percent with 1 decimal
function formatPct(val) {
  if (val === undefined || val === null || Number.isNaN(Number(val))) return '—';
  return `${(Number(val) * 100).toFixed(1)}%`;
}

// Format raw number with 3 decimals
function formatDec(val) {
  if (val === undefined || val === null || Number.isNaN(Number(val))) return '—';
  return Number(val).toFixed(3);
}

// Compute reference state for a single field
function getFieldReferenceState(feature, rawValue) {
  if (rawValue === '' || rawValue === undefined || rawValue === null) {
    return { state: 'waiting', label: 'Awaiting input', class: 'status-waiting' };
  }
  const val = Number(rawValue);
  if (Number.isNaN(val)) {
    return { state: 'invalid', label: 'Non-numeric', class: 'status-outside' };
  }
  if (val < 0) {
    return { state: 'invalid', label: 'Cannot be negative', class: 'status-outside' };
  }

  const ref = WDBC_DEVELOPMENT_REFERENCE[feature];
  if (!ref) {
    return { state: 'common', label: 'Input set', class: 'status-common' };
  }

  if (val < ref.min || val > ref.max) {
    return {
      state: 'outside',
      label: `Outside observed (${val < ref.min ? `< ${ref.min}` : `> ${ref.max}`})`,
      class: 'status-outside',
      min: ref.min,
      max: ref.max,
    };
  }
  if (val < ref.p01 || val > ref.p99) {
    return { state: 'extreme', label: 'Extreme (outside P1–P99)', class: 'status-extreme' };
  }
  if (val < ref.p05 || val > ref.p95) {
    return { state: 'unusual', label: 'Unusual (outside P5–P95)', class: 'status-unusual' };
  }
  return { state: 'common', label: 'Common range (P5–P95)', class: 'status-common' };
}

// Compute aggregate input quality metrics
function computeInputQuality() {
  let completed = 0;
  let common = 0;
  let unusual = 0;
  let extreme = 0;
  let outside = 0;
  const outliers = [];

  for (const feat of ML_FEATURES) {
    const val = state.inputs[feat];
    if (val !== '' && !Number.isNaN(Number(val))) {
      completed++;
      const refState = getFieldReferenceState(feat, val);
      if (refState.state === 'common') common++;
      else if (refState.state === 'unusual') unusual++;
      else if (refState.state === 'extreme') extreme++;
      else if (refState.state === 'outside') {
        outside++;
        outliers.push({ feature: feat, value: Number(val), label: featureLabel(feat), ...refState });
      }
    }
  }

  return { completed, common, unusual, extreme, outside, outliers, isComplete: completed === 30 };
}

// Execution Stages configuration
const STAGES = [
  { id: 'validating', label: 'Validating Structured features (30/30) and Mammography image' },
  { id: 'ml', label: 'Running frozen Logistic Regression on WDBC features (raw cutoff 0.36)' },
  { id: 'dl', label: 'Running frozen EfficientNet-B0 on Mammography image (raw cutoff 0.515)' },
  { id: 'gradcam', label: 'Generating Grad-CAM attention heatmap on top_conv' },
  { id: 'combining', label: 'Computing unvalidated 40/60 raw combination heuristic' },
  { id: 'ai', label: 'Generating contextual educational guidance' },
  { id: 'saving', label: 'Persisting analysis record to research history' },
];

function getStageStatus(stageId) {
  const stageOrder = ['idle', 'validating', 'ml', 'dl', 'gradcam', 'combining', 'ai', 'saving', 'done'];
  const currentIndex = stageOrder.indexOf(state.stage);
  const thisIndex = stageOrder.indexOf(stageId);

  if (state.stage === 'error') {
    return { class: 'error', icon: '⚠️' };
  }
  if (currentIndex > thisIndex || state.stage === 'done') {
    return { class: 'completed', icon: '✓' };
  }
  if (currentIndex === thisIndex) {
    return { class: 'active', icon: '⏳' };
  }
  return { class: 'waiting', icon: '○' };
}

// File selection handler for Mammography branch
async function handleFileSelected(file, isPreset = false, presetType = null) {
  state.errorMessage = null;

  if (!file) return;

  if (file.size === 0) {
    state.errorMessage = 'The selected file is empty (0 bytes). Please choose a valid image.';
    render();
    return;
  }

  // Client-side file size limit check (20 MB)
  if (file.size > 20 * 1024 * 1024) {
    state.errorMessage = 'Image upload is too large. Maximum supported file size is 20 MB.';
    render();
    return;
  }

  const validTypes = ['image/jpeg', 'image/png'];
  const ext = file.name.split('.').pop()?.toLowerCase();
  const validExts = ['jpg', 'jpeg', 'png'];

  if (!validTypes.includes(file.type) && !validExts.includes(ext)) {
    state.errorMessage = 'Unsupported file format. Please upload a standard JPEG or PNG mammography image.';
    render();
    return;
  }

  cleanupObjectUrl();
  const objUrl = URL.createObjectURL(file);

  try {
    const dimensions = await new Promise((resolve) => {
      const img = new Image();
      img.onload = () => resolve({ width: img.naturalWidth, height: img.naturalHeight });
      img.onerror = () => resolve({ width: null, height: null });
      img.src = objUrl;
    });

    state.file = file;
    state.objectUrl = objUrl;
    state.isPreset = isPreset;
    state.presetType = presetType;
    state.previewMetadata = {
      name: file.name,
      size: file.size,
      type: file.type || `image/${ext}`,
      width: dimensions.width,
      height: dimensions.height,
    };
  } catch {
    state.errorMessage = 'Failed to inspect mammogram image dimensions.';
  }

  render();
}

// Load demo presets for Mammography branch
async function loadMammogramDemoPreset(type) {
  const assetPath =
    type === 'malignant'
      ? '/assets/demo-images/demo-malignant-mammogram.png'
      : '/assets/demo-images/demo-benign-mammogram.png';

  try {
    const res = await fetch(assetPath);
    if (!res.ok) throw new Error(`Demo image asset not found (${res.status})`);
    const blob = await res.blob();
    const filename = type === 'malignant' ? 'demo-malignant-mammogram.png' : 'demo-benign-mammogram.png';
    const file = new File([blob], filename, { type: 'image/png' });
    await handleFileSelected(file, true, type);
  } catch (err) {
    state.errorMessage = `Could not load ${type} demo preset: ${err.message}`;
    render();
  }
}

// Load sample preset for Structured ML branch
function loadStructuredSample(type) {
  const sample = SAMPLES[type];
  if (!sample) return;
  for (const feat of ML_FEATURES) {
    state.inputs[feat] = sample[feat] !== undefined ? String(sample[feat]) : '';
  }
  state.outlierConfirmed = false;
  state.branch1Notification = null;
  state.errorMessage = null;
  render();
}

// Clear structured inputs
function clearStructuredInputs() {
  for (const feat of ML_FEATURES) {
    state.inputs[feat] = '';
  }
  state.outlierConfirmed = false;
  state.branch1Notification = null;
  state.errorMessage = null;
  render();
}

// Reset the entire Fusion workstation
function resetFusionWorkstation() {
  clearStructuredInputs();
  cleanupObjectUrl();
  state.file = null;
  state.previewMetadata = null;
  state.isPreset = false;
  state.presetType = null;
  state.result = null;
  state.errorMessage = null;
  state.stage = 'idle';
  state.isAnalyzing = false;
  state.modal = null;
  state.modalData = null;
  state.differsExpanded = false;
  render();
}

// Ask AI Guide handoff
function handoffToAdvisor() {
  if (!state.result) return;
  const res = state.result;
  const ml = res.ml_result || {};
  const dl = res.dl_result || {};

  const advisorContext = {
    analysis_type: 'fusion',
    ml_model: ml.model_name || 'Logistic Regression',
    ml_raw_probability: ml.raw_probability ?? ml.probability ?? 0,
    ml_threshold: ml.decision_threshold ?? 0.36,
    ml_classification: ml.diagnosis || 'Unknown',
    dl_model: dl.model_name || 'EfficientNet-B0',
    dl_raw_probability: dl.raw_probability ?? 0,
    dl_threshold: dl.decision_threshold ?? 0.515,
    dl_classification: dl.diagnosis || 'Unknown',
    dl_calibrated_probability: dl.calibrated_probability ?? dl.probability ?? 0,
    gradcam_status: dl.explanation_status || 'unavailable',
    combined_malignant_score: res.combined_malignant_score ?? res.combined_confidence ?? 0,
    combined_threshold: res.combined_threshold ?? 0.5,
    branch_agreement: res.branch_agreement ?? (ml.diagnosis === dl.diagnosis),
    branches_unpaired: true,
    prediction_id: res.id || null,
  };

  sessionStorage.setItem('bcai_advisor_context', JSON.stringify(advisorContext));
  window.location.href = '/pages/advisor.html';
}

// Main execution routine
async function executeFusion() {
  state.errorMessage = null;

  // 1. Verify structured branch completeness
  const quality = computeInputQuality();
  if (!quality.isComplete) {
    state.errorMessage = `Structured branch is incomplete (${quality.completed}/30 features). All 30 WDBC features are required.`;
    render();
    return;
  }

  // 2. Outlier safeguard check
  if (quality.outliers.length > 0 && !state.outlierConfirmed) {
    state.modal = 'outlier';
    state.modalData = quality.outliers;
    render();
    return;
  }

  // 3. Verify mammography image selection
  if (!state.file) {
    state.errorMessage = 'A valid mammography image is required to run Experimental Fusion.';
    render();
    return;
  }

  // Prepare payload
  const clinicalData = {};
  for (const feat of ML_FEATURES) {
    clinicalData[feat] = Number(state.inputs[feat]);
  }

  state.isAnalyzing = true;
  state.result = null;
  state.stage = 'validating';
  render();

  try {
    await new Promise((r) => setTimeout(r, 200));
    state.stage = 'ml';
    render();

    await new Promise((r) => setTimeout(r, 200));
    state.stage = 'dl';
    render();

    await new Promise((r) => setTimeout(r, 200));
    state.stage = 'gradcam';
    render();

    await new Promise((r) => setTimeout(r, 150));
    state.stage = 'combining';
    render();

    // Call single endpoint: include_explanation = true
    const response = await predictionService.multimodal({
      clinicalData,
      imageFile: state.file,
      patientId: state.selectedPatientId || undefined,
      includeExplanation: true,
    });

    state.stage = 'ai';
    render();
    await new Promise((r) => setTimeout(r, 150));

    state.stage = 'saving';
    render();
    await new Promise((r) => setTimeout(r, 150));

    state.result = response;
    state.stage = 'done';
  } catch (err) {
    state.stage = 'error';
    state.errorMessage = err.message || 'Experimental Fusion analysis failed.';
  } finally {
    state.isAnalyzing = false;
    render();

    // Scroll to results if present
    if (state.result) {
      setTimeout(() => {
        const resEl = document.querySelector('#fusionResultsArea');
        resEl?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, 100);
    }
  }
}

// ---------------------------------------------------------------------------
// HTML Renderers
// ---------------------------------------------------------------------------

function renderHero() {
  return `
    <header class="fusion-hero">
      <div class="fusion-hero-eyebrow">
        <span>Dual-Branch Research Workstation</span>
      </div>
      <h1>Experimental Research Fusion</h1>
      <p class="fusion-hero-desc">
        Two independent research branches combined with an unvalidated software heuristic.
        Branch 1 evaluates nuclear morphology features from FNA cytology (WDBC), and Branch 2 evaluates
        full mammography images (CBIS-DDSM). The two datasets are entirely unpaired.
      </p>
      <div class="fusion-hero-specs">
        <span class="fusion-spec-pill">Branch 1: <strong>WDBC FNA (30 Features)</strong> · 40% Weight</span>
        <span class="fusion-spec-pill">Branch 2: <strong>CBIS-DDSM (EfficientNet-B0)</strong> · 60% Weight</span>
        <span class="fusion-spec-pill">Decision Midpoint: <strong>0.50 (Software Midpoint)</strong></span>
        <span class="fusion-spec-pill">Contract: <strong>Raw Branch Probabilities Only</strong></span>
      </div>
    </header>

    <aside class="fusion-unpaired-banner" role="note">
      <div class="fusion-unpaired-icon">⚠️</div>
      <div class="fusion-unpaired-body">
        <h3>Unpaired Dataset Scientific Contract</h3>
        <p>
          WDBC and CBIS-DDSM observations are not paired from the same individuals. This page demonstrates
          software-level output combination, not a validated multimodal medical model. If the two models produce
          conflicting outputs, the weighted combined score cannot resolve the disagreement as a clinical diagnosis.
        </p>
      </div>
    </aside>
  `;
}

function renderDoctorPatientBar() {
  if (!isDoctor) return '';

  const currentPatient = state.patients.find((p) => String(p.id) === String(state.selectedPatientId));
  const patientLabel = currentPatient
    ? `${esc(currentPatient.full_name)} (ID: #${currentPatient.id})`
    : 'No patient selected (Unassigned research run)';

  return `
    <section class="doctor-patient-bar" aria-label="Shared Patient Context">
      <div class="doctor-patient-info">
        <span class="doctor-patient-badge">Analysis Subject</span>
        <span>Patient: <strong>${patientLabel}</strong></span>
      </div>
      <div style="display:flex;gap:8px;align-items:center;">
        <select id="doctorPatientSelect" class="v2-field" style="padding:6px 12px;font-size:0.85rem;min-width:220px;">
          <option value="">-- Select Patient --</option>
          ${state.patients
            .map(
              (p) =>
                `<option value="${p.id}" ${String(p.id) === String(state.selectedPatientId) ? 'selected' : ''}>
                  ${esc(p.full_name)} (DOB: ${p.date_of_birth || 'N/A'})
                </option>`
            )
            .join('')}
        </select>
        ${
          currentPatient
            ? `<a href="/pages/patient-detail.html?id=${currentPatient.id}" class="v2-button secondary btn-xs" style="text-decoration:none;">View Patient</a>`
            : ''
        }
      </div>
    </section>
  `;
}

function renderStructuredBranch() {
  const quality = computeInputQuality();
  const groups = state.activeMlGroupTab === 'all'
    ? ML_GROUPS
    : ML_GROUPS.filter(([title]) => title.toLowerCase().includes(state.activeMlGroupTab));

  return `
    <article class="fusion-branch-card" id="fusionStructuredBranch">
      <header class="fusion-branch-header">
        <div class="fusion-branch-title-group">
          <span class="fusion-branch-step">Branch 1 · Study A</span>
          <h2 class="fusion-branch-title">Structured FNA Cytology Branch</h2>
        </div>
        <span class="fusion-weight-badge weight-40">40% Weight</span>
      </header>

      <div class="fusion-branch-meta">
        <span>Dataset: <strong>WDBC</strong></span>
        <span>Model: <strong>Logistic Regression</strong></span>
        <span>Frozen Cutoff: <strong>Raw ≥ 0.36</strong></span>
      </div>

      <div class="fusion-toolbar" style="display:flex;flex-direction:column;gap:10px;padding:12px;background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;">
        <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;">
          <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;">
            <span style="font-size:0.82rem;font-weight:700;color:#334155;">Research Demos:</span>
            <button type="button" class="v2-button secondary btn-xs" id="loadMlBenignBtn" title="Load Benign WDBC Sample (#8510426)">Benign WDBC Sample</button>
            <button type="button" class="v2-button secondary btn-xs" id="loadMlMalignantBtn" title="Load Malignant WDBC Sample (#842302)">Malignant WDBC Sample</button>
          </div>
          <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;">
            <span style="font-size:0.82rem;font-weight:700;color:#334155;">CSV Demos:</span>
            <button type="button" class="v2-button ghost btn-xs" id="downloadBenignCsvBtn" title="Download Benign WDBC CSV demo">Download Benign CSV</button>
            <button type="button" class="v2-button ghost btn-xs" id="downloadMalignantCsvBtn" title="Download Malignant WDBC CSV demo">Download Malignant CSV</button>
          </div>
        </div>
        <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;border-top:1px solid #edf2f7;padding-top:8px;">
          <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;">
            <span style="font-size:0.82rem;font-weight:700;color:#1e293b;">Input method:</span>
            <button type="button" class="v2-button ${state.branch1InputMode === 'manual' ? 'primary' : 'secondary'} btn-xs" id="branch1ManualBtn" title="Direct manual entry in 30 feature fields">Manual Entry</button>
            <button type="button" class="v2-button secondary btn-xs" id="openCsvModalBtn" title="Import 30 WDBC features from CSV">Import WDBC CSV</button>
            <button type="button" class="v2-button secondary btn-xs" id="openOcrModalBtn" title="Extract features from lab report photo">OCR Report</button>
          </div>
          <div>
            <button type="button" class="v2-button ghost btn-xs" id="clearMlBtn" title="Clear all 30 fields" style="color:#b91c1c;">Clear</button>
          </div>
        </div>
      </div>

      ${state.branch1Notification ? `
        <div class="fusion-branch-alert" id="branch1Notification" style="display:flex;align-items:center;justify-content:space-between;background:#ecfdf5;border:1px solid #a7f3d0;border-radius:6px;padding:8px 12px;font-size:0.84rem;color:#065f46;margin-top:-2px;">
          <span style="display:flex;align-items:center;gap:6px;">
            <span style="font-weight:700;">✓</span>
            <span id="branch1NotificationMsg">${esc(state.branch1Notification.message)}</span>
          </span>
          <button type="button" id="dismissBranch1NotificationBtn" style="background:none;border:none;cursor:pointer;color:#065f46;font-size:1.1rem;line-height:1;padding:0 4px;" aria-label="Dismiss">&times;</button>
        </div>
      ` : ''}

      <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;">
        <span class="fusion-quality-pill ${quality.isComplete ? 'complete' : ''}">
          ${quality.completed} / 30 Features Completed
        </span>
        <div style="font-size:0.78rem;color:#64748b;display:flex;gap:10px;">
          <span style="color:#15803d;">● ${quality.common} Common</span>
          <span style="color:#b45309;">● ${quality.unusual} Unusual</span>
          <span style="color:#c2410c;">● ${quality.extreme} Extreme</span>
          ${quality.outside > 0 ? `<span style="color:#b91c1c;font-weight:700;">● ${quality.outside} Outside</span>` : ''}
        </div>
      </div>

      <!-- Feature Group Filter Tabs -->
      <div style="display:flex;gap:6px;border-bottom:1px solid #e2e8f0;padding-bottom:6px;">
        <button type="button" class="v2-button ${state.activeMlGroupTab === 'all' ? 'primary' : 'ghost'} btn-xs" data-group-tab="all">All (30)</button>
        <button type="button" class="v2-button ${state.activeMlGroupTab === 'mean' ? 'primary' : 'ghost'} btn-xs" data-group-tab="mean">Mean (10)</button>
        <button type="button" class="v2-button ${state.activeMlGroupTab === 'se' ? 'primary' : 'ghost'} btn-xs" data-group-tab="se">SE (10)</button>
        <button type="button" class="v2-button ${state.activeMlGroupTab === 'worst' ? 'primary' : 'ghost'} btn-xs" data-group-tab="worst">Worst (10)</button>
      </div>

      <!-- 30 Interactive Feature Inputs -->
      <div class="fusion-features-accordion">
        ${groups
          .map(([groupTitle, features]) => `
            <div class="fusion-group-box">
              <div class="fusion-group-heading">
                <span>${esc(groupTitle)}</span>
                <span style="font-size:0.75rem;font-weight:400;color:#64748b;">${GROUP_DESCRIPTIONS[groupTitle] || ''}</span>
              </div>
              <div class="fusion-fields-grid">
                ${features
                  .map((feat) => {
                    const val = state.inputs[feat];
                    const ref = WDBC_DEVELOPMENT_REFERENCE[feat];
                    const status = getFieldReferenceState(feat, val);
                    return `
                      <div class="fusion-field-cell">
                        <label class="fusion-field-label" for="input_${feat}">
                          <span>${esc(featureLabel(feat))}</span>
                          <span class="${status.class}" style="font-size:0.68rem;">${ref ? `[${ref.min}–${ref.max}]` : ''}</span>
                        </label>
                        <input
                          type="number"
                          step="any"
                          id="input_${feat}"
                          class="fusion-field-input"
                          data-feature="${feat}"
                          value="${val}"
                          placeholder="e.g. ${ref?.mean ?? 0}"
                        />
                        <span class="fusion-field-status ${status.class}">${status.label}</span>
                      </div>
                    `;
                  })
                  .join('')}
              </div>
            </div>
          `)
          .join('')}
      </div>
    </article>
  `;
}

function renderMammographyBranch() {
  const hasImage = Boolean(state.file && state.objectUrl);
  const meta = state.previewMetadata;

  return `
    <article class="fusion-branch-card" id="fusionMammographyBranch">
      <header class="fusion-branch-header">
        <div class="fusion-branch-title-group">
          <span class="fusion-branch-step">Branch 2 · Study B</span>
          <h2 class="fusion-branch-title">Mammography Image Branch</h2>
        </div>
        <span class="fusion-weight-badge weight-60">60% Weight</span>
      </header>

      <div class="fusion-branch-meta">
        <span>Dataset: <strong>CBIS-DDSM</strong></span>
        <span>Model: <strong>EfficientNet-B0 (224×224×3)</strong></span>
        <span>Frozen Cutoff: <strong>Raw ≥ 0.515</strong></span>
      </div>

      <div class="fusion-toolbar" style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;padding:12px;background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;">
        <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;">
          <span style="font-size:0.82rem;font-weight:700;color:#334155;">Research Demos:</span>
          <button type="button" class="v2-button secondary btn-xs" id="loadDlBenignBtn" title="Load Benign Mammogram Demo">Benign Mammogram</button>
          <button type="button" class="v2-button secondary btn-xs" id="loadDlMalignantBtn" title="Load Malignant Mammogram Demo">Malignant Mammogram</button>
        </div>
        <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;">
          <span style="font-size:0.82rem;font-weight:700;color:#334155;">Your Image:</span>
          <button type="button" class="v2-button secondary btn-xs" id="uploadMammogramToolbarBtn" title="Upload custom mammogram image">Upload Mammogram</button>
          ${
            hasImage
              ? `<button type="button" class="v2-button ghost btn-xs" id="removeImageBtn" style="color:#b91c1c;">Remove Image</button>`
              : ''
          }
        </div>
      </div>

      ${
        !hasImage
          ? `
            <div class="fusion-dropzone-box" id="mammogramDropzone" tabindex="0" role="button" aria-label="Upload mammogram image">
              <div class="fusion-dropzone-icon">📷</div>
              <h3 class="fusion-dropzone-title">Drag & drop mammography image here</h3>
              <p class="fusion-dropzone-sub">Supports JPEG and PNG formats (224×224 normalized for inference, max 20 MB)</p>
              <button type="button" class="v2-button secondary btn-sm" id="selectImageTriggerBtn">Upload Mammogram</button>
              <input type="file" id="mammogramFileInput" accept="image/jpeg,image/png" style="display:none;" />
            </div>
          `
          : `
            <div class="fusion-image-preview-card">
              <div class="fusion-preview-canvas-wrap">
                <img src="${state.objectUrl}" alt="Selected mammogram preview" id="mammogramPreviewImg" />
              </div>
              <div class="fusion-preview-meta-row">
                <div>
                  <strong style="color:#ffffff;">${esc(meta?.name)}</strong>
                  <span> · ${(Number(meta?.size || 0) / 1024).toFixed(1)} KB</span>
                  ${meta?.width ? `<span> · ${meta.width} × ${meta.height} px</span>` : ''}
                </div>
                <div class="fusion-preview-actions">
                  <button type="button" class="v2-button secondary btn-xs" id="replaceImageBtn">Replace</button>
                  <button type="button" class="v2-button ghost btn-xs" id="removeImageBtn2" style="color:#f87171;">Remove</button>
                </div>
              </div>
            </div>
          `
      }

      <div style="font-size:0.8rem;color:#64748b;background:#f8fafc;padding:10px 12px;border-radius:6px;border:1px solid #f1f5f9;">
        <strong>Note:</strong> Explainability (Grad-CAM on <code>top_conv</code>) will be generated live during execution.
      </div>
    </article>
  `;
}

function renderExecutionHub() {
  const quality = computeInputQuality();
  const hasImage = Boolean(state.file);
  const isReady = quality.isComplete && hasImage && !state.isAnalyzing;

  return `
    <section class="fusion-hub-card" aria-label="Execution Convergence Hub">
      <div class="fusion-hub-header">
        <h2>Converging Combination Hub</h2>
        <p>Both independent evidence streams must be verified before evaluating the 40/60 software heuristic.</p>
      </div>

      <div class="fusion-precheck-summary">
        <div class="fusion-precheck-item ${quality.isComplete ? 'valid' : 'invalid'}">
          <span>${quality.isComplete ? '✓' : '✗'}</span>
          <span>Branch 1: ${quality.isComplete ? 'Structured Data Complete (30/30)' : `Incomplete (${quality.completed}/30)`}</span>
        </div>
        <div class="fusion-precheck-item ${hasImage ? 'valid' : 'invalid'}">
          <span>${hasImage ? '✓' : '✗'}</span>
          <span>Branch 2: ${hasImage ? `Mammogram Selected (${esc(state.file?.name)})` : 'Mammogram Image Required'}</span>
        </div>
      </div>

      ${
        state.errorMessage
          ? `<div class="v2-alert error" style="width:100%;max-width:720px;">${esc(state.errorMessage)}</div>`
          : ''
      }

      ${
        state.isAnalyzing
          ? `
            <div class="fusion-stages-card" style="width:100%;max-width:720px;">
              <h3 style="margin:0;font-size:0.95rem;color:#0f172a;">Executing Experimental Fusion Pipeline…</h3>
              <div class="fusion-stages-list">
                ${STAGES.map((s) => {
                  const status = getStageStatus(s.id);
                  return `
                    <div class="fusion-stage-row ${status.class}">
                      <span>${status.icon}</span>
                      <span>${s.label}</span>
                    </div>
                  `;
                }).join('')}
              </div>
            </div>
          `
          : `
            <button
              type="button"
              id="runFusionBtn"
              class="v2-button primary fusion-run-button"
              ${!isReady ? 'disabled' : ''}
            >
              Run Experimental Fusion
            </button>
          `
      }
    </section>
  `;
}

function renderResults() {
  if (!state.result) return '';

  const res = state.result;
  const ml = res.ml_result || {};
  const dl = res.dl_result || {};

  const mlRaw = Number(ml.raw_probability ?? ml.probability ?? 0);
  const dlRaw = Number(dl.raw_probability ?? 0);
  const dlCalibrated = Number(dl.calibrated_probability ?? dl.probability ?? 0);

  // Exact 40/60 math breakdown
  const mlWeighted = mlRaw * 0.4;
  const dlWeighted = dlRaw * 0.6;
  const combinedScore = Number(res.combined_malignant_score ?? (mlWeighted + dlWeighted));

  const isMalignantSide = combinedScore >= 0.5;
  const agreement = res.branch_agreement ?? (ml.diagnosis === dl.diagnosis);

  return `
    <section class="fusion-results-workspace" id="fusionResultsArea" aria-label="Fusion Analysis Results">
      <!-- 1. Prominent Branch Disagreement or Agreement Banner -->
      ${
        !agreement
          ? `
            <div class="fusion-disagreement-card">
              <span class="fusion-disagreement-badge">⚠️ Branch Disagreement</span>
              <h2>Branch Disagreement: Conflicting Independent Model Outputs</h2>
              <p>
                The structured cytology branch and mammography branch produced different model classifications.
                Because they were trained on separate, unpaired datasets (WDBC and CBIS-DDSM), the experimental
                weighted score cannot resolve this disagreement as a validated clinical diagnosis.
              </p>
              <div class="fusion-disagreement-reasons">
                <strong>Independent Model Classifications:</strong><br>
                • Structured FNA (WDBC): <strong>${esc(ml.diagnosis)}</strong> (Raw probability: ${formatPct(mlRaw)} vs cutoff 0.36)<br>
                • Mammography Image (CBIS-DDSM): <strong>${esc(dl.diagnosis)}</strong> (Raw probability: ${formatPct(dlRaw)} vs cutoff 0.515)<br>
                <em>The combined number below is visually secondary and must not overrule this disagreement.</em>
              </div>
            </div>
          `
          : `
            <div class="fusion-agreement-card">
              <span class="fusion-agreement-badge">✓ Branch Agreement</span>
              <h2>Both Independent Research Branches Produced ${esc(ml.diagnosis)} Classification</h2>
              <p>
                Both independent research branches produced the same model-side class (${esc(ml.diagnosis)}).
                However, agreement does not validate the combined result as a clinical diagnosis because observations are unpaired.
              </p>
            </div>
          `
      }

      <!-- 2. Transparent Mathematical Formula Card -->
      <div class="fusion-formula-card">
        <h3>
          <span>Mathematical Combination Visualizer</span>
          <span style="font-size:0.75rem;font-weight:500;color:#64748b;">Explicit Raw Probability Inputs</span>
        </h3>
        <div class="fusion-formula-grid">
          <!-- ML Box -->
          <div class="fusion-formula-box">
            <span class="fusion-formula-label">Structured ML Branch (40%)</span>
            <span class="fusion-formula-math">${formatDec(mlRaw)} × 0.40</span>
            <span class="fusion-formula-result">= ${formatDec(mlWeighted)}</span>
          </div>

          <div class="fusion-formula-operator">+</div>

          <!-- DL Box -->
          <div class="fusion-formula-box">
            <span class="fusion-formula-label">Mammography DL Branch (60%)</span>
            <span class="fusion-formula-math">${formatDec(dlRaw)} × 0.60</span>
            <span class="fusion-formula-result">= ${formatDec(dlWeighted)}</span>
          </div>

          <div class="fusion-formula-operator">=</div>

          <!-- Final Combined Box -->
          <div class="fusion-formula-box fusion-formula-final">
            <span class="fusion-formula-label">Experimental Combined Score</span>
            <span class="fusion-formula-math" style="font-size:1.3rem;color:#0369a1;">${formatDec(combinedScore)}</span>
            <span class="fusion-formula-result" style="font-weight:700;">(${formatPct(combinedScore)})</span>
          </div>
        </div>
        <p class="fusion-formula-disclaimer">
          * Note: These weights (40% ML / 60% DL) are an experimental software choice, not learned multimodal parameters.
          The formula strictly consumes raw model outputs; the Platt-calibrated DL probability (${formatPct(dlCalibrated)}) is excluded.
        </p>
      </div>

      <!-- 3. Combined Score Hero -->
      <div class="fusion-combined-card">
        <span class="fusion-combined-eyebrow">Experimental Software Demonstration</span>
        <div class="fusion-combined-score-num">${formatPct(combinedScore)}</div>
        <div class="fusion-combined-indication ${isMalignantSide ? 'malignant-side' : 'benign-side'}">
          <span>Experimental heuristic indication:</span>
          <strong>${isMalignantSide ? 'Malignant-side indication' : 'Benign-side indication'}</strong>
        </div>
        <p class="fusion-midpoint-disclaimer">
          0.50 is the software decision midpoint for this experimental combination and has not been validated as a clinical threshold.
        </p>
      </div>

      <!-- 4. Deep-Dive Independent Branch Results -->
      <div class="fusion-branches-deepdive">
        <!-- ML Branch Independent Result -->
        <div class="fusion-deepdive-card">
          <div class="fusion-deepdive-header">
            <div>
              <span class="fusion-branch-step">Branch 1 Evidence</span>
              <h3 class="fusion-deepdive-title">Logistic Regression (WDBC)</h3>
            </div>
            <span class="v2-badge ${ml.diagnosis === 'Malignant' ? 'error' : 'success'}">${esc(ml.diagnosis)}</span>
          </div>

          <div class="fusion-deepdive-meta-list">
            <div class="fusion-deepdive-meta-row">
              <span>Raw Malignant Probability:</span>
              <span><strong>${formatPct(mlRaw)}</strong> (${formatDec(mlRaw)})</span>
            </div>
            <div class="fusion-deepdive-meta-row">
              <span>Decision Threshold (Raw):</span>
              <span>≥ 0.360</span>
            </div>
            <div class="fusion-deepdive-meta-row">
              <span>Model Classification:</span>
              <span>${esc(ml.diagnosis)}</span>
            </div>
            <div class="fusion-deepdive-meta-row">
              <span>Feature Modality:</span>
              <span>FNA Nuclear Morphology (30 inputs)</span>
            </div>
          </div>

          ${
            ml.top_features && ml.top_features.length > 0
              ? `
                <div style="margin-top:8px;">
                  <strong style="font-size:0.82rem;color:#334155;">Key Influential Features:</strong>
                  <div class="fusion-top-features" style="margin-top:6px;">
                    ${ml.top_features.slice(0, 5).map((f) => `
                      <div class="fusion-feature-row">
                        <span>${esc(featureLabel(f.feature))}</span>
                        <span style="font-weight:600;">${f.value !== undefined ? Number(f.value).toFixed(2) : ''}</span>
                      </div>
                    `).join('')}
                  </div>
                </div>
              `
              : ''
          }
        </div>

        <!-- DL Branch Independent Result -->
        <div class="fusion-deepdive-card">
          <div class="fusion-deepdive-header">
            <div>
              <span class="fusion-branch-step">Branch 2 Evidence</span>
              <h3 class="fusion-deepdive-title">EfficientNet-B0 (CBIS-DDSM)</h3>
            </div>
            <span class="v2-badge ${dl.diagnosis === 'Malignant' ? 'error' : 'success'}">${esc(dl.diagnosis)}</span>
          </div>

          <div class="fusion-deepdive-meta-list">
            <div class="fusion-deepdive-meta-row">
              <span>Raw Malignant Probability:</span>
              <span><strong>${formatPct(dlRaw)}</strong> (${formatDec(dlRaw)})</span>
            </div>
            <div class="fusion-deepdive-meta-row">
              <span>Decision Threshold (Raw):</span>
              <span>≥ 0.515</span>
            </div>
            <div class="fusion-deepdive-meta-row">
              <span>Calibrated Probability (Platt):</span>
              <span>${formatPct(dlCalibrated)} <em style="font-size:0.75rem;color:#64748b;">(Display reliability only)</em></span>
            </div>
            <div class="fusion-deepdive-meta-row">
              <span>Grad-CAM Attention Status:</span>
              <span>${dl.explanation_status === 'available' ? '✓ Generated on top_conv' : 'Unavailable'}</span>
            </div>
          </div>

          <!-- Grad-CAM Inspection Viewer -->
          ${
            dl.explanation_image
              ? `
                <div class="fusion-gradcam-box">
                  <div class="fusion-gradcam-switcher">
                    <button type="button" class="v2-button ${state.gradcamViewMode === 'side-by-side' ? 'primary' : 'secondary'} btn-xs" data-cam-mode="side-by-side">Side-by-Side</button>
                    <button type="button" class="v2-button ${state.gradcamViewMode === 'original' ? 'primary' : 'secondary'} btn-xs" data-cam-mode="original">Original</button>
                    <button type="button" class="v2-button ${state.gradcamViewMode === 'gradcam' ? 'primary' : 'secondary'} btn-xs" data-cam-mode="gradcam">Heatmap Overlay</button>
                  </div>

                  <div class="fusion-gradcam-display">
                    ${
                      state.gradcamViewMode === 'side-by-side'
                        ? `
                          <div style="display:flex;gap:4px;width:100%;height:100%;">
                            <img src="${state.objectUrl}" alt="Original mammogram" style="width:50%;object-fit:contain;" />
                            <img src="${dl.explanation_image}" alt="Grad-CAM overlay" style="width:50%;object-fit:contain;" />
                          </div>
                        `
                        : state.gradcamViewMode === 'original'
                        ? `<img src="${state.objectUrl}" alt="Original mammogram" />`
                        : `<img src="${dl.explanation_image}" alt="Grad-CAM heatmap overlay" />`
                    }
                  </div>
                  <span style="font-size:0.72rem;color:#64748b;text-align:center;">
                    Grad-CAM highlights broad model-attention regions. It does not establish lesion borders.
                  </span>
                </div>
              `
              : `<p style="font-size:0.8rem;color:#64748b;font-style:italic;">Grad-CAM explanation visualization is not available for this run.</p>`
          }
        </div>
      </div>

      <!-- 5. Expandable: Why can these results differ? -->
      <div class="fusion-differ-box">
        <div class="fusion-differ-toggle" id="toggleDiffersBtn">
          <span>Why can these results differ?</span>
          <span>${state.differsExpanded ? '▲ Collapse' : '▼ Expand'}</span>
        </div>
        ${
          state.differsExpanded
            ? `
              <div class="fusion-differ-content">
                <p>
                  It is scientifically expected that the Structured ML and Mammography DL branches may occasionally arrive at
                  different classifications:
                </p>
                <div class="fusion-differ-grid">
                  <div class="fusion-differ-col">
                    <h4>1. Distinct Biological Modalities</h4>
                    <p>
                      The Structured branch inspects microscopic nuclear morphology parameters (e.g., radius, concavity, texture)
                      extracted from fine-needle aspirates (FNA). The Mammography branch inspects macroscopic tissue density patterns,
                      calcifications, and masses on 2D digital projection radiographs.
                    </p>
                  </div>
                  <div class="fusion-differ-col">
                    <h4>2. Unpaired Patient Populations</h4>
                    <p>
                      The WDBC dataset (Wisconsin) and CBIS-DDSM dataset (Curated Breast Imaging Subset of DDSM) were collected
                      from completely different clinical cohorts in different eras with different screening protocols. There was no
                      joint multimodal training.
                    </p>
                  </div>
                </div>
              </div>
            `
            : ''
        }
      </div>

      <!-- 6. AI Educational Guidance -->
      <div class="fusion-ai-card">
        <div class="fusion-ai-header">
          <h3 class="fusion-ai-title">
            <span>AI Educational Guidance</span>
          </h3>
          <div style="font-size:0.75rem;color:#64748b;">
            <span>Provider: <strong>${esc(res.advice_provider || 'local')}</strong></span>
            ${res.advice_model ? `<span> · Model: <strong>${esc(res.advice_model)}</strong></span>` : ''}
          </div>
        </div>
        <div class="fusion-ai-body">${esc(res.advice || 'No automated advice returned for this run.')}</div>
      </div>

      <!-- 7. Result Action Bar -->
      <div class="fusion-action-bar">
        ${
          res.id
            ? `<a href="/predictions/${res.id}/report/" target="_blank" class="v2-button secondary" id="btnViewReport" data-prediction-id="${res.id}">View Analysis Report</a>`
            : ''
        }
        <button type="button" class="v2-button secondary" id="askAdvisorBtn">Ask AI Guide About This Fusion Result</button>
        <a href="/pages/history.html" class="v2-button ghost">View History</a>
        <button type="button" class="v2-button ghost" id="resetFusionBtn">Reset Fusion</button>
      </div>
    </section>
  `;
}

function renderModals() {
  if (!state.modal) return '';

  // Outlier Safeguard Modal
  if (state.modal === 'outlier') {
    const outliers = state.modalData || [];
    return `
      <div class="v2-modal-backdrop" id="modalBackdrop">
        <div class="v2-modal-card">
          <h3 class="v2-modal-title" style="color:#b91c1c;">⚠️ Outlier Review Required Before Fusion</h3>
          <p class="v2-modal-desc">
            One or more structured features lie outside observed min/max development bounds.
            Please review these values before proceeding with the experimental combination.
          </p>
          <div style="max-height:240px;overflow-y:auto;margin:12px 0;">
            <table class="v2-table" style="width:100%;font-size:0.8rem;">
              <thead>
                <tr>
                  <th>Feature</th>
                  <th>Entered Value</th>
                  <th>Observed Range</th>
                </tr>
              </thead>
              <tbody>
                ${outliers.map((o) => `
                  <tr>
                    <td><strong>${esc(o.label)}</strong></td>
                    <td style="color:#b91c1c;font-weight:700;">${o.value}</td>
                    <td>${o.min} – ${o.max}</td>
                  </tr>
                `).join('')}
              </tbody>
            </table>
          </div>
          <div class="v2-modal-actions">
            <button type="button" class="v2-button ghost" id="cancelModalBtn">Cancel & Edit</button>
            <button type="button" class="v2-button primary" id="confirmOutlierBtn">Confirm & Run Fusion</button>
          </div>
        </div>
      </div>
    `;
  }

  // CSV Import Modal
  if (state.modal === 'csv') {
    if (state.modalData?.isMultiRow) {
      const { rows, rowCount } = state.modalData;
      return `
        <div class="v2-modal-backdrop" id="modalBackdrop">
          <div class="v2-modal-card" style="max-width:680px;">
            <h3 class="v2-modal-title">Import WDBC FNA Features CSV</h3>
            <div style="font-size:0.84rem;font-weight:700;color:#0369a1;margin-bottom:6px;">
              Multiple WDBC Observations Detected (${rowCount} rows)
            </div>
            <p class="v2-modal-desc" style="margin-bottom:10px;">
              Experimental Fusion represents exactly <strong>ONE</strong> WDBC structured observation + <strong>ONE</strong> mammography image.
              Select one valid observation below for this Fusion run:
            </p>

            <div style="font-size:0.75rem;color:#64748b;background:#f8fafc;border:1px solid #e2e8f0;padding:8px 12px;border-radius:6px;margin-bottom:12px;line-height:1.4;">
              <strong>Unpaired Dataset Notice:</strong> WDBC cytology observations and CBIS-DDSM mammography images are scientifically unpaired datasets. Selecting this observation does not imply clinical association with the selected mammogram.
            </div>

            <div class="fusion-csv-table-wrap" style="max-height:260px;overflow-y:auto;border:1px solid #e2e8f0;border-radius:6px;margin-bottom:14px;">
              <table class="fusion-csv-table" style="width:100%;border-collapse:collapse;font-size:0.82rem;">
                <thead style="background:#f1f5f9;position:sticky;top:0;z-index:1;">
                  <tr style="text-align:left;border-bottom:1px solid #cbd5e1;">
                    <th style="padding:8px 10px;width:54px;text-align:center;">Select</th>
                    <th style="padding:8px 10px;">Row #</th>
                    <th style="padding:8px 10px;">Sample ID</th>
                    <th style="padding:8px 10px;">Features</th>
                    <th style="padding:8px 10px;">Status</th>
                  </tr>
                </thead>
                <tbody>
                  ${rows.map((row, idx) => `
                    <tr style="border-bottom:1px solid #f1f5f9;background:${idx % 2 === 0 ? '#ffffff' : '#f8fafc'};">
                      <td style="padding:8px 10px;text-align:center;">
                        <input
                          type="radio"
                          name="csvObservationSelect"
                          id="csvRowRadio_${idx}"
                          value="${idx}"
                          ${!row.valid ? 'disabled' : ''}
                          ${state.selectedCsvRowIndex === idx ? 'checked' : ''}
                          aria-label="Select row ${row.rowNumber}"
                        />
                      </td>
                      <td style="padding:8px 10px;font-weight:600;">#${row.rowNumber}</td>
                      <td style="padding:8px 10px;color:#334155;">${esc(row.id || 'N/A')}</td>
                      <td style="padding:8px 10px;color:#475569;">${row.completedCount} / 30</td>
                      <td style="padding:8px 10px;">
                        ${row.valid
                          ? '<span style="color:#15803d;font-weight:700;">✓ Valid</span>'
                          : `<span style="color:#dc2626;font-size:0.75rem;" title="${esc(row.errors.join('; '))}">✗ ${esc(row.errors[0])}</span>`
                        }
                      </td>
                    </tr>
                  `).join('')}
                </tbody>
              </table>
            </div>

            <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">
              <button type="button" class="v2-button ghost btn-xs" id="csvPickAnotherBtn">Select Different File</button>
              <div style="display:flex;gap:8px;">
                <button type="button" class="v2-button ghost btn-xs" id="cancelModalBtn">Cancel</button>
                <button
                  type="button"
                  class="v2-button primary btn-xs"
                  id="btnLoadSelectedCsvRow"
                  ${state.selectedCsvRowIndex === null || !rows[state.selectedCsvRowIndex]?.valid ? 'disabled' : ''}
                >
                  Import Selected Observation
                </button>
              </div>
            </div>
          </div>
        </div>
      `;
    }

    return `
      <div class="v2-modal-backdrop" id="modalBackdrop">
        <div class="v2-modal-card" style="max-width:580px;">
          <h3 class="v2-modal-title">Import WDBC FNA Features CSV</h3>
          <p class="v2-modal-desc">
            Upload a CSV containing the 30 WDBC nuclear morphology features used by the Structured FNA Cytology branch.
          </p>

          <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:6px;padding:10px 12px;margin:10px 0;font-size:0.80rem;line-height:1.5;color:#334155;">
            <div style="font-weight:700;color:#0f172a;margin-bottom:3px;">Accepted CSV Format:</div>
            <div>• <strong>Required:</strong> 30 WDBC FNA nuclear morphology features (mean_radius ... worst_fractal_dimension)</div>
            <div>• <strong>Optional:</strong> <code>id</code> column</div>
            <div>• <strong>Ignored if present:</strong> <code>diagnosis</code>, <code>target</code>, <code>label</code>, unnamed index fields</div>
          </div>

          <div style="font-size:0.75rem;color:#64748b;margin:0 0 12px;line-height:1.4;">
            <strong>Unpaired Dataset Notice:</strong> WDBC cytology measurements and CBIS-DDSM mammography images are scientifically independent. A valid imported observation will populate Branch 1 inputs for this experimental fusion run without implying clinical pairing with any mammogram.
          </div>

          ${state.csvError ? `
            <div class="v2-alert error" id="csvErrorBox" style="background:#fef2f2;border:1px solid #fca5a5;color:#991b1b;border-radius:6px;padding:8px 12px;font-size:0.82rem;margin-bottom:12px;line-height:1.4;">
              <strong style="display:block;margin-bottom:2px;">CSV Validation Error:</strong>
              ${esc(state.csvError)}
            </div>
          ` : ''}

          <div class="fusion-dropzone-box" id="csvDropzone" style="min-height:130px;margin:12px 0;">
            <div style="font-size:1.6rem;color:#0284c7;margin-bottom:4px;">📄</div>
            <p style="margin:0 0 8px;font-size:0.88rem;font-weight:600;">Drag CSV here or browse</p>
            <button type="button" class="v2-button secondary btn-xs" id="csvFileTriggerBtn">Select CSV File</button>
            <input type="file" id="csvFileInput" accept=".csv,text/csv" style="display:none;" />
          </div>

          <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">
            <div style="display:flex;gap:8px;flex-wrap:wrap;">
              <button type="button" class="v2-button ghost btn-xs" id="downloadBenignCsvModalBtn">Download Benign CSV</button>
              <button type="button" class="v2-button ghost btn-xs" id="downloadMalignantCsvModalBtn">Download Malignant CSV</button>
              <button type="button" class="v2-button ghost btn-xs" id="downloadCsvTemplateBtn">Download Template</button>
            </div>
            <button type="button" class="v2-button ghost btn-xs" id="cancelModalBtn">Close</button>
          </div>
        </div>
      </div>
    `;
  }

  // Report OCR Modal
  if (state.modal === 'ocr') {
    return `
      <div class="v2-modal-backdrop" id="modalBackdrop">
        <div class="v2-modal-card">
          <h3 class="v2-modal-title">Extract Features from Lab Report Image</h3>
          <p class="v2-modal-desc">
            Upload a scanned cytology report photo. The system will use automated OCR to extract up to 30 numeric fields.
          </p>
          <div class="fusion-dropzone-box" id="ocrDropzone" style="min-height:140px;margin:16px 0;">
            <div style="font-size:1.6rem;color:#0284c7;margin-bottom:6px;">📋</div>
            <p style="margin:0 0 8px;font-size:0.88rem;font-weight:600;">Drag report photo here or browse</p>
            <button type="button" class="v2-button secondary btn-xs" id="ocrFileTriggerBtn">Select Report Image</button>
            <input type="file" id="ocrFileInput" accept="image/jpeg,image/png" style="display:none;" />
          </div>
          <div style="display:flex;justify-content:flex-end;">
            <button type="button" class="v2-button ghost btn-xs" id="cancelModalBtn">Close</button>
          </div>
        </div>
      </div>
    `;
  }

  return '';
}

function downloadCsvBlob(csvContent, filename) {
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

// ---------------------------------------------------------------------------
// Event Binding & DOM Synchronization
// ---------------------------------------------------------------------------

function bindEvents() {
  // Doctor Patient Select
  const docSelect = document.querySelector('#doctorPatientSelect');
  if (docSelect) {
    docSelect.onchange = (e) => {
      state.selectedPatientId = e.target.value;
      render();
    };
  }

  // Structured Branch Inputs
  document.querySelectorAll('.fusion-field-input').forEach((input) => {
    input.oninput = (e) => {
      const feat = e.target.dataset.feature;
      state.inputs[feat] = e.target.value;
      state.outlierConfirmed = false;

      // Update cell label status dynamically
      const cell = e.target.closest('.fusion-field-cell');
      if (cell) {
        const statusEl = cell.querySelector('.fusion-field-status');
        const refState = getFieldReferenceState(feat, e.target.value);
        if (statusEl) {
          statusEl.textContent = refState.label;
          statusEl.className = `fusion-field-status ${refState.class}`;
        }
      }

      // Update summary counts
      const quality = computeInputQuality();
      const pill = document.querySelector('.fusion-quality-pill');
      if (pill) {
        pill.textContent = `${quality.completed} / 30 Features Completed`;
        if (quality.isComplete) pill.classList.add('complete');
        else pill.classList.remove('complete');
      }

      // Check run button enabled state
      const runBtn = document.querySelector('#runFusionBtn');
      if (runBtn) {
        runBtn.disabled = !(quality.isComplete && state.file && !state.isAnalyzing);
      }
    };
  });

  // ML Group Tabs
  document.querySelectorAll('[data-group-tab]').forEach((btn) => {
    btn.onclick = () => {
      state.activeMlGroupTab = btn.dataset.groupTab;
      render();
    };
  });

  // Structured Presets
  const loadMlBenignBtn = document.querySelector('#loadMlBenignBtn');
  if (loadMlBenignBtn) loadMlBenignBtn.onclick = () => loadStructuredSample('benign');

  const loadMlMalignantBtn = document.querySelector('#loadMlMalignantBtn');
  if (loadMlMalignantBtn) loadMlMalignantBtn.onclick = () => loadStructuredSample('malignant');

  const clearMlBtn = document.querySelector('#clearMlBtn');
  if (clearMlBtn) clearMlBtn.onclick = () => clearStructuredInputs();

  // Toolbar CSV Demos (Branch 1)
  const dlBenignCsvBtn = document.querySelector('#downloadBenignCsvBtn');
  if (dlBenignCsvBtn) {
    dlBenignCsvBtn.onclick = () => {
      downloadCsvBlob(generateWdbcResearchDemoCsv(SAMPLES.benign), 'wdbc_benign_research_demo.csv');
    };
  }

  const dlMalignantCsvBtn = document.querySelector('#downloadMalignantCsvBtn');
  if (dlMalignantCsvBtn) {
    dlMalignantCsvBtn.onclick = () => {
      downloadCsvBlob(generateWdbcResearchDemoCsv(SAMPLES.malignant), 'wdbc_malignant_research_demo.csv');
    };
  }

  // CSV & OCR Modal Triggers
  const openCsvModalBtn = document.querySelector('#openCsvModalBtn');
  if (openCsvModalBtn) {
    openCsvModalBtn.onclick = () => {
      state.modal = 'csv';
      state.modalData = null;
      state.selectedCsvRowIndex = null;
      state.csvError = null;
      render();
    };
  }

  const openOcrModalBtn = document.querySelector('#openOcrModalBtn');
  if (openOcrModalBtn) openOcrModalBtn.onclick = () => { state.modal = 'ocr'; render(); };

  // Mammography Presets
  const loadDlBenignBtn = document.querySelector('#loadDlBenignBtn');
  if (loadDlBenignBtn) loadDlBenignBtn.onclick = () => loadMammogramDemoPreset('benign');

  const loadDlMalignantBtn = document.querySelector('#loadDlMalignantBtn');
  if (loadDlMalignantBtn) loadDlMalignantBtn.onclick = () => loadMammogramDemoPreset('malignant');

  // Mammography Upload / Dropzone
  const dropzone = document.querySelector('#mammogramDropzone');
  const fileInput = document.querySelector('#mammogramFileInput');
  const selectTrigger = document.querySelector('#selectImageTriggerBtn');
  const uploadToolbarBtn = document.querySelector('#uploadMammogramToolbarBtn');

  if (selectTrigger && fileInput) {
    selectTrigger.onclick = () => fileInput.click();
  }

  if (uploadToolbarBtn && fileInput) {
    uploadToolbarBtn.onclick = () => fileInput.click();
  }

  if (fileInput) {
    fileInput.onchange = (e) => {
      const file = e.target.files[0];
      if (file) handleFileSelected(file);
    };
  }

  if (dropzone) {
    dropzone.ondragover = (e) => {
      e.preventDefault();
      dropzone.classList.add('dragover');
    };
    dropzone.ondragleave = () => dropzone.classList.remove('dragover');
    dropzone.ondrop = (e) => {
      e.preventDefault();
      dropzone.classList.remove('dragover');
      const file = e.dataTransfer.files[0];
      if (file) handleFileSelected(file);
    };
    dropzone.onclick = (e) => {
      if (e.target !== selectTrigger) fileInput?.click();
    };
  }

  // Replace & Remove Image buttons
  const replaceBtn = document.querySelector('#replaceImageBtn');
  if (replaceBtn) {
    replaceBtn.onclick = () => {
      const dummyInput = document.createElement('input');
      dummyInput.type = 'file';
      dummyInput.accept = 'image/jpeg,image/png';
      dummyInput.onchange = (e) => {
        const file = e.target.files[0];
        if (file) handleFileSelected(file);
      };
      dummyInput.click();
    };
  }

  const removeBtn = document.querySelector('#removeImageBtn');
  const removeBtn2 = document.querySelector('#removeImageBtn2');
  const handleRemove = () => {
    cleanupObjectUrl();
    state.file = null;
    state.previewMetadata = null;
    state.isPreset = false;
    state.presetType = null;
    render();
  };
  if (removeBtn) removeBtn.onclick = handleRemove;
  if (removeBtn2) removeBtn2.onclick = handleRemove;

  // Run Fusion Action
  const runBtn = document.querySelector('#runFusionBtn');
  if (runBtn) runBtn.onclick = () => executeFusion();

  // Grad-CAM mode switcher
  document.querySelectorAll('[data-cam-mode]').forEach((btn) => {
    btn.onclick = () => {
      state.gradcamViewMode = btn.dataset.camMode;
      render();
    };
  });

  // Toggle "Why can results differ?"
  const toggleDiffersBtn = document.querySelector('#toggleDiffersBtn');
  if (toggleDiffersBtn) {
    toggleDiffersBtn.onclick = () => {
      state.differsExpanded = !state.differsExpanded;
      render();
    };
  }

  // Advisor Handoff
  const askAdvisorBtn = document.querySelector('#askAdvisorBtn');
  if (askAdvisorBtn) askAdvisorBtn.onclick = () => handoffToAdvisor();

  // Authenticated View Report
  const btnReport = document.querySelector('#btnViewReport');
  if (btnReport) {
    btnReport.onclick = (e) => {
      e.preventDefault();
      const pid = btnReport.getAttribute('data-prediction-id');
      if (pid) reportService.open(pid);
    };
  }

  // Reset Fusion Action
  const resetBtn = document.querySelector('#resetFusionBtn');
  if (resetBtn) resetBtn.onclick = () => resetFusionWorkstation();

  // Modal actions & Accessibility
  const cancelModalBtn = document.querySelector('#cancelModalBtn');
  const modalBackdrop = document.querySelector('#modalBackdrop');
  let modalCleanup = null;
  const closeModal = () => {
    if (modalCleanup) { modalCleanup(); modalCleanup = null; }
    state.modal = null;
    state.modalData = null;
    state.selectedCsvRowIndex = null;
    state.csvError = null;
    render();
  };
  if (modalBackdrop) {
    modalCleanup = bindModalAccessibility(modalBackdrop, closeModal);
    modalBackdrop.onclick = (e) => {
      if (e.target === modalBackdrop) closeModal();
    };
  }
  if (cancelModalBtn) cancelModalBtn.onclick = closeModal;

  const confirmOutlierBtn = document.querySelector('#confirmOutlierBtn');
  if (confirmOutlierBtn) {
    confirmOutlierBtn.onclick = () => {
      state.outlierConfirmed = true;
      closeModal();
      executeFusion();
    };
  }

  // Branch 1 Input Method Controls
  const branch1ManualBtn = document.querySelector('#branch1ManualBtn');
  if (branch1ManualBtn) {
    branch1ManualBtn.onclick = () => {
      state.branch1InputMode = 'manual';
      const firstInput = document.querySelector('.fusion-field-input');
      if (firstInput) {
        firstInput.focus();
        firstInput.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    };
  }

  const dismissBranch1Notif = document.querySelector('#dismissBranch1NotificationBtn');
  if (dismissBranch1Notif) {
    dismissBranch1Notif.onclick = () => {
      state.branch1Notification = null;
      render();
    };
  }

  // CSV Modal actions
  const handleCsvText = (text) => {
    try {
      state.csvError = null;
      const parsed = parseClinicalCsv(text);
      if (parsed.isMultiRow) {
        state.modal = 'csv';
        state.modalData = parsed;
        state.selectedCsvRowIndex = null; // NEVER silently choose row 1
        render();
      } else {
        const row = parsed.rows[0];
        if (!row.valid) {
          state.csvError = row.errors.join(' ');
          render();
          return;
        }
        for (const feat of ML_FEATURES) {
          if (row.values[feat] !== undefined) {
            state.inputs[feat] = String(row.values[feat]);
          }
        }
        state.outlierConfirmed = false;
        state.branch1Notification = {
          type: 'success',
          message: '1 valid WDBC observation loaded.',
        };
        closeModal();
      }
    } catch (err) {
      state.csvError = err.message || 'Failed to parse CSV file.';
      render();
    }
  };

  const csvTrigger = document.querySelector('#csvFileTriggerBtn');
  const csvInput = document.querySelector('#csvFileInput');
  if (csvTrigger && csvInput) csvTrigger.onclick = () => csvInput.click();
  if (csvInput) {
    csvInput.onchange = async (e) => {
      const file = e.target.files?.[0];
      if (!file) return;
      try {
        const text = await file.text();
        handleCsvText(text);
      } catch (err) {
        state.csvError = `Failed to read CSV: ${err.message}`;
        render();
      } finally {
        csvInput.value = '';
      }
    };
  }

  const csvDropzone = document.querySelector('#csvDropzone');
  if (csvDropzone) {
    csvDropzone.ondragover = (e) => {
      e.preventDefault();
      csvDropzone.classList.add('dragover');
    };
    csvDropzone.ondragleave = () => {
      csvDropzone.classList.remove('dragover');
    };
    csvDropzone.ondrop = async (e) => {
      e.preventDefault();
      csvDropzone.classList.remove('dragover');
      const file = e.dataTransfer?.files?.[0];
      if (file) {
        try {
          const text = await file.text();
          handleCsvText(text);
        } catch (err) {
          state.csvError = `Failed to read CSV: ${err.message}`;
          render();
        }
      }
    };
  }

  // Multi-row Observation Selection
  const rowRadios = document.querySelectorAll('input[name="csvObservationSelect"]');
  rowRadios.forEach((radio) => {
    radio.onchange = (e) => {
      state.selectedCsvRowIndex = parseInt(e.target.value, 10);
      const btn = document.querySelector('#btnLoadSelectedCsvRow');
      if (btn) {
        const row = state.modalData?.rows?.[state.selectedCsvRowIndex];
        btn.disabled = !(row && row.valid);
      }
    };
  });

  const btnLoadSelected = document.querySelector('#btnLoadSelectedCsvRow');
  if (btnLoadSelected) {
    btnLoadSelected.onclick = () => {
      if (state.selectedCsvRowIndex === null) return;
      const row = state.modalData?.rows?.[state.selectedCsvRowIndex];
      if (!row || !row.valid) return;
      for (const feat of ML_FEATURES) {
        if (row.values[feat] !== undefined) {
          state.inputs[feat] = String(row.values[feat]);
        }
      }
      state.outlierConfirmed = false;
      state.branch1Notification = {
        type: 'success',
        message: '1 valid WDBC observation loaded.',
      };
      closeModal();
    };
  }

  const csvPickAnotherBtn = document.querySelector('#csvPickAnotherBtn');
  if (csvPickAnotherBtn) {
    csvPickAnotherBtn.onclick = () => {
      state.modalData = null;
      state.selectedCsvRowIndex = null;
      state.csvError = null;
      render();
    };
  }

  const dlBenignModalBtn = document.querySelector('#downloadBenignCsvModalBtn');
  if (dlBenignModalBtn) {
    dlBenignModalBtn.onclick = () => {
      downloadCsvBlob(generateWdbcResearchDemoCsv(SAMPLES.benign), 'wdbc_benign_research_demo.csv');
    };
  }

  const dlMalignantModalBtn = document.querySelector('#downloadMalignantCsvModalBtn');
  if (dlMalignantModalBtn) {
    dlMalignantModalBtn.onclick = () => {
      downloadCsvBlob(generateWdbcResearchDemoCsv(SAMPLES.malignant), 'wdbc_malignant_research_demo.csv');
    };
  }

  const dlTemplateBtn = document.querySelector('#downloadCsvTemplateBtn');
  if (dlTemplateBtn) {
    dlTemplateBtn.onclick = () => {
      downloadCsvBlob(generateCsvTemplate(), 'wdbc_features_template.csv');
    };
  }

  const dlExampleBtn = document.querySelector('#downloadExampleCsvBtn');
  if (dlExampleBtn) {
    dlExampleBtn.onclick = () => {
      downloadCsvBlob(generateWdbcResearchDemoCsv(SAMPLES.benign), 'wdbc_benign_research_demo.csv');
    };
  }

  // OCR Modal actions
  const ocrTrigger = document.querySelector('#ocrFileTriggerBtn');
  const ocrInput = document.querySelector('#ocrFileInput');
  if (ocrTrigger && ocrInput) ocrTrigger.onclick = () => ocrInput.click();
  if (ocrInput) {
    ocrInput.onchange = async (e) => {
      const file = e.target.files[0];
      if (!file) return;
      try {
        ocrTrigger.disabled = true;
        ocrTrigger.textContent = 'Extracting features…';
        const res = await predictionService.extractClinical(file);
        if (res?.values) {
          let filled = 0;
          for (const feat of ML_FEATURES) {
            if (res.values[feat] !== undefined && res.values[feat] !== null) {
              state.inputs[feat] = String(res.values[feat]);
              filled++;
            }
          }
          state.outlierConfirmed = false;
          alert(`Extracted ${filled}/30 features from lab report photo.`);
          closeModal();
        } else {
          alert('No numeric WDBC features could be extracted.');
        }
      } catch (err) {
        alert(`OCR extraction failed: ${err.message}`);
      } finally {
        if (ocrTrigger) {
          ocrTrigger.disabled = false;
          ocrTrigger.textContent = 'Select Report Image';
        }
      }
    };
  }
}

// ---------------------------------------------------------------------------
// Main Render Function
// ---------------------------------------------------------------------------

function render() {
  app.innerHTML = `
    <main class="fusion-workstation">
      ${renderHero()}
      ${renderDoctorPatientBar()}

      <!-- Dual Independent Input Workstation -->
      <section class="fusion-dual-grid">
        ${renderStructuredBranch()}
        ${renderMammographyBranch()}
      </section>

      <!-- Converging Execution Hub -->
      ${renderExecutionHub()}

      <!-- Results Workspace (Shown after execution) -->
      ${renderResults()}

      <!-- Modals (Outlier check, CSV import, OCR report) -->
      ${renderModals()}
    </main>
  `;

  bindEvents();
}

// ---------------------------------------------------------------------------
// Initialization
// ---------------------------------------------------------------------------

async function init() {
  if (isDoctor) {
    try {
      state.patients = await patientService.list();
    } catch (err) {
      console.warn('Failed to load doctor patient list:', err);
    }
  }

  render();
}

init();
