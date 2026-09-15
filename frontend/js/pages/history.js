import { requireAuth } from '../core/guards.js';
import { mountShell } from '../components/shell.js';
import { auth } from '../core/auth.js';
import { predictionService } from '../services/prediction.service.js';
import { patientService } from '../services/patient.service.js';
import { reportService } from '../services/report.service.js';
import { activityCardHtml, esc } from '../components/workspace.js';
import { t } from '../core/i18n.js';

if (requireAuth('../login.html?v=auth-v3')) {
  mountShell('Activity');
  initHistoryPage();
}

window.addEventListener('bcai:languageChanged', () => {
  initHistoryPage();
});

async function initHistoryPage() {
  const app = document.querySelector('#app');
  const user = auth.user();
  const isDoctor = user?.role === 'doctor';

  const searchParams = new URLSearchParams(location.search);
  const initialPatientId = searchParams.get('patient_id') || '';

  app.innerHTML = `
    <section class="research-main">
      <header class="research-hero">
        <span class="eyebrow">${isDoctor ? t('nav.doctorWorkspace') : t('profile.personalAccount')}</span>
        <h1>${isDoctor ? t('history.doctorTitle') : t('history.userTitle')}</h1>
        <p>${
          isDoctor
            ? t('history.doctorSubtitle')
            : t('history.userSubtitle')
        }</p>
      </header>

      <!-- Toolbar -->
      <div class="workspace-toolbar" style="flex-wrap: wrap; gap: 0.75rem; align-items: center;">
        <div class="workspace-toolbar-left" style="flex-wrap: wrap; gap: 0.75rem; align-items: center;">
          <div class="workspace-search-wrap">
            <svg class="workspace-search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="11" cy="11" r="8"></circle>
              <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
            </svg>
            <input type="search" id="historySearchInput" class="workspace-search-input" placeholder="${t('history.searchPlaceholder')}">
          </div>

          <select id="historyModalitySelect" class="workspace-select" aria-label="Filter by analysis modality">
            <option value="">${t('history.filterAll')}</option>
            <option value="ml">${t('history.filterMl')}</option>
            <option value="dl">${t('history.filterDl')}</option>
            <option value="multimodal">${t('history.filterMultimodal')}</option>
          </select>

          ${
            isDoctor
              ? `
            <select id="historyPatientSelect" class="workspace-select" aria-label="Filter by patient">
              <option value="">${t('history.filterAllPatients')}</option>
              <option value="unlinked">${t('history.filterStandalone')}</option>
            </select>
          `
              : ''
          }

          <div class="workspace-date-filter-group" style="display: flex; align-items: center; gap: 0.5rem;">
            <label for="historyDateFrom" style="font-size: 0.8125rem; font-weight: 500; color: var(--slate-600);">${t('history.fromDate')}</label>
            <input type="date" id="historyDateFrom" class="form-input" style="padding: 0.375rem 0.5rem; font-size: 0.8125rem; width: auto;" aria-label="Filter from date">
            <label for="historyDateTo" style="font-size: 0.8125rem; font-weight: 500; color: var(--slate-600);">${t('history.toDate')}</label>
            <input type="date" id="historyDateTo" class="form-input" style="padding: 0.375rem 0.5rem; font-size: 0.8125rem; width: auto;" aria-label="Filter to date">
          </div>

          <button type="button" id="historyClearFiltersBtn" class="studio-btn studio-btn-outline studio-btn-sm" style="height: 38px;">
            ${t('history.clearFilters')}
          </button>
        </div>

        <div class="workspace-toolbar-right" style="margin-left: auto;">
          <span id="historyCountBadge" class="patient-modality-pill has-analyses" style="font-size: 0.8125rem;">
            ${t('common.loading')}
          </span>
        </div>
      </div>

      <!-- Activity Feed List -->
      <div id="activityList">
        <div class="studio-card" style="text-align: center; padding: 2.5rem; color: var(--slate-500);">
          ${t('common.loading')}
        </div>
      </div>
    </section>
  `;

  const listEl = document.querySelector('#activityList');
  const searchInput = document.querySelector('#historySearchInput');
  const modalitySelect = document.querySelector('#historyModalitySelect');
  const patientSelect = document.querySelector('#historyPatientSelect');
  const dateFromInput = document.querySelector('#historyDateFrom');
  const dateToInput = document.querySelector('#historyDateTo');
  const clearFiltersBtn = document.querySelector('#historyClearFiltersBtn');
  const countBadge = document.querySelector('#historyCountBadge');

  let rows = [];
  let patientMap = new Map(); // id -> name

  async function loadData() {
    try {
      // Fix A: Load full history once so doctor can filter across all patients locally
      const promises = [predictionService.history()];
      if (isDoctor) {
        promises.push(patientService.list().catch(() => []));
      }

      const [historyData, patientList] = await Promise.all(promises);
      rows = Array.isArray(historyData) ? historyData : [];

      if (isDoctor && Array.isArray(patientList)) {
        patientList.forEach((p) => patientMap.set(p.id, p.full_name));

        if (patientSelect) {
          patientList.forEach((p) => {
            const opt = document.createElement('option');
            opt.value = String(p.id);
            opt.textContent = `Patient: ${p.full_name} (#${p.id})`;
            if (initialPatientId && String(p.id) === String(initialPatientId)) {
              opt.selected = true;
            }
            patientSelect.appendChild(opt);
          });
        }
      }

      renderList();
    } catch (err) {
      listEl.innerHTML = `
        <div class="studio-card error" style="padding: 1.5rem; color: #b91c1c;">
          <strong>Failed to load activity logs:</strong> ${esc(err.message || 'Server error')}
        </div>
      `;
      if (countBadge) countBadge.textContent = 'Error loading records';
    }
  }

  function getISODateOnly(dateStr) {
    if (!dateStr) return '';
    try {
      const d = new Date(dateStr);
      if (isNaN(d.getTime())) return '';
      return d.toISOString().slice(0, 10);
    } catch (_) {
      return '';
    }
  }

  function renderList() {
    const query = (searchInput?.value || '').trim().toLowerCase();
    const modality = modalitySelect?.value || '';
    const selectedPatient = patientSelect?.value || '';
    let fromDate = dateFromInput?.value || '';
    let toDate = dateToInput?.value || '';

    // Enforce From <= To rule
    if (fromDate && toDate && fromDate > toDate) {
      // Swap or adjust if user set inverted dates
      dateToInput.value = fromDate;
      toDate = fromDate;
    }

    const filtered = rows.filter((r) => {
      // Modality filter
      if (modality && r.prediction_type !== modality) return false;

      // Patient filter (doctor only)
      if (isDoctor && selectedPatient) {
        if (selectedPatient === 'unlinked') {
          if (r.patient_id != null) return false;
        } else {
          if (String(r.patient_id) !== String(selectedPatient)) return false;
        }
      }

      // Date Range filters
      if (fromDate || toDate) {
        const rowDate = getISODateOnly(r.created_at);
        if (fromDate && rowDate < fromDate) return false;
        if (toDate && rowDate > toDate) return false;
      }

      // Query search
      if (query) {
        const pName = r.patient_id ? (patientMap.get(r.patient_id) || '') : '';
        const diag = (r.diagnosis || '').toLowerCase();
        const model = (r.model_name || '').toLowerCase();
        const type = (r.prediction_type || '').toLowerCase();
        const idStr = String(r.id);

        if (
          !diag.includes(query) &&
          !model.includes(query) &&
          !type.includes(query) &&
          !idStr.includes(query) &&
          !pName.toLowerCase().includes(query)
        ) {
          return false;
        }
      }

      return true;
    });

    if (countBadge) {
      countBadge.textContent = `Showing ${filtered.length} of ${rows.length} ${rows.length === 1 ? 'analysis' : 'analyses'}`;
    }

    if (filtered.length === 0) {
      listEl.innerHTML = `
        <div class="studio-card" style="text-align: center; padding: 3rem 1.5rem;">
          <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">📜</div>
          <h3 style="font-size: 1.125rem; font-weight: 700; color: var(--slate-800); margin-bottom: 0.25rem;">
            No Activity Records Found
          </h3>
          <p style="font-size: 0.875rem; color: var(--slate-500); max-width: 420px; margin: 0 auto 1.5rem;">
            ${
              query || modality || selectedPatient || fromDate || toDate
                ? 'No analysis runs match the current search criteria, date range, or modality filters.'
                : 'No analyses have been logged yet. Launch Structured ML, Mammography DL, or Experimental Fusion to start logging evaluations.'
            }
          </p>
          <div style="display: flex; gap: 0.75rem; justify-content: center; flex-wrap: wrap;">
            <a href="ml-analysis.html" class="studio-btn studio-btn-primary studio-btn-sm">Run Structured ML</a>
            <a href="dl-analysis.html" class="studio-btn studio-btn-outline studio-btn-sm">Run Mammography DL</a>
            <a href="multimodal.html" class="studio-btn studio-btn-outline studio-btn-sm">Run Experimental Fusion</a>
          </div>
        </div>
      `;
      return;
    }

    listEl.innerHTML = `
      <div>
        ${filtered
          .map((r) =>
            activityCardHtml(
              r,
              reportService.url(r.id),
              r.patient_id ? (patientMap.get(r.patient_id) || `Patient #${r.patient_id}`) : ''
            )
          )
          .join('')}
      </div>
    `;

    // Authenticated View Report delegation
    listEl.querySelectorAll('.btn-view-report').forEach((btn) => {
      btn.addEventListener('click', () => {
        const pid = btn.getAttribute('data-prediction-id');
        if (pid) {
          reportService.open(pid);
        }
      });
    });

    // Authenticated Print Report delegation
    listEl.querySelectorAll('.btn-print-report').forEach((btn) => {
      btn.addEventListener('click', () => {
        const pid = btn.getAttribute('data-prediction-id');
        if (pid) {
          reportService.print(pid);
        }
      });
    });
  }

  function clearFilters() {
    if (searchInput) searchInput.value = '';
    if (modalitySelect) modalitySelect.value = '';
    if (patientSelect) patientSelect.value = '';
    if (dateFromInput) dateFromInput.value = '';
    if (dateToInput) dateToInput.value = '';
    renderList();
  }

  searchInput?.addEventListener('input', renderList);
  modalitySelect?.addEventListener('change', renderList);
  patientSelect?.addEventListener('change', renderList);
  dateFromInput?.addEventListener('change', renderList);
  dateToInput?.addEventListener('change', renderList);
  clearFiltersBtn?.addEventListener('click', clearFilters);

  loadData();
}
