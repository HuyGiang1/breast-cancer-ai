import { mountShell } from '../components/shell.js';
import { predictionService } from '../services/prediction.service.js';
import { patientService } from '../services/patient.service.js';
import { reportService } from '../services/report.service.js';
import { auth } from '../core/auth.js';
import { t } from '../core/i18n.js';
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
} from '../utils/clinical-csv.js';

mountShell('Structured ML Analysis');

const app = document.querySelector('#app');
const currentUser = auth.user();
const isDoctor = currentUser?.role === 'doctor';

const urlParams = new URLSearchParams(window.location.search);
const initialPatientId = urlParams.get('patient_id') || '';

// Internal State
const state = {
  inputs: Object.fromEntries(ML_FEATURES.map((f) => [f, ''])),
  selectedPatientId: isDoctor && initialPatientId ? initialPatientId : '',
  patients: [],
  activeTab: 'all',
  result: null,
  outlierConfirmed: false,
  sortBy: 'mag', // 'mag' | 'malignant' | 'benign' | 'unusual' | 'default'
  modal: null, // 'csv' | 'ocr' | 'outlier' | null
  modalData: null,
};

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

// Compute reference state for a single field
function getFieldReferenceState(feature, rawValue) {
  if (rawValue === '' || rawValue === undefined || rawValue === null) {
    return { state: 'waiting', label: t('ml.awaitingInput', 'Awaiting input'), class: 'status-waiting' };
  }
  const val = Number(rawValue);
  if (Number.isNaN(val)) {
    return { state: 'invalid', label: t('ml.nonNumeric', 'Non-numeric'), class: 'status-outside' };
  }
  if (val < 0) {
    return { state: 'invalid', label: t('ml.cannotBeNegative', 'Cannot be negative'), class: 'status-outside' };
  }

  const ref = WDBC_DEVELOPMENT_REFERENCE[feature];
  if (!ref) {
    return { state: 'common', label: t('ml.inputSet', 'Input set'), class: 'status-common' };
  }

  if (val < ref.min || val > ref.max) {
    return {
      state: 'outside',
      label: `${t('ml.rangeOutside', 'Outside observed')} (${val < ref.min ? `< ${ref.min}` : `> ${ref.max}`})`,
      class: 'status-outside',
      min: ref.min,
      max: ref.max,
    };
  }
  if (val < ref.p01 || val > ref.p99) {
    return { state: 'extreme', label: t('ml.rangeExtreme', 'Extreme (outside P1–P99)'), class: 'status-extreme' };
  }
  if (val < ref.p05 || val > ref.p95) {
    return { state: 'unusual', label: t('ml.rangeUnusual', 'Unusual (outside P5–P95)'), class: 'status-unusual' };
  }
  return { state: 'common', label: t('ml.rangeCommon', 'Common range (P5–P95)'), class: 'status-common' };
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
      const st = getFieldReferenceState(feat, val);
      if (st.state === 'common') common++;
      else if (st.state === 'unusual') unusual++;
      else if (st.state === 'extreme') extreme++;
      else if (st.state === 'outside') {
        outside++;
        outliers.push({ feature: feat, value: Number(val), min: st.min, max: st.max });
      }
    }
  }

  return { completed, common, unusual, extreme, outside, outliers };
}

