import { requireAuth } from '../core/guards.js';
import { mountShell } from '../components/shell.js';
import { auth } from '../core/auth.js';
import { predictionService } from '../services/prediction.service.js';
import { patientService } from '../services/patient.service.js';
import { reportService } from '../services/report.service.js';
import { activityCardHtml, esc } from '../components/workspace.js';

if (requireAuth('../login.html?v=auth-v3')) {
  mountShell('Activity');
  initHistoryPage();
}

async function initHistoryPage() {
  const app = document.querySelector('#app');
  const user = auth.user();
  const isDoctor = user?.role === 'doctor';

  const searchParams = new URLSearchParams(location.search);
  const initialPatientId = searchParams.get('patient_id') || '';

  app.innerHTML = `
    <section class="research-main">
      <header class="research-hero">
        <span class="eyebrow">${isDoctor ? 'Clinician Records' : 'Personal Records'}</span>
        <h1>${isDoctor ? 'Analysis Activity' : 'My Activity'}</h1>
        <p>${
          isDoctor
            ? 'Review and filter diagnostic evaluations across your clinical patient registry and standalone analyses.'
            : 'Review your personal self-assessment logs, model confidence scores, and dual-engine research telemetry.'
        }</p>
      </header>

      <!-- Toolbar -->
      <div class="workspace-toolbar">
        <div class="workspace-toolbar-left">
          <div class="workspace-search-wrap">
            <svg class="workspace-search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="11" cy="11" r="8"></circle>
              <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
            </svg>
            <input type="search" id="historySearchInput" class="workspace-search-input" placeholder="Search by model, diagnosis, or keyword...">
          </div>

          <select id="historyModalitySelect" class="workspace-select" aria-label="Filter by analysis modality">
            <option value="">All Modalities</option>
            <option value="ml">Wisconsin Structured ML</option>
            <option value="dl">Mammography Deep Learning</option>
            <option value="multimodal">Multimodal Fusion</option>
          </select>

          ${
            isDoctor
              ? `
            <select id="historyPatientSelect" class="workspace-select" aria-label="Filter by patient">
              <option value="">All Patients &amp; Standalone</option>
              <option value="unlinked">Standalone Analyses Only</option>
            </select>
          `
              : ''
          }
        </div>
      </div>

      <!-- Activity Feed List -->
      <div id="activityList">
        <div class="studio-card" style="text-align: center; padding: 2.5rem; color: var(--slate-500);">
          Loading activity records...
        </div>
      </div>
    </section>
  `;

  const listEl = document.querySelector('#activityList');
  const searchInput = document.querySelector('#historySearchInput');
  const modalitySelect = document.querySelector('#historyModalitySelect');
  const patientSelect = document.querySelector('#historyPatientSelect');

  let rows = [];
  let patientMap = new Map(); // id -> name

  async function loadData() {
    try {
      const promises = [predictionService.history(initialPatientId || undefined)];
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
    }
  }

  function renderList() {
    const query = (searchInput?.value || '').trim().toLowerCase();
    const modality = modalitySelect?.value || '';
    const selectedPatient = patientSelect?.value || '';

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

    if (filtered.length === 0) {
      listEl.innerHTML = `
        <div class="studio-card" style="text-align: center; padding: 3rem 1.5rem;">
          <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">📜</div>
          <h3 style="font-size: 1.125rem; font-weight: 700; color: var(--slate-800); margin-bottom: 0.25rem;">
            No Activity Records Found
          </h3>
          <p style="font-size: 0.875rem; color: var(--slate-500); max-width: 400px; margin: 0 auto 1.5rem;">
            ${
              query || modality || selectedPatient
                ? 'No analysis runs match the current search criteria or modality filters.'
                : 'No analyses have been logged yet. Launch Wisconsin ML, Mammography DL, or Multimodal Fusion to start logging evaluations.'
            }
          </p>
          <div style="display: flex; gap: 0.75rem; justify-content: center; flex-wrap: wrap;">
            <a href="ml-analysis.html" class="studio-btn studio-btn-primary studio-btn-sm">Run Wisconsin ML</a>
            <a href="dl-analysis.html" class="studio-btn studio-btn-outline studio-btn-sm">Run Mammography DL</a>
            <a href="multimodal.html" class="studio-btn studio-btn-outline studio-btn-sm">Run Multimodal Fusion</a>
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

    // Print report delegation
    listEl.querySelectorAll('.btn-print-report').forEach((btn) => {
      btn.addEventListener('click', () => {
        const url = btn.getAttribute('data-report-url');
        if (url) {
          const printWin = window.open(url, '_blank');
          if (printWin) {
            printWin.onload = () => {
              try {
                printWin.print();
              } catch (e) {}
            };
          }
        }
      });
    });
  }

  searchInput?.addEventListener('input', renderList);
  modalitySelect?.addEventListener('change', renderList);
  patientSelect?.addEventListener('change', renderList);

  loadData();
}
