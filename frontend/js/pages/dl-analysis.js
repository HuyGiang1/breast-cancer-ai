import { mountShell } from '../components/shell.js';
import { predictionService } from '../services/prediction.service.js';
import { patientService } from '../services/patient.service.js';
import { reportService } from '../services/report.service.js';
import { auth } from '../core/auth.js';

mountShell('Mammography Research Analysis');

const app = document.querySelector('#app');
const currentUser = auth.user();
const isDoctor = currentUser?.role === 'doctor';

const urlParams = new URLSearchParams(window.location.search);
const initialPatientId = urlParams.get('patient_id') || '';

// Internal Workstation State
const state = {
  file: null,
  objectUrl: null,
  previewMetadata: null, // { name, size, type, width, height }
  isPreset: false,
  presetType: null, // 'benign' | 'malignant'
  selectedPatientId: isDoctor && initialPatientId ? initialPatientId : '',
  patients: [],
  comparisonMode: 'side-by-side', // 'side-by-side' | 'original' | 'gradcam'
  stage: 'idle', // 'idle' | 'validating' | 'uploading' | 'inferring' | 'gradcam' | 'interpreting' | 'saving' | 'done' | 'error'
  isAnalyzing: false,
  result: null,
  errorMessage: null,
};

// Revoke previous blob URL to prevent browser memory leaks
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

// Stage configurations for transparent execution tracking
const STAGES = [
  { id: 'validating', label: 'Validating mammography image format and dimensions' },
  { id: 'uploading', label: 'Uploading image to inference runtime' },
  { id: 'inferring', label: 'Running frozen EfficientNet-B0 (224×224 input)' },
  { id: 'gradcam', label: 'Generating Grad-CAM attention map on top_conv' },
  { id: 'interpreting', label: 'Evaluating raw probability vs frozen 0.515 cutoff' },
  { id: 'saving', label: 'Saving analysis record' },
];