// Main Render Function
function render() {
  const quality = computeInputQuality();
  const selectedPatient = state.patients.find((p) => String(p.id) === String(state.selectedPatientId));

  app.innerHTML = `
    <div class="ml-workstation">
      <!-- 1. Hero & Model Context -->
      <header class="ml-hero">
        <div class="ml-hero-eyebrow">
          <span>${t('ml.heroEyebrow')}</span>
        </div>
        <h1>${t('ml.heroTitle')}</h1>
        <p class="ml-hero-desc">
          ${t('ml.heroDesc')}
        </p>
        <div class="ml-hero-specs">
          <span class="ml-spec-pill">${t('ml.specModel')}</span>
          <span class="ml-spec-pill">${t('ml.specDataset')}</span>
          <span class="ml-spec-pill">${t('ml.specHoldout')}</span>
          <span class="ml-spec-pill">${t('ml.specThreshold')}</span>
          <span class="ml-spec-pill">${t('ml.specClinical')}</span>
        </div>
      </header>

      <!-- 2. Doctor Patient Context (Visible only to doctors) -->
      ${isDoctor ? `
        <div class="doctor-patient-bar">
          <div class="doctor-patient-info">
            <span class="doctor-patient-badge">${t('ml.doctorBadge')}</span>
            <span>
              ${selectedPatient
                ? `${t('ml.analyzingFor')} <strong>${esc(selectedPatient.full_name)}</strong> (ID: ${selectedPatient.id})`
                : t('ml.noPatientSelected')
              }
            </span>
            ${selectedPatient ? `<a href="/pages/patients.html" class="v2-link" style="margin-left:8px;">${t('ml.viewPatient')}</a>` : ''}
          </div>
          <div class="doctor-patient-controls">
            <label for="doctorPatientSelect" style="font-size:0.82rem;font-weight:600;color:#166534;">${t('ml.attachToPatient')}</label>
            <select id="doctorPatientSelect" class="doctor-patient-select">
              <option value="">${t('ml.noPatientOption')}</option>
              ${state.patients.map((p) => `
                <option value="${p.id}" ${String(p.id) === String(state.selectedPatientId) ? 'selected' : ''}>
                  ${esc(p.full_name)} (DOB: ${esc(p.date_of_birth || 'N/A')})
                </option>
              `).join('')}
            </select>
          </div>
        </div>
      ` : ''}

      <!-- 3. Quick Entry Toolbar -->
      <section class="ml-toolbar" aria-label="Quick Entry Toolbar">
        <div class="ml-toolbar-actions">
          <button type="button" class="ml-tool-btn" id="btnImportCsv">
            <span>📥</span> ${t('ml.importCsv')}
          </button>
          <button type="button" class="ml-tool-btn" id="btnExtractOcr">
            <span>📷</span> ${t('ml.extractOcr')}
          </button>
          <button type="button" class="ml-tool-btn primary-sample" id="btnSampleBenign" title="Loads canonical WDBC development Row 19">
            <span>🔬</span> ${t('ml.loadBenign')}
          </button>
          <button type="button" class="ml-tool-btn primary-sample" id="btnSampleMalignant" title="Loads canonical WDBC development Row 0">
            <span>🔬</span> ${t('ml.loadMalignant')}
          </button>
          <button type="button" class="ml-tool-btn danger-action" id="btnClearAll">
            <span>🗑️</span> ${t('ml.clearAll')}
          </button>
        </div>

        <div class="ml-toolbar-meta">
          <button type="button" class="ml-tool-btn" id="btnDownloadTemplate" style="background:#fff;">
            <span>📄</span> ${t('ml.downloadTemplate')}
          </button>
          <button type="button" class="ml-tool-btn" id="btnDownloadExample" style="background:#fff;">
            <span>📄</span> ${t('ml.downloadExample')}
          </button>
          <span class="ml-progress-pill" id="toolbarProgressPill">
            <span id="count">${quality.completed} / 30</span> ${t('common.status', 'complete')}
          </span>
        </div>
      </section>

      <!-- Hidden file inputs -->
      <input type="file" id="fileCsvInput" accept=".csv,text/csv" style="display:none;">
      <input type="file" id="fileOcrInput" accept="image/jpeg,image/png,image/webp" style="display:none;">

      <!-- 4. Two-Column Workspace: Left Features + Right Sticky Sidebar -->
      <div class="ml-workspace-grid">
        <!-- LEFT: Feature Workspace -->
        <div class="ml-feature-workspace">
          <!-- Group Navigation Tabs -->
          <nav class="ml-group-nav" aria-label="Feature Groups">
            <button type="button" class="ml-group-tab ${state.activeTab === 'all' ? 'active' : ''}" data-tab="all">
              ${t('ml.tabAll')}
            </button>
            <button type="button" class="ml-group-tab ${state.activeTab === 'mean' ? 'active' : ''}" data-tab="mean">
              ${t('ml.tabMean')}
            </button>
            <button type="button" class="ml-group-tab ${state.activeTab === 'se' ? 'active' : ''}" data-tab="se">
              ${t('ml.tabSe')}
            </button>
            <button type="button" class="ml-group-tab ${state.activeTab === 'worst' ? 'active' : ''}" data-tab="worst">
              ${t('ml.tabWorst')}
            </button>
          </nav>

          <!-- Form with Feature Sections -->
          <form id="analysis" class="ml-workstation-form" novalidate>
            <button type="submit" id="btnSubmitHidden" style="position:absolute;width:0;height:0;opacity:0;pointer-events:none;"></button>
            ${renderFeatureGroups()}
          </form>
        </div>

        <!-- RIGHT: Sticky Lab Sidebar -->
        <aside class="ml-sidebar" aria-label="Execution and Input Quality">
          <!-- Run Execution Panel -->
          <div class="ml-side-panel">
            <h3>
              <span>⚡ ${t('ml.modelExecution')}</span>
              <span style="font-size:0.75rem;color:#0f766e;font-weight:600;">${t('ml.frozenCandidate')}</span>
            </h3>

            <div class="ml-sidebar-meter">
              <div class="ml-sidebar-meter-label">
                <span>${t('ml.inputCompletion')}</span>
                <strong id="sidebarProgressCount">${quality.completed} / 30</strong>
              </div>
              <div class="ml-sidebar-progress-bar">
                <div class="ml-sidebar-progress-fill" style="width: ${(quality.completed / 30) * 100}%;"></div>
              </div>
            </div>

            <p style="font-size:0.78rem;color:#64748b;line-height:1.4;margin:12px 0 16px;">
              ${t('ml.executionNote')}
            </p>

            <button
              type="button"
              class="ml-run-btn"
              id="btnRunModel"
              ${quality.completed < 30 ? 'disabled' : ''}
            >
              ${t('ml.runModelBtn')}
            </button>
          </div>

          <!-- Live Input Quality Review -->
          <div class="ml-side-panel">
            <h3>
              <span>📊 ${t('ml.devDataFit')}</span>
              <span style="font-size:0.72rem;color:#64748b;">${t('ml.devCohort')}</span>
            </h3>
            <ul class="ml-quality-list">
              <li class="ml-quality-item">
                <span>${t('ml.rangeCommon')}</span>
                <span class="ml-quality-tag" style="background:#dcfce7;color:#15803d;">${quality.common}</span>
              </li>
              <li class="ml-quality-item">
                <span>${t('ml.rangeUnusual')}</span>
                <span class="ml-quality-tag" style="background:#fef3c7;color:#b45309;">${quality.unusual}</span>
              </li>
              <li class="ml-quality-item">
                <span>${t('ml.rangeExtreme')}</span>
                <span class="ml-quality-tag" style="background:#fed7aa;color:#c2410c;">${quality.extreme}</span>
              </li>
              <li class="ml-quality-item">
                <span>${t('ml.rangeOutside')}</span>
                <span class="ml-quality-tag" style="background:#fee2e2;color:#b91c1c;">${quality.outside}</span>
              </li>
            </ul>

            ${quality.outliers.length > 0 ? `
              <div style="margin-top:14px;padding:10px;background:#fff5f5;border:1px solid #fecaca;border-radius:6px;">
                <div style="font-size:0.78rem;font-weight:700;color:#b91c1c;margin-bottom:4px;">
                  ${t('ml.outliersWarning', { count: quality.outliers.length })}
                </div>
                <div style="font-size:0.72rem;color:#7f1d1d;line-height:1.3;">
                  ${t('ml.outliersNote')}
                </div>
              </div>
            ` : ''}
          </div>

          <!-- Scientific Cytology Scope -->
          <div class="ml-side-panel" style="background:#f8fafc;">
            <h4 style="font-size:0.82rem;font-weight:700;color:#334155;margin:0 0 8px;">
              ℹ️ ${t('ml.cytologyScopeTitle')}
            </h4>
            <p style="font-size:0.74rem;color:#64748b;line-height:1.4;margin:0;">
              ${t('ml.cytologyScopeDesc')}
            </p>
          </div>
        </aside>
      </div>

      <!-- 5. Rich Result Workspace (Rendered after prediction) -->
      <div id="result" class="ml-result-container">
        ${state.result ? renderResultWorkspace(state.result) : ''}
      </div>

      <!-- Modal Dialog Overlays -->
      ${renderModal()}
    </div>
  `;

  attachEventListeners();
}

// Render Feature Groups based on active tab
function renderFeatureGroups() {
  const groupsToRender = ML_GROUPS.filter(([title]) => {
    if (state.activeTab === 'all') return true;
    if (state.activeTab === 'mean') return title.startsWith('Mean');
    if (state.activeTab === 'se') return title.startsWith('Standard');
    if (state.activeTab === 'worst') return title.startsWith('Worst');
    return true;
  });

  return groupsToRender.map(([title, features]) => {
    const completedInGroup = features.filter((f) => state.inputs[f] !== '' && !Number.isNaN(Number(state.inputs[f]))).length;
    const desc = GROUP_DESCRIPTIONS[title] || '';

    return `
      <section class="ml-group-section" id="section-${title.replace(/\s+/g, '-').toLowerCase()}">
        <div class="ml-group-header">
          <h2>${title}</h2>
          <span class="ml-group-progress">${completedInGroup} / ${features.length} complete</span>
        </div>
        <p class="ml-group-desc">${desc}</p>

        <div class="ml-fields-grid">
          ${features.map((feat) => renderFeatureCard(feat)).join('')}
        </div>
      </section>
    `;
  }).join('');
}

// Render Individual Feature Card
function renderFeatureCard(feature) {
  const value = state.inputs[feature] ?? '';
  const ref = WDBC_DEVELOPMENT_REFERENCE[feature] || {};
  const status = getFieldReferenceState(feature, value);
  const displayName = ref.display_name || featureLabel(feature);

  return `
    <div class="ml-field-card" id="card-${feature}">
      <div class="ml-field-header">
        <label for="input-${feature}" class="ml-field-label">${displayName}</label>
        <span class="ml-ref-status-badge ${status.class}" id="badge-${feature}">
          ${status.label}
        </span>
      </div>

      <input
        type="number"
        step="any"
        min="0"
        class="ml-field-input-box"
        id="input-${feature}"
        name="${feature}"
        data-feature="${feature}"
        value="${esc(value)}"
        placeholder="e.g. ${ref.median ?? '14.2'}"
        aria-describedby="ref-${feature} desc-${feature}"
        required
      >

      <div class="ml-field-footer">
        <div class="ml-ref-line" id="ref-${feature}">
          WDBC dev P5–P95: ${ref.p05 ?? '—'} – ${ref.p95 ?? '—'}
        </div>
        <div class="ml-ref-desc" id="desc-${feature}">
          ${ref.description ?? 'FNA nuclear morphology measurement.'}
        </div>
      </div>
    </div>
  `;
}