function getStageStatus(stageId) {
  const stageOrder = ['idle', 'validating', 'uploading', 'inferring', 'gradcam', 'interpreting', 'saving', 'done'];
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

// Validate file selection safely
async function handleFileSelected(file, isPreset = false, presetType = null) {
  state.errorMessage = null;

  if (!file) {
    return;
  }

  // 1. Empty / zero-byte file check
  if (file.size === 0) {
    state.errorMessage = 'The selected file is empty (0 bytes). Please choose a valid image.';
    render();
    return;
  }

  // 2. Format / MIME validation
  const validTypes = ['image/jpeg', 'image/png'];
  const ext = file.name.split('.').pop()?.toLowerCase();
  const validExts = ['jpg', 'jpeg', 'png'];

  if (!validTypes.includes(file.type) && !validExts.includes(ext)) {
    state.errorMessage = 'Unsupported file format. Please upload a standard JPEG or PNG mammography image.';
    render();
    return;
  }

  // 3. Oversized file check (> 15 MB)
  if (file.size > 15 * 1024 * 1024) {
    state.errorMessage = 'File exceeds the 15 MB limit. Please select an optimized image.';
    render();
    return;
  }

  // Revoke previous object URL
  cleanupObjectUrl();

  const newUrl = URL.createObjectURL(file);

  // 4. Verify browser decode and measure pixel dimensions
  try {
    const img = new Image();
    await new Promise((resolve, reject) => {
      img.onload = () => resolve(img);
      img.onerror = () => reject(new Error('Image decode error'));
      img.src = newUrl;
    });

    state.file = file;
    state.objectUrl = newUrl;
    state.isPreset = isPreset;
    state.presetType = presetType;
    state.previewMetadata = {
      name: file.name,
      size: file.size,
      type: file.type || (ext === 'png' ? 'image/png' : 'image/jpeg'),
      width: img.naturalWidth,
      height: img.naturalHeight,
    };
    state.stage = 'idle';
    render();
  } catch {
    cleanupObjectUrl();
    state.errorMessage = 'Corrupt or unreadable image file. Unable to decode image data.';
    render();
  }
}

// Load canonical committed demo research assets
async function loadDemoPreset(type) {
  const filename = type === 'benign' ? 'demo-benign-mammogram.png' : 'demo-malignant-mammogram.png';
  const path = `/assets/demo-images/${filename}`;

  try {
    const response = await fetch(path);
    if (!response.ok) {
      throw new Error(`Demo asset not accessible (${response.status})`);
    }
    const blob = await response.blob();
    const file = new File([blob], filename, { type: 'image/png' });
    await handleFileSelected(file, true, type);
  } catch (err) {
    state.errorMessage = `Could not load ${type} research example: ${err.message}`;
    render();
  }
}

// Remove selected image and reset canvas
function handleRemoveImage() {
  cleanupObjectUrl();
  state.file = null;
  state.previewMetadata = null;
  state.isPreset = false;
  state.presetType = null;
  state.errorMessage = null;
  state.stage = 'idle';
  render();
}

// Reset entire workstation for another analysis
function handleResetAnalysis() {
  cleanupObjectUrl();
  state.file = null;
  state.previewMetadata = null;
  state.isPreset = false;
  state.presetType = null;
  state.stage = 'idle';
  state.isAnalyzing = false;
  state.result = null;
  state.errorMessage = null;
  state.comparisonMode = 'side-by-side';
  render();
}

// Execute analysis with sequential stages
async function executeAnalysis() {
  if (!state.file || state.isAnalyzing) return;

  state.isAnalyzing = true;
  state.errorMessage = null;

  try {
    // Stage 1: Validating
    state.stage = 'validating';
    render();
    await new Promise((r) => setTimeout(r, 150));

    // Stage 2: Uploading
    state.stage = 'uploading';
    render();
    await new Promise((r) => setTimeout(r, 150));

    // Stage 3: Inferring & Grad-CAM (backend processes)
    state.stage = 'inferring';
    render();

    // Call prediction service with includeExplanation = true
    const result = await predictionService.dl(state.file, {
      patientId: state.selectedPatientId || undefined,
      includeExplanation: true,
    });

    // Stage 4: Grad-CAM attention
    state.stage = 'gradcam';
    render();
    await new Promise((r) => setTimeout(r, 150));

    // Stage 5: Interpreting
    state.stage = 'interpreting';
    render();
    await new Promise((r) => setTimeout(r, 150));

    // Stage 6: Saving & done
    state.stage = 'saving';
    render();
    await new Promise((r) => setTimeout(r, 150));

    state.stage = 'done';
    state.result = result;
  } catch (err) {
    state.stage = 'error';
    state.errorMessage = err?.message || 'Inference service encountered an error. Please try again.';
  } finally {
    state.isAnalyzing = false;
    render();
  }
}

// Handoff to AI Guide with minimal structured context
function handleAskAiGuide() {
  if (!state.result) return;
  const r = state.result;
  const isMalignant = (r.raw_probability ?? 0) >= 0.515;
  const classLabel = isMalignant ? 'Malignant' : 'Benign';

  const contextPayload = {
    analysis_type: 'dl',
    model: 'EfficientNet-B0',
    dataset: 'CBIS-DDSM',
    representation: 'full processed image',
    classification: classLabel,
    raw_probability: r.raw_probability,
    threshold: 0.515,
    calibrated_probability: r.calibrated_probability,
    gradcam_status: r.explanation_status || 'unavailable',
    prediction_id: r.id || r.prediction_id || null,
  };

  try {
    sessionStorage.setItem('bcai_advisor_context', JSON.stringify(contextPayload));
  } catch {}

  window.location.href = '/pages/advisor.html';
}

// Main Render Function
function render() {
  const selectedPatient = state.patients.find((p) => String(p.id) === String(state.selectedPatientId));
  const hasImage = Boolean(state.file && state.objectUrl);
  const hasResult = Boolean(state.result);

  app.innerHTML = `
    <div class="dl-workstation">
      <!-- 1. Hero & Model Context -->
      <header class="ml-hero">
        <div class="ml-hero-eyebrow">
          <span>🔬 Study B · CBIS-DDSM Full Processed Image</span>
          <span>•</span>
          <span>EfficientNet-B0 Candidate</span>
        </div>
        <h1>Mammography Research Analysis Workstation</h1>
        <p class="ml-hero-desc">
          High-precision research inspection for digitized mammography images.
          Evaluated against the frozen <strong>EfficientNet-B0</strong> model (ID: <code>cbis-efficientnetb0-full-v1</code>)
          with a frozen decision cutoff at <strong>≥ 0.515 raw malignant probability</strong>.
        </p>
        <div class="ml-hero-specs">
          <span class="ml-spec-pill">Architecture: <strong>EfficientNet-B0</strong></span>
          <span class="ml-spec-pill">Dataset: <strong>CBIS-DDSM (Processed)</strong></span>
          <span class="ml-spec-pill">Input Tensor: <strong>224 × 224 × 3</strong></span>
          <span class="ml-spec-pill">Raw Cutoff: <strong>0.515</strong></span>
          <span class="ml-spec-pill">XAI Layer: <strong>top_conv (Grad-CAM)</strong></span>
          <span class="ml-spec-pill">Calibration: <strong>Platt (Display Only)</strong></span>
        </div>
      </header>

      <!-- 2. Doctor Patient Context (Visible only to doctors) -->
      ${isDoctor ? `
        <div class="doctor-patient-bar">
          <div class="doctor-patient-info">
            <span class="doctor-patient-badge">Doctor Workspace</span>
            <span>
              ${selectedPatient
                ? `Analyzing for <strong>${esc(selectedPatient.full_name)}</strong> (ID: ${selectedPatient.id})`
                : 'No patient selected (Research-only analysis)'
              }
            </span>
            ${selectedPatient ? `<a href="/pages/patients.html" class="v2-link" style="margin-left:8px;">View Patient</a>` : ''}
          </div>
          <div class="doctor-patient-controls">
            <label for="doctorPatientSelect" style="font-size:0.82rem;font-weight:600;color:#166534;">Attach to Patient:</label>
            <select id="doctorPatientSelect" class="doctor-patient-select">
              <option value="">— No patient / Research-only —</option>
              ${state.patients.map((p) => `
                <option value="${p.id}" ${String(p.id) === String(state.selectedPatientId) ? 'selected' : ''}>
                  ${esc(p.full_name)} (DOB: ${esc(p.date_of_birth || 'N/A')})
                </option>
              `).join('')}
            </select>
          </div>
        </div>
      ` : ''}

      <!-- 3. Error Banner (if any) -->
      ${state.errorMessage ? `
        <div class="dl-uncertainty-banner" style="background:#fef2f2;border-color:#fca5a5;color:#991b1b;" role="alert">
          <span style="font-size:1.2rem;">⚠️</span>
          <div>
            <strong>File or Execution Notice:</strong> ${esc(state.errorMessage)}
          </div>
        </div>
      ` : ''}

      <!-- 4. Three-Column Workstation Layout -->
      <div class="dl-workspace-grid">
        <!-- LEFT: Image Upload & Demo Presets -->
        <div class="dl-card" aria-label="Image Selection">
          <h3 class="dl-card-title">
            <span>Mammogram Input</span>
            <span style="font-size:0.75rem;color:#64748b;font-weight:normal;">JPEG / PNG</span>
          </h3>

          <div
            id="dropzone"
            class="dl-upload-dropzone"
            tabindex="0"
            role="button"
            aria-label="Upload mammography image"
          >
            <span class="dl-upload-icon">📁</span>
            <div class="dl-upload-primary-text">Drop mammography image here</div>
            <div class="dl-upload-subtext">Supports JPEG and PNG formats up to 15MB</div>
            <span class="dl-upload-file-btn">Choose JPEG / PNG</span>
            <input
              type="file"
              id="fileInput"
              accept="image/jpeg,image/png"
              style="display:none;"
              aria-hidden="true"
            >
          </div>

          <div class="dl-transparency-box">
            <strong>Preprocessing Pipeline:</strong><br>
            Original image → Decoded as RGB → Resized to 224 × 224 → Fed to frozen EfficientNet-B0.<br>
            <span style="color:#64748b;font-size:0.72rem;">No DICOM windowing or metadata extraction is performed.</span>
          </div>

          <div style="margin-top:20px;">
            <div style="font-size:0.8rem;font-weight:700;text-transform:uppercase;color:#475569;margin-bottom:8px;letter-spacing:0.04em;">
              Canonical Research Examples
            </div>
            <div class="dl-presets-list">
              <button type="button" class="dl-preset-btn benign" id="btnPresetBenign">
                <span>🔬</span>
                <div>
                  <div>Load benign research example</div>
                  <small style="color:#64748b;font-size:0.72rem;">CBIS-DDSM verified benign case</small>
                </div>
              </button>
              <button type="button" class="dl-preset-btn malignant" id="btnPresetMalignant">
                <span>🔬</span>
                <div>
                  <div>Load malignant research example</div>
                  <small style="color:#64748b;font-size:0.72rem;">CBIS-DDSM verified malignant case</small>
                </div>
              </button>
            </div>
          </div>
        </div>

        <!-- CENTER: Medical Imaging Inspection Canvas -->
        <div class="dl-canvas-panel" aria-label="Medical Imaging Inspection Canvas">
          <div class="dl-canvas-header">
            <span class="dl-canvas-title">
              <span>🖼️ Inspection Canvas</span>
              <span class="dl-canvas-badge">224 × 224 Native Matrix</span>
            </span>
            <span style="font-size:0.75rem;color:#94a3b8;">
              ${hasImage ? 'Image Loaded & Ready' : 'Awaiting Image Input'}
            </span>
          </div>

          <div class="dl-canvas-body">
            ${hasImage ? `
              <img
                src="${state.objectUrl}"
                alt="Uploaded mammogram preview"
                class="dl-canvas-img"
                id="canvasPreviewImage"
              >
            ` : `
              <div class="dl-canvas-empty">
                <div style="font-size:2.8rem;margin-bottom:8px;opacity:0.6;">🩻</div>
                <div style="font-weight:600;font-size:1rem;color:#cbd5e1;margin-bottom:4px;">No mammogram loaded</div>
                <p style="font-size:0.82rem;max-width:320px;margin:0 auto;line-height:1.4;">
                  Upload a mammography scan or select a canonical research example to inspect the matrix.
                </p>
              </div>
            `}
          </div>

          ${hasImage && state.previewMetadata ? `
            <div class="dl-canvas-metadata-bar">
              <div>File: <strong>${esc(state.previewMetadata.name)}</strong></div>
              <div>Type: <strong>${esc(state.previewMetadata.type)}</strong></div>
              <div>Size: <strong>${(state.previewMetadata.size / 1024).toFixed(1)} KB</strong></div>
              <div>Dimensions: <strong>${state.previewMetadata.width} × ${state.previewMetadata.height} px</strong></div>
              ${state.isPreset ? `<div>Source: <strong style="color:#64dfdf;">Research Example (${state.presetType})</strong></div>` : ''}
            </div>

            <div class="dl-canvas-controls">
              <button type="button" class="v2-button secondary btn-xs" id="btnReplaceImage">
                Replace Image
              </button>
              <button type="button" class="v2-button secondary btn-xs" id="btnRemoveImage" style="color:#ef4444;">
                Remove Image
              </button>
            </div>
          ` : ''}
        </div>

        <!-- RIGHT: Model Execution & State Tracking -->
        <div class="dl-card" aria-label="Model Execution">
          <h3 class="dl-card-title">
            <span>Model Execution</span>
            <span style="font-size:0.72rem;background:#f0fdfa;color:#0f766e;padding:2px 6px;border-radius:4px;font-weight:700;">
              FROZEN
            </span>
          </h3>

          <div style="font-size:0.82rem;color:#475569;margin-bottom:16px;line-height:1.45;">
            Inference generates model classification and a Grad-CAM coarse attention overlay on convolutional layer <code>top_conv</code>.
          </div>

          <button
            type="button"
            class="dl-run-btn"
            id="btnRunAnalysis"
            ${!hasImage || state.isAnalyzing ? 'disabled' : ''}
          >
            ${state.isAnalyzing ? `
              <span>⏳ Analyzing Mammogram…</span>
            ` : `
              <span>⚡ Analyze Mammogram</span>
            `}
          </button>

          <!-- Real Execution Tracker -->
          <div class="dl-stages-tracker" aria-live="polite">
            <div style="font-size:0.75rem;font-weight:700;text-transform:uppercase;color:#475569;letter-spacing:0.04em;margin-top:6px;">
              Execution Stages
            </div>
            ${STAGES.map((s) => {
              const st = getStageStatus(s.id);
              return `
                <div class="dl-stage-item ${st.class}">
                  <span class="dl-stage-icon">${st.icon}</span>
                  <span>${s.label}</span>
                </div>
              `;
            }).join('')}
          </div>
        </div>
      </div>

      <!-- 5. Full-Width Result Workspace (After Analysis) -->
      ${hasResult ? renderResultWorkspace() : ''}
    </div>
  `;

  bindEvents();
}

// Render the rich Result Workspace
function renderResultWorkspace() {
  const r = state.result;
  const rawProb = Number(r.raw_probability ?? 0);
  const calibProb = Number(r.calibrated_probability ?? 0);
  const threshold = Number(r.decision_threshold ?? 0.515);

  // Classification is derived strictly from raw probability
  const isMalignant = rawProb >= threshold;
  const classLabel = isMalignant ? 'Malignant' : 'Benign';
  const diffPp = ((rawProb - threshold) * 100).toFixed(1);
  const diffSign = rawProb >= threshold ? '+' : '';

  // Uncertainty zone check
  const isUncertain = Math.abs(rawProb - threshold) < 0.05 || Boolean(r.uncertainty_warning);

  // Grad-CAM overlay status
  const hasGradcam = r.explanation_status === 'available' && Boolean(r.explanation_image);

  return `
    <section class="dl-result-workspace" id="resultWorkspace" aria-label="Analysis Results">
      <div class="dl-result-header">
        <h2>
          <span>📋</span> Mammography Analysis Result
          <span style="font-size:0.8rem;color:#64748b;font-weight:normal;margin-left:8px;">
            Prediction #${esc(r.id || r.prediction_id || 'Live')}
          </span>
        </h2>
        <div style="font-size:0.82rem;color:#475569;">
          Evaluated via <strong>EfficientNet-B0</strong> (CBIS-DDSM Full Processed Image)
        </div>
      </div>

      <!-- 1. Primary Classification Dominant Banner -->
      <div class="dl-classification-banner ${isMalignant ? 'malignant' : 'benign'}">
        <div>
          <div style="font-size:0.75rem;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;color:#475569;margin-bottom:2px;">
            Model Classification
          </div>
          <div class="dl-class-badge">
            <span>${isMalignant ? '🔴' : '🟢'}</span>
            <span>${classLabel}</span>
          </div>
          <div class="dl-class-subtext">
            Derived strictly from raw probability <strong>${(rawProb * 100).toFixed(1)}%</strong> relative to frozen threshold <strong>51.5%</strong>.
          </div>
        </div>

        <div style="text-align:right;">
          <div style="font-size:0.78rem;color:#64748b;margin-bottom:2px;">Threshold Distance</div>
          <div style="font-size:1.4rem;font-weight:800;color:${isMalignant ? '#991b1b' : '#166534'};">
            ${diffSign}${diffPp} pp
          </div>
          <div style="font-size:0.72rem;color:#64748b;">relative to 51.5% cutoff</div>
        </div>
      </div>

      <!-- 2. Uncertainty Warning (if close to threshold) -->
      ${isUncertain ? `
        <div class="dl-uncertainty-banner">
          <span style="font-size:1.2rem;">⚠️</span>
          <div>
            <strong>Borderline Probability Notice:</strong>
            This model output is relatively close to the frozen software decision threshold (51.5%) and should be interpreted cautiously.
            ${r.uncertainty_warning ? `<br><small>${esc(r.uncertainty_warning)}</small>` : ''}
          </div>
        </div>
      ` : ''}

      <!-- 3. Metrics Split: Raw Output vs Platt Calibration -->
      <div class="dl-metrics-split">
        <!-- Raw Probability Card -->
        <div class="dl-metric-card primary">
          <div class="dl-metric-card-header">
            <span>Raw Malignant Probability</span>
            <span class="dl-metric-threshold-badge">Cutoff: 51.5%</span>
          </div>
          <div class="dl-metric-value-row">
            <span class="dl-metric-value">${(rawProb * 100).toFixed(1)}%</span>
            <span class="dl-metric-distance">
              (${diffSign}${diffPp} pp from cutoff)
            </span>
          </div>
          <div class="dl-metric-note">
            <strong>Decision Rule:</strong>
            The model assigns class <em>Malignant</em> when raw probability is ≥ 0.515, and <em>Benign</em> otherwise.
            This value directly drives classification.
          </div>
        </div>

        <!-- Calibrated Probability Card -->
        <div class="dl-metric-card">
          <div class="dl-metric-card-header">
            <span>Calibrated Display Probability</span>
            <span style="font-size:0.72rem;background:#e2e8f0;padding:2px 6px;border-radius:4px;font-weight:600;">
              Platt Scaling
            </span>
          </div>
          <div class="dl-metric-value-row">
            <span class="dl-metric-value">${(calibProb * 100).toFixed(1)}%</span>
          </div>
          <div class="dl-metric-note">
            <strong>Display Interpretation Only:</strong>
            The calibrated probability is computed via post-hoc Platt calibration for display reliability.
            <strong>The calibrated probability is not used to determine the model class.</strong>
          </div>
        </div>
      </div>

      <!-- 4. Interactive Image Comparison Workspace (Original vs Grad-CAM) -->
      <div class="dl-comparison-section" aria-label="Visual Model Attention Comparison">
        <div class="dl-comparison-toolbar">
          <div style="font-size:0.85rem;font-weight:700;letter-spacing:0.04em;text-transform:uppercase;color:#64dfdf;display:flex;align-items:center;gap:8px;">
            <span>🔬 Visual Model Attention (Grad-CAM)</span>
            <span style="background:rgba(100,223,223,0.15);color:#64dfdf;font-size:0.72rem;padding:2px 6px;border-radius:4px;">
              Layer: top_conv
            </span>
          </div>

          <div class="dl-comparison-tabs">
            <button
              type="button"
              class="dl-comp-tab ${state.comparisonMode === 'side-by-side' ? 'active' : ''}"
              data-mode="side-by-side"
            >
              Side by Side
            </button>
            <button
              type="button"
              class="dl-comp-tab ${state.comparisonMode === 'original' ? 'active' : ''}"
              data-mode="original"
            >
              Original Mammogram
            </button>
            <button
              type="button"
              class="dl-comp-tab ${state.comparisonMode === 'gradcam' ? 'active' : ''}"
              data-mode="gradcam"
            >
              Grad-CAM Overlay
            </button>
          </div>
        </div>

        ${hasGradcam ? `
          <div class="dl-comparison-views ${state.comparisonMode === 'side-by-side' ? 'side-by-side' : 'single'}">
            ${state.comparisonMode !== 'gradcam' ? `
              <div class="dl-view-box">
                <div class="dl-view-box-header">
                  <span>Original Mammogram (Input)</span>
                  <span>224 × 224 Matrix</span>
                </div>
                <img
                  src="${state.objectUrl}"
                  alt="Original submitted mammogram"
                  class="dl-view-box-img"
                >
              </div>
            ` : ''}

            ${state.comparisonMode !== 'original' ? `
              <div class="dl-view-box">
                <div class="dl-view-box-header">
                  <span style="color:#64dfdf;">Grad-CAM Model Attention (top_conv)</span>
                  <span>Jet Color Overlay</span>
                </div>
                <img
                  src="${r.explanation_image}"
                  alt="Grad-CAM coarse model-attention overlay for the submitted mammography image."
                  class="dl-view-box-img"
                  id="gradcamOverlayImage"
                >
              </div>
            ` : ''}
          </div>

          <div class="dl-comparison-disclaimer">
            <strong>Model Attention Disclaimer:</strong>
            ${esc(r.explanation_disclaimer || 'Grad-CAM shows coarse model-attention regions contributing to model activation on the 224×224 input representation. It is not a validated lesion localization, tumor boundary, or pathology segmentation.')}
          </div>
        ` : `
          <div style="background:rgba(255,255,255,0.05);border-radius:8px;padding:24px;text-align:center;color:#94a3b8;">
            <p style="margin:0 0 6px 0;font-weight:600;color:#e2e8f0;">
              Model attention visualization could not be generated for this run.
            </p>
            <small>Model inference completed successfully, but Grad-CAM attention was unavailable.</small>
          </div>
        `}
      </div>

      <!-- 5. Educational Guidance & Next Steps -->
      <div class="dl-guidance-grid">
        <div class="dl-guidance-card">
          <h4><span>💡</span> What Does This Result Mean?</h4>
          <ul>
            <li>The frozen EfficientNet-B0 network analyzed the 224×224 pixel representation of the submitted mammogram.</li>
            <li>A raw malignant score of <strong>${(rawProb * 100).toFixed(1)}%</strong> was generated, evaluated against the benchmark cutoff (<strong>51.5%</strong>).</li>
            <li>Grad-CAM visualizes coarse regional features in convolutional layer <code>top_conv</code> that contributed to this numeric score.</li>
          </ul>
        </div>

        <div class="dl-guidance-card">
          <h4><span>🚫</span> What This Result Does NOT Mean</h4>
          <ul>
            <li>This is <strong>not a medical diagnosis</strong>, radiological interpretation, or biopsy equivalent.</li>
            <li>The model does not identify tumor size, margins, microcalcifications, or BI-RADS assessment categories.</li>
            <li>Warm/red Grad-CAM regions indicate mathematical model attention, not confirmed cancer locations.</li>
          </ul>
        </div>
      </div>

      <!-- 6. AI Educational Guidance -->
      ${r.advice ? `
        <div class="dl-ai-advice-card">
          <div class="dl-ai-advice-header">
            <div style="display:flex;align-items:center;gap:8px;">
              <span class="dl-ai-badge">AI Educational Guidance</span>
              <span style="font-size:0.75rem;color:#0f766e;">Non-diagnostic educational notes</span>
            </div>
            ${r.advice_provider ? `
              <span style="font-size:0.72rem;color:#64748b;">
                Generated by ${esc(r.advice_provider)} (${esc(r.advice_model || 'Research Engine')})
              </span>
            ` : ''}
          </div>
          <div style="font-size:0.88rem;color:#1e293b;line-height:1.55;white-space:pre-wrap;">${esc(r.advice)}</div>
        </div>
      ` : ''}

      <!-- 7. Clinical & Safe Next Steps -->
      <div class="dl-guidance-card" style="background:#f0fdf4;border-color:#bbf7d0;">
        <h4 style="color:#166534;"><span>🩺</span> Recommended Next Steps</h4>
        <ul style="color:#166534;">
          <li>This research result should be reviewed by an appropriate healthcare professional or licensed radiologist.</li>
          <li>Any concerning symptoms or palpable lumps require immediate clinical evaluation regardless of AI software outputs.</li>
          <li>Prior screening mammograms should be obtained for longitudinal comparison if formal clinical evaluation is undertaken.</li>
          <li>Further diagnostic imaging (diagnostic mammography, ultrasound, or MRI) may be ordered by your physician as indicated.</li>
        </ul>
      </div>

      <!-- 8. Action Bar -->
      <div class="dl-action-bar">
        <button type="button" class="v2-button secondary" id="btnAnalyzeAnother">
          Analyze Another Image
        </button>
        <button type="button" class="v2-button secondary" id="btnAskAiGuide">
          Ask AI Guide About This Result
        </button>
        ${r.id || r.prediction_id ? `
          <a
            href="/pages/reports.html?id=${encodeURIComponent(r.id || r.prediction_id)}"
            class="v2-button"
            id="btnViewReport"
            data-prediction-id="${encodeURIComponent(r.id || r.prediction_id)}"
          >
            View Analysis Report
          </a>
        ` : ''}
      </div>
    </section>
  `;
}

// Bind DOM Events
function bindEvents() {
  const dropzone = document.querySelector('#dropzone');
  const fileInput = document.querySelector('#fileInput');
  const btnRun = document.querySelector('#btnRunAnalysis');
  const btnPresetBenign = document.querySelector('#btnPresetBenign');
  const btnPresetMalignant = document.querySelector('#btnPresetMalignant');
  const btnReplace = document.querySelector('#btnReplaceImage');
  const btnRemove = document.querySelector('#btnRemoveImage');
  const doctorSelect = document.querySelector('#doctorPatientSelect');
  const btnAnalyzeAnother = document.querySelector('#btnAnalyzeAnother');
  const btnAskAi = document.querySelector('#btnAskAiGuide');

  // File picker trigger
  if (dropzone && fileInput) {
    dropzone.onclick = () => fileInput.click();
    dropzone.onkeydown = (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        fileInput.click();
      }
    };
    fileInput.onchange = () => {
      if (fileInput.files?.[0]) {
        handleFileSelected(fileInput.files[0]);
      }
    };

    // Drag & drop handlers
    dropzone.ondragover = (e) => {
      e.preventDefault();
      dropzone.classList.add('dragover');
    };
    dropzone.ondragleave = () => {
      dropzone.classList.remove('dragover');
    };
    dropzone.ondrop = (e) => {
      e.preventDefault();
      dropzone.classList.remove('dragover');
      if (e.dataTransfer?.files?.[0]) {
        handleFileSelected(e.dataTransfer.files[0]);
      }
    };
  }

  // Preset buttons
  if (btnPresetBenign) {
    btnPresetBenign.onclick = () => loadDemoPreset('benign');
  }
  if (btnPresetMalignant) {
    btnPresetMalignant.onclick = () => loadDemoPreset('malignant');
  }

  // Replace & Remove
  if (btnReplace && fileInput) {
    btnReplace.onclick = () => fileInput.click();
  }
  if (btnRemove) {
    btnRemove.onclick = handleRemoveImage;
  }

  // Run analysis
  if (btnRun) {
    btnRun.onclick = executeAnalysis;
  }

  // Doctor patient selector
  if (doctorSelect) {
    doctorSelect.onchange = (e) => {
      state.selectedPatientId = e.target.value;
      render();
    };
  }

  // Comparison view mode tabs
  document.querySelectorAll('.dl-comp-tab').forEach((tab) => {
    tab.onclick = () => {
      state.comparisonMode = tab.getAttribute('data-mode') || 'side-by-side';
      render();
    };
  });

  // Action buttons
  if (btnAnalyzeAnother) {
    btnAnalyzeAnother.onclick = handleResetAnalysis;
  }
  if (btnAskAi) {
    btnAskAi.onclick = handleAskAiGuide;
  }
  const btnReport = document.querySelector('#btnViewReport');
  if (btnReport) {
    btnReport.onclick = (e) => {
      e.preventDefault();
      const pid = btnReport.getAttribute('data-prediction-id');
      if (pid) reportService.open(pid);
    };
  }
}

// Initial Initialization
async function init() {
  if (isDoctor) {
    try {
      state.patients = await patientService.list();
    } catch {
      state.patients = [];
    }
  }
  render();
}

init();