// Render Result Workspace
function renderResultWorkspace(r) {
  const prob = Number(r.raw_probability ?? r.probability);
  const threshold = Number(r.decision_threshold ?? 0.36);
  const isMalignant = prob >= threshold;
  const distancePct = ((prob - threshold) * 100).toFixed(1);
  const distanceSign = Number(distancePct) >= 0 ? `+${distancePct}` : distancePct;

  const topFeatures = r.top_features || [];
  const allFeatures = r.all_features || topFeatures;
  const malignantContributors = topFeatures.filter((f) => f.direction === 'toward_malignant').slice(0, 5);
  const benignContributors = topFeatures.filter((f) => f.direction === 'toward_benign').slice(0, 5);

  // Sorting for full table
  const sortedFeatures = [...allFeatures].sort((a, b) => {
    if (state.sortBy === 'malignant') return b.log_odds_contribution - a.log_odds_contribution;
    if (state.sortBy === 'benign') return a.log_odds_contribution - b.log_odds_contribution;
    if (state.sortBy === 'unusual') {
      const order = { outside_observed: 4, extreme: 3, unusual: 2, within_reference: 1 };
      return (order[b.reference_state] || 0) - (order[a.reference_state] || 0);
    }
    if (state.sortBy === 'default') return ML_FEATURES.indexOf(a.feature) - ML_FEATURES.indexOf(b.feature);
    return Math.abs(b.log_odds_contribution) - Math.abs(a.log_odds_contribution);
  });

  const quality = r.input_quality || computeInputQuality();
  const predictionId = r.prediction_id || r.id;

  return `
    <section class="ml-result-workspace" id="mlResultWorkspace" aria-live="polite">
      <!-- Section A: Classification Banner -->
      <div class="ml-result-header">
        <span class="ml-hero-eyebrow" style="color:#0f766e;margin-bottom:12px;">
          ${t('ml.executionComplete')}
        </span>

        <div class="ml-classification-banner ${isMalignant ? 'malignant' : 'benign'}">
          <div>
            <div style="font-size:0.8rem;font-weight:700;text-transform:uppercase;color:#475569;margin-bottom:6px;">
              ${t('ml.modelClassification')}
            </div>
            <span class="ml-class-badge ${isMalignant ? 'malignant' : 'benign'}">
              ${isMalignant ? t('common.malignant') : t('common.benign')}
            </span>
          </div>

          <div class="ml-prob-metric">
            <div class="ml-prob-number">
              ${(prob * 100).toFixed(1)}%
            </div>
            <div class="ml-prob-sub">
              ${t('ml.rawMalignantProb')} (${distanceSign} pp)
            </div>
          </div>
        </div>

        <p style="font-size:0.82rem;color:#64748b;margin:0;line-height:1.4;">
          ${t('ml.researchDisclaimer')}
        </p>
      </div>

      <!-- Section B: Why Did the Model Return This? -->
      <section class="ml-contrib-section">
        <h3>${t('ml.whyModelResponded')}</h3>
        <p class="ml-contrib-note">
          ${t('ml.contribFormula')}
        </p>

        <div class="ml-contrib-columns">
          <!-- Pushing Toward Benign -->
          <div class="ml-contrib-card benign">
            <h4><span>⬅️</span> ${t('ml.pushingBenign')} (${benignContributors.length})</h4>
            ${benignContributors.length === 0 ? `<p style="font-size:0.84rem;color:#64748b;">${t('ml.noStrongBenign')}</p>` : ''}
            ${benignContributors.map((feat) => {
              const maxVal = 5.0; // visual cap
              const fillPct = Math.min(100, Math.round((Math.abs(feat.log_odds_contribution) / maxVal) * 100));
              return `
                <div class="ml-contrib-row">
                  <div class="ml-contrib-row-header">
                    <span>${esc(feat.display_name)} (${feat.raw_value})</span>
                    <strong>${feat.log_odds_contribution}</strong>
                  </div>
                  <div class="ml-contrib-bar-wrap">
                    <div class="ml-contrib-bar-fill benign" style="width:${fillPct}%;"></div>
                  </div>
                </div>
              `;
            }).join('')}
          </div>

          <!-- Pushing Toward Malignant -->
          <div class="ml-contrib-card malignant">
            <h4><span>➡️</span> ${t('ml.pushingMalignant')} (${malignantContributors.length})</h4>
            ${malignantContributors.length === 0 ? `<p style="font-size:0.84rem;color:#64748b;">${t('ml.noStrongMalignant')}</p>` : ''}
            ${malignantContributors.map((feat) => {
              const maxVal = 5.0; // visual cap
              const fillPct = Math.min(100, Math.round((Math.abs(feat.log_odds_contribution) / maxVal) * 100));
              return `
                <div class="ml-contrib-row">
                  <div class="ml-contrib-row-header">
                    <span>${esc(feat.display_name)} (${feat.raw_value})</span>
                    <strong>+${feat.log_odds_contribution}</strong>
                  </div>
                  <div class="ml-contrib-bar-wrap">
                    <div class="ml-contrib-bar-fill malignant" style="width:${fillPct}%;"></div>
                  </div>
                </div>
              `;
            }).join('')}
          </div>
        </div>
      </section>

      <!-- Section C: Input Quality Review -->
      <section style="margin:24px 0;padding:16px;background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;">
        <h4 style="font-size:0.95rem;font-weight:700;color:#0f172a;margin:0 0 8px;">
          ${t('ml.devDataFit')}
        </h4>
        <p style="font-size:0.82rem;color:#475569;margin:0 0 12px;line-height:1.4;">
          ${t('ml.cytologyScopeDesc')}
        </p>
        <div style="display:flex;flex-wrap:wrap;gap:12px;font-size:0.82rem;">
          <span style="background:#dcfce7;color:#15803d;padding:4px 10px;border-radius:4px;font-weight:600;">
            ${quality.within_common_range_count ?? quality.common} ${t('ml.rangeCommon')}
          </span>
          <span style="background:#fef3c7;color:#b45309;padding:4px 10px;border-radius:4px;font-weight:600;">
            ${quality.unusual_count ?? quality.unusual} ${t('ml.rangeUnusual')}
          </span>
          <span style="background:#fed7aa;color:#c2410c;padding:4px 10px;border-radius:4px;font-weight:600;">
            ${quality.extreme_count ?? quality.extreme} ${t('ml.rangeExtreme')}
          </span>
          ${(quality.outside_observed_count ?? quality.outside) > 0 ? `
            <span style="background:#fee2e2;color:#b91c1c;padding:4px 10px;border-radius:4px;font-weight:600;">
              ${quality.outside_observed_count ?? quality.outside} ${t('ml.rangeOutside')}
            </span>
          ` : ''}
        </div>
      </section>

      <!-- Section D: Full Feature Breakdown Table -->
      <section style="margin:32px 0;">
        <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;margin-bottom:12px;">
          <h4 style="font-size:1.1rem;font-weight:700;color:#0f172a;margin:0;">
            ${t('ml.fullContribTitle')}
          </h4>
          <div style="display:flex;gap:8px;flex-wrap:wrap;">
            <button type="button" class="ml-tool-btn ${state.sortBy === 'mag' ? 'primary-sample' : ''}" data-sort="mag">
              ${t('ml.sortMag')}
            </button>
            <button type="button" class="ml-tool-btn ${state.sortBy === 'malignant' ? 'primary-sample' : ''}" data-sort="malignant">
              ${t('ml.sortMal')}
            </button>
            <button type="button" class="ml-tool-btn ${state.sortBy === 'benign' ? 'primary-sample' : ''}" data-sort="benign">
              ${t('ml.sortBen')}
            </button>
            <button type="button" class="ml-tool-btn ${state.sortBy === 'unusual' ? 'primary-sample' : ''}" data-sort="unusual">
              ${t('ml.sortUnusual')}
            </button>
            <button type="button" class="ml-tool-btn ${state.sortBy === 'default' ? 'primary-sample' : ''}" data-sort="default">
              ${t('ml.sortDefault')}
            </button>
          </div>
        </div>

        <div class="ml-table-container">
          <table class="ml-breakdown-table">
            <thead>
              <tr>
                <th>${t('ml.thFeature')}</th>
                <th>${t('ml.thRaw')}</th>
                <th>WDBC P5–P95</th>
                <th>${t('ml.thCohortState')}</th>
                <th>${t('ml.thVisualImpact')}</th>
                <th>${t('ml.thContrib')}</th>
              </tr>
            </thead>
            <tbody>
              ${sortedFeatures.map((f) => {
                const ref = WDBC_DEVELOPMENT_REFERENCE[f.feature] || {};
                const isMal = f.direction === 'toward_malignant';
                return `
                  <tr>
                    <td><strong>${esc(f.display_name || featureLabel(f.feature))}</strong></td>
                    <td>${f.raw_value}</td>
                    <td>${ref.p05 ?? '—'} – ${ref.p95 ?? '—'}</td>
                    <td>
                      <span class="ml-ref-status-badge ${
                        f.reference_state === 'outside_observed' ? 'status-outside' :
                        f.reference_state === 'extreme' ? 'status-extreme' :
                        f.reference_state === 'unusual' ? 'status-unusual' : 'status-common'
                      }">
                        ${f.reference_state ? f.reference_state.replace(/_/g, ' ') : 'common'}
                      </span>
                    </td>
                    <td>
                      <span style="font-weight:700;color:${isMal ? '#dc2626' : '#0284c7'};">
                        ${isMal ? 'Toward Malignant ➡️' : 'Toward Benign ⬅️'}
                      </span>
                    </td>
                    <td><strong>${f.log_odds_contribution > 0 ? `+${f.log_odds_contribution}` : f.log_odds_contribution}</strong></td>
                  </tr>
                `;
              }).join('')}
            </tbody>
          </table>
        </div>
      </section>

      <!-- Section E & F: AI Educational Guidance & General Wellbeing -->
      <div class="ml-guidance-grid">
        <!-- AI Educational Guidance -->
        <article class="ml-guidance-card ai-advice">
          <h4><span>💡</span> AI Educational Guidance</h4>
          <p>${esc(r.advice || 'AI educational guidance is currently being generated. Review with a medical professional.')}</p>
          <div class="ml-guidance-meta">
            Provider: <strong>${esc(r.advice_provider || 'rule_engine')}</strong> ·
            Model: <strong>${esc(r.advice_model || 'wdbc_advisory_v1')}</strong>
          </div>
        </article>

        <!-- General Wellbeing Guidance -->
        <article class="ml-guidance-card wellbeing">
          <h4><span>🌱</span> General Wellbeing Guidance</h4>
          <p>
            General health behaviors support recovery and treatment tolerance: prioritize balanced whole-food meals, adequate hydration, regular gentle physical activity as tolerated, and consistent sleep patterns.
          </p>
          <div class="ml-guidance-meta">
            Evidence source: Standard clinical oncology lifestyle & nutrition guidelines. This advice is decoupled from specific nuclear morphology values.
          </div>
        </article>
      </div>

      <!-- Section G: Action Row -->
      <div class="ml-result-actions">
        ${predictionId ? `
          <button type="button" class="ml-action-btn report" id="btnViewReport" data-prediction-id="${predictionId}">
            <span>📄</span> View Analysis Report
          </button>
        ` : ''}

        <button type="button" class="ml-action-btn advisor" id="btnAskAdvisor">
          <span>💬</span> Ask AI Guide About This Result
        </button>

        <button type="button" class="ml-action-btn secondary" id="btnResultClear">
          <span>🔄</span> Reset Workspace
        </button>
      </div>
    </section>
  `;
}

// Render Modal Dialogs (CSV, OCR, Outlier Confirmation)
function renderModal() {
  if (!state.modal) return '';

  if (state.modal === 'csv') {
    const { isMultiRow, rows, rowCount } = state.modalData;
    return `
      <div class="ml-modal-overlay" role="dialog" aria-modal="true">
        <div class="ml-modal-content">
          <div class="ml-modal-header">
            <h3>Import CSV: ${isMultiRow ? `Multiple Rows Detected (${rowCount})` : 'Single Row Preview'}</h3>
            <button type="button" class="ml-modal-close" id="btnModalClose">&times;</button>
          </div>
          <div class="ml-modal-body">
            <p style="font-size:0.86rem;color:#475569;margin:0 0 16px;">
              ${isMultiRow
                ? 'Select exactly ONE sample row to load into the workstation. Bulk prediction is not supported.'
                : 'Review the parsed values before loading them into the feature workspace.'
              }
            </p>

            <div class="ml-table-container" style="max-height:300px;">
              <table class="ml-breakdown-table">
                <thead>
                  <tr>
                    <th>Select</th>
                    <th>Row</th>
                    <th>ID / Label</th>
                    <th>Completion</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  ${rows.map((row, idx) => `
                    <tr>
                      <td>
                        <input
                          type="radio"
                          name="csvRowSelect"
                          value="${idx}"
                          ${idx === 0 ? 'checked' : ''}
                          ${!row.valid ? 'disabled' : ''}
                        >
                      </td>
                      <td>#${row.rowNumber}</td>
                      <td>${esc(row.id || 'N/A')}</td>
                      <td>${row.completedCount} / 30</td>
                      <td>
                        ${row.valid
                          ? '<span style="color:#16a34a;font-weight:700;">✓ Valid</span>'
                          : `<span style="color:#dc2626;font-size:0.75rem;">${esc(row.errors[0])}</span>`
                        }
                      </td>
                    </tr>
                  `).join('')}
                </tbody>
              </table>
            </div>
          </div>
          <div class="ml-modal-footer">
            <button type="button" class="ml-tool-btn" id="btnModalCancel">Cancel</button>
            <button type="button" class="ml-run-btn" id="btnModalLoadCsvRow" style="width:auto;">
              Load Selected Row
            </button>
          </div>
        </div>
      </div>
    `;
  }

  if (state.modal === 'ocr') {
    const data = state.modalData;
    return `
      <div class="ml-modal-overlay" role="dialog" aria-modal="true">
        <div class="ml-modal-content" style="max-width:820px;">
          <div class="ml-modal-header">
            <h3>Report Image Extraction Review</h3>
            <button type="button" class="ml-modal-close" id="btnModalClose">&times;</button>
          </div>
          <div class="ml-modal-body">
            <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:14px;flex-wrap:wrap;gap:8px;">
              <div>
                Extracted: <strong>${data.filled_count} / 30</strong> fields
              </div>
              <div style="font-size:0.8rem;background:#f1f5f9;padding:4px 10px;border-radius:6px;">
                Provider: <strong>${esc(data.provider)}</strong> (${esc(data.model)})
              </div>
            </div>

            <p style="font-size:0.84rem;color:#475569;margin-bottom:14px;">
              Please inspect the extracted values below. You may edit any value before loading into the workstation.
            </p>

            <div class="ml-table-container" style="max-height:360px;">
              <table class="ml-breakdown-table">
                <thead>
                  <tr>
                    <th>Feature</th>
                    <th>Extracted Value</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  ${ML_FEATURES.map((feat) => {
                    const val = data.values?.[feat];
                    const hasVal = val !== null && val !== undefined && !Number.isNaN(Number(val));
                    return `
                      <tr>
                        <td><strong>${esc(featureLabel(feat))}</strong></td>
                        <td>
                          <input
                            type="number"
                            step="any"
                            min="0"
                            class="ml-field-input-box"
                            style="padding:4px 8px;font-size:0.86rem;width:140px;"
                            id="ocr-edit-${feat}"
                            value="${hasVal ? val : ''}"
                          >
                        </td>
                        <td>
                          ${hasVal
                            ? '<span style="color:#16a34a;font-weight:700;">✓ Extracted</span>'
                            : '<span style="color:#f59e0b;font-weight:700;">Missing</span>'
                          }
                        </td>
                      </tr>
                    `;
                  }).join('')}
                </tbody>
              </table>
            </div>
          </div>
          <div class="ml-modal-footer">
            <button type="button" class="ml-tool-btn" id="btnModalCancel">Cancel</button>
            <button type="button" class="ml-run-btn" id="btnModalLoadOcr" style="width:auto;">
              Load Extracted Values
            </button>
          </div>
        </div>
      </div>
    `;
  }

  if (state.modal === 'outlier') {
    const outliers = state.modalData.outliers;
    return `
      <div class="ml-modal-overlay" role="dialog" aria-modal="true">
        <div class="ml-modal-content">
          <div class="ml-modal-header" style="border-bottom:2px solid #fecaca;background:#fff5f5;">
            <h3 style="color:#b91c1c;">⚠️ Review Values Outside Observed Development Cohort</h3>
            <button type="button" class="ml-modal-close" id="btnModalClose">&times;</button>
          </div>
          <div class="ml-modal-body">
            <p style="font-size:0.88rem;color:#334155;line-height:1.5;margin-bottom:14px;">
              The following ${outliers.length} value(s) are outside the minimum and maximum ranges observed in the 455-sample WDBC development dataset.
              Please verify that they were not entered by mistake (e.g. typos or misplaced decimal points).
            </p>

            <div class="ml-table-container">
              <table class="ml-breakdown-table">
                <thead>
                  <tr>
                    <th>Feature</th>
                    <th>Entered Value</th>
                    <th>Observed Min–Max</th>
                  </tr>
                </thead>
                <tbody>
                  ${outliers.map((o) => `
                    <tr>
                      <td><strong>${esc(featureLabel(o.feature))}</strong></td>
                      <td style="color:#b91c1c;font-weight:800;">${o.value}</td>
                      <td>${o.min} – ${o.max}</td>
                    </tr>
                  `).join('')}
                </tbody>
              </table>
            </div>
          </div>
          <div class="ml-modal-footer">
            <button type="button" class="ml-tool-btn" id="btnModalCancel">Go Back & Edit</button>
            <button type="button" class="ml-run-btn" id="btnModalConfirmOutlier" style="width:auto;background:#b91c1c;">
              I Reviewed These Values — Run Model
            </button>
          </div>
        </div>
      </div>
    `;
  }

  return '';
}

// Event Listeners Binding
function attachEventListeners() {
  // Input changes
  document.querySelectorAll('.ml-field-input-box').forEach((input) => {
    input.addEventListener('input', (e) => {
      const feat = e.target.dataset.feature;
      if (!feat) return;
      state.inputs[feat] = e.target.value.trim();
      state.outlierConfirmed = false;

      // Update badge dynamically
      const status = getFieldReferenceState(feat, e.target.value.trim());
      const badge = document.querySelector(`#badge-${feat}`);
      if (badge) {
        badge.className = `ml-ref-status-badge ${status.class}`;
        badge.textContent = status.label;
      }

      // Update progress
      const q = computeInputQuality();
      const toolbarProgress = document.querySelector('#toolbarProgressPill');
      if (toolbarProgress) toolbarProgress.textContent = `${q.completed} / 30 fields complete`;
      const sidebarCount = document.querySelector('#sidebarProgressCount');
      if (sidebarCount) sidebarCount.textContent = `${q.completed} / 30`;
      const sidebarFill = document.querySelector('.ml-sidebar-progress-fill');
      if (sidebarFill) sidebarFill.style.width = `${(q.completed / 30) * 100}%`;

      const btnRun = document.querySelector('#btnRunModel');
      if (btnRun) btnRun.disabled = q.completed < 30;
    });
  });

  // Form submission and programmatic input sync
  const formEl = document.querySelector('#analysis');
  if (formEl) {
    formEl.addEventListener('submit', (e) => {
      e.preventDefault();
      handleRun();
    });
    formEl.addEventListener('input', () => {
      for (const feat of ML_FEATURES) {
        if (formEl.elements[feat] && formEl.elements[feat].value !== state.inputs[feat]) {
          state.inputs[feat] = formEl.elements[feat].value.trim();
        }
      }
      const q = computeInputQuality();
      const countEl = document.querySelector('#count');
      if (countEl) countEl.textContent = `${q.completed} / 30`;
      const toolbarProgress = document.querySelector('#toolbarProgressPill');
      if (toolbarProgress) toolbarProgress.innerHTML = `<span id="count">${q.completed} / 30</span> fields complete`;
      const sidebarCount = document.querySelector('#sidebarProgressCount');
      if (sidebarCount) sidebarCount.textContent = `${q.completed} / 30`;
      const sidebarFill = document.querySelector('.ml-sidebar-progress-fill');
      if (sidebarFill) sidebarFill.style.width = `${(q.completed / 30) * 100}%`;
      const btnRun = document.querySelector('#btnRunModel');
      if (btnRun) btnRun.disabled = q.completed < 30;
    });
  }

  // Group tabs
  document.querySelectorAll('.ml-group-tab').forEach((tab) => {
    tab.addEventListener('click', (e) => {
      state.activeTab = e.target.dataset.tab;
      render();
    });
  });

  // Doctor patient selector
  const patientSelect = document.querySelector('#doctorPatientSelect');
  if (patientSelect) {
    patientSelect.addEventListener('change', (e) => {
      state.selectedPatientId = e.target.value;
      render();
    });
  }

  // Quick toolbar: Sample Benign
  document.querySelector('#btnSampleBenign')?.addEventListener('click', () => {
    Object.assign(state.inputs, SAMPLES.benign);
    state.outlierConfirmed = false;
    render();
  });

  // Quick toolbar: Sample Malignant
  document.querySelector('#btnSampleMalignant')?.addEventListener('click', () => {
    Object.assign(state.inputs, SAMPLES.malignant);
    state.outlierConfirmed = false;
    render();
  });

  // Quick toolbar: Clear All
  document.querySelector('#btnClearAll')?.addEventListener('click', () => {
    const quality = computeInputQuality();
    if (quality.completed > 0 || state.result) {
      if (!window.confirm('Clear all inputs and results from the workspace?')) return;
    }
    state.inputs = Object.fromEntries(ML_FEATURES.map((f) => [f, '']));
    state.result = null;
    state.outlierConfirmed = false;
    render();
  });

  // Quick toolbar: Download Template
  document.querySelector('#btnDownloadTemplate')?.addEventListener('click', () => {
    const csvContent = generateCsvTemplate();
    downloadBlob(csvContent, 'wdbc_features_template.csv', 'text/csv');
  });

  // Quick toolbar: Download Example CSV
  document.querySelector('#btnDownloadExample')?.addEventListener('click', () => {
    const csvContent = generateExampleCsv(SAMPLES.benign);
    downloadBlob(csvContent, 'wdbc_benign_example.csv', 'text/csv');
  });

  // Quick toolbar: Import CSV
  const csvFileInput = document.querySelector('#fileCsvInput');
  document.querySelector('#btnImportCsv')?.addEventListener('click', () => {
    csvFileInput?.click();
  });
  csvFileInput?.addEventListener('change', (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      try {
        const parsed = parseClinicalCsv(reader.result);
        if (parsed.isMultiRow) {
          state.modal = 'csv';
          state.modalData = parsed;
          render();
        } else {
          // Single row
          const firstRow = parsed.rows[0];
          if (!firstRow.valid) {
            alert(`CSV Error: ${firstRow.errors.join(' ')}`);
            return;
          }
          Object.assign(state.inputs, firstRow.values);
          state.outlierConfirmed = false;
          render();
        }
      } catch (err) {
        alert(err.message || 'Failed to parse CSV.');
      } finally {
        csvFileInput.value = '';
      }
    };
    reader.readAsText(file);
  });

  // Quick toolbar: Extract from Report Image
  const ocrFileInput = document.querySelector('#fileOcrInput');
  document.querySelector('#btnExtractOcr')?.addEventListener('click', () => {
    ocrFileInput?.click();
  });
  ocrFileInput?.addEventListener('change', async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const btn = document.querySelector('#btnExtractOcr');
    const originalText = btn ? btn.innerHTML : '';
    if (btn) btn.innerHTML = '<span>⏳</span> Analyzing...';

    try {
      const data = await predictionService.extractClinical(file);
      state.modal = 'ocr';
      state.modalData = data;
      render();
    } catch (err) {
      alert(`OCR Extraction Failed: ${err.message}`);
    } finally {
      if (btn) btn.innerHTML = originalText;
      ocrFileInput.value = '';
    }
  });

  // Run Frozen Model Execution
  document.querySelector('#btnRunModel')?.addEventListener('click', handleRun);

  // Result table sorting
  document.querySelectorAll('[data-sort]').forEach((btn) => {
    btn.addEventListener('click', (e) => {
      state.sortBy = e.currentTarget.dataset.sort;
      render();
    });
  });

  // Modal actions
  document.querySelector('#btnModalClose')?.addEventListener('click', closeModal);
  document.querySelector('#btnModalCancel')?.addEventListener('click', closeModal);

  document.querySelector('#btnModalLoadCsvRow')?.addEventListener('click', () => {
    const selectedRadio = document.querySelector('input[name="csvRowSelect"]:checked');
    if (!selectedRadio) return;
    const rowIndex = Number(selectedRadio.value);
    const row = state.modalData.rows[rowIndex];
    if (row && row.valid) {
      Object.assign(state.inputs, row.values);
      state.outlierConfirmed = false;
      closeModal();
      render();
    }
  });

  document.querySelector('#btnModalLoadOcr')?.addEventListener('click', () => {
    for (const feat of ML_FEATURES) {
      const input = document.querySelector(`#ocr-edit-${feat}`);
      if (input && input.value !== '') {
        state.inputs[feat] = input.value.trim();
      }
    }
    state.outlierConfirmed = false;
    closeModal();
    render();
  });

  document.querySelector('#btnModalConfirmOutlier')?.addEventListener('click', async () => {
    state.outlierConfirmed = true;
    closeModal();
    await executePrediction();
  });

  // Result action: View Report
  document.querySelector('#btnViewReport')?.addEventListener('click', (e) => {
    const pid = e.currentTarget.dataset.predictionId;
    if (pid) {
      reportService.open(pid);
    }
  });

  // Result action: Ask AI Guide
  document.querySelector('#btnAskAdvisor')?.addEventListener('click', () => {
    if (!state.result) return;
    const r = state.result;
    const topContribs = (r.top_features || []).slice(0, 4).map((f) => ({
      feature: f.display_name || f.feature,
      direction: f.direction,
      contribution: f.log_odds_contribution,
    }));

    const advisorContext = {
      prediction_id: r.prediction_id || r.id || null,
      model: 'Logistic Regression (WDBC)',
      dataset: 'WDBC',
      classification: r.diagnosis,
      raw_probability: r.raw_probability ?? r.probability,
      threshold: r.decision_threshold ?? 0.36,
      top_contributors: topContribs,
      input_quality_summary: r.input_quality || computeInputQuality(),
    };

    sessionStorage.setItem('bcai_advisor_context', JSON.stringify(advisorContext));
    window.location.href = '/pages/advisor.html';
  });

  // Result action: Reset
  document.querySelector('#btnResultClear')?.addEventListener('click', () => {
    state.result = null;
    render();
  });
}

function closeModal() {
  state.modal = null;
  state.modalData = null;
  render();
}

function downloadBlob(content, filename, type) {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

// Handle Run Workflow
async function handleRun() {
  const q = computeInputQuality();
  if (q.completed < 30) {
    alert('Please fill all 30 fields before running the model.');
    return;
  }

  // Check outliers safeguard
  if (q.outside > 0 && !state.outlierConfirmed) {
    state.modal = 'outlier';
    state.modalData = { outliers: q.outliers };
    render();
    return;
  }

  await executePrediction();
}

// Prediction Execution
async function executePrediction() {
  const btn = document.querySelector('#btnRunModel');
  if (btn) btn.disabled = true;
  const hiddenBtn = document.querySelector('#btnSubmitHidden');
  if (hiddenBtn) hiddenBtn.disabled = true;

  const resultContainer = document.querySelector('#result');
  if (resultContainer) {
    resultContainer.innerHTML = `
      <div style="background:#f0fdfa;border:1px solid #99f6e4;border-radius:12px;padding:24px;text-align:center;color:#0f766e;font-weight:600;margin-top:24px;">
        Running frozen Logistic Regression model…
      </div>
    `;
  }

  const steps = [
    'Validating inputs…',
    'Running frozen Logistic Regression…',
    'Calculating model contributions…',
    'Generating educational guidance…',
  ];

  let stepIdx = 0;
  const timer = setInterval(() => {
    stepIdx++;
    if (btn && steps[stepIdx]) {
      btn.textContent = steps[stepIdx];
    }
  }, 400);

  try {
    const payload = Object.fromEntries(
      ML_FEATURES.map((feat) => [feat, Number(state.inputs[feat])])
    );

    const result = await predictionService.ml(payload, {
      patientId: state.selectedPatientId || undefined,
    });

    state.result = result;
    render();

    // Scroll to results
    setTimeout(() => {
      document.querySelector('#mlResultWorkspace')?.scrollIntoView({ behavior: 'smooth' });
    }, 100);
  } catch (err) {
    alert(`Prediction failed: ${err.message || 'Unknown error'}`);
  } finally {
    clearInterval(timer);
    if (btn) {
      btn.disabled = false;
      btn.textContent = 'Run Frozen Model';
    }
  }
}

// Initial Setup
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

window.addEventListener('bcai:languageChanged', () => {
  render();
});

init();
