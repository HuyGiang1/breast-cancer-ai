import { requireAuth } from '../core/guards.js';
import { mountShell } from '../components/shell.js';
import { auth } from '../core/auth.js';
import { patientService } from '../services/patient.service.js';
import { predictionService } from '../services/prediction.service.js';
import { toast } from '../components/toast.js';
import {
  patientModalHtml,
  deleteConfirmModalHtml,
  patientCardHtml,
  accessRestrictedHtml,
  bindModalAccessibility,
  esc,
} from '../components/workspace.js';

if (requireAuth('../login.html?v=auth-v3')) {
  mountShell('Doctor Workspace');
  initPatientsPage();
}

async function initPatientsPage() {
  const app = document.querySelector('#app');
  const user = auth.user();

  if (user?.role !== 'doctor') {
    app.innerHTML = `
      <section class="research-main">
        <header class="research-hero">
          <span class="eyebrow">Doctor Workspace</span>
          <h1>Doctor Workspace</h1>
          <p>Multi-patient research workspace and patient-linked analysis registry.</p>
        </header>
        ${accessRestrictedHtml({
          title: 'Doctor Workspace Access Restricted',
          message: 'The Patient Registry and multi-patient management tools are exclusive to Doctor / Clinician Workspace accounts. Personal accounts are designed for independent self-analysis and direct model exploration.',
          returnUrl: 'history.html',
          returnLabel: 'Go to My Activity',
        })}
      </section>
    `;
    return;
  }

  // Doctor view skeleton
  app.innerHTML = `
    <section class="research-main">
      <header class="research-hero">
        <div style="display: flex; align-items: center; justify-content: space-between; gap: 1rem; flex-wrap: wrap;">
          <div>
            <span class="eyebrow">Doctor Workspace · Research Registry</span>
            <h1>Patient Registry</h1>
            <p>Research patient records, multi-modality analysis history, and cohort tracking. <span style="font-size: 0.8125rem; color: var(--slate-500); display: block; margin-top: 0.25rem;">Prototype Doctor Workspace access does not independently verify professional licensure.</span></p>
          </div>
          <button type="button" class="studio-btn studio-btn-primary" id="openAddPatientBtn" style="display: inline-flex; align-items: center; gap: 0.5rem;">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="12" y1="5" x2="12" y2="19"></line>
              <line x1="5" y1="12" x2="19" y2="12"></line>
            </svg>
            <span>Register Patient</span>
          </button>
        </div>
      </header>

      <!-- Workspace Summary Metrics -->
      <div class="workspace-metrics-strip" id="workspaceMetrics">
        <div class="workspace-metric-card">
          <span class="workspace-metric-label">Total Patients</span>
          <span class="workspace-metric-value" id="metricTotalPatients">—</span>
          <span class="workspace-metric-subtext">Active in registry</span>
        </div>
        <div class="workspace-metric-card">
          <span class="workspace-metric-label">Analyses Logged</span>
          <span class="workspace-metric-value" id="metricTotalAnalyses">—</span>
          <span class="workspace-metric-subtext">Across all patients</span>
        </div>
        <div class="workspace-metric-card">
          <span class="workspace-metric-label">Structured ML</span>
          <span class="workspace-metric-value" id="metricMlAnalyses">—</span>
          <span class="workspace-metric-subtext">Wisconsin cytology runs</span>
        </div>
        <div class="workspace-metric-card">
          <span class="workspace-metric-label">Mammography DL</span>
          <span class="workspace-metric-value" id="metricDlAnalyses">—</span>
          <span class="workspace-metric-subtext">Deep learning scans</span>
        </div>
        <div class="workspace-metric-card">
          <span class="workspace-metric-label">Multimodal Fusions</span>
          <span class="workspace-metric-value" id="metricFusionAnalyses">—</span>
          <span class="workspace-metric-subtext">Combined evaluations</span>
        </div>
      </div>

      <!-- Workspace Toolbar -->
      <div class="workspace-toolbar">
        <div class="workspace-toolbar-left">
          <div class="workspace-search-wrap">
            <svg class="workspace-search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="11" cy="11" r="8"></circle>
              <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
            </svg>
            <input type="search" id="patientSearchInput" class="workspace-search-input" placeholder="Search patients by name, ID, or notes...">
          </div>

          <select id="modalityFilterSelect" class="workspace-select" aria-label="Filter by analysis modality">
            <option value="all">All Modalities</option>
            <option value="ml">Has Structured ML</option>
            <option value="dl">Has Mammography DL</option>
            <option value="multimodal">Has Multimodal Fusion</option>
            <option value="any">Has Any Analyses</option>
            <option value="none">No Analyses Yet</option>
          </select>

          <select id="patientSortSelect" class="workspace-select" aria-label="Sort patient registry">
            <option value="updated-desc">Recently Updated</option>
            <option value="name-asc">Name (A → Z)</option>
            <option value="name-desc">Name (Z → A)</option>
            <option value="analyses-desc">Most Analyses</option>
            <option value="created-asc">Oldest Registered</option>
          </select>
        </div>
      </div>

      <!-- Modal Host Container -->
      <div id="modalHost"></div>

      <!-- Patient Grid -->
      <div id="patientList">
        <div class="studio-card" style="text-align: center; padding: 2.5rem; color: var(--slate-500);">
          Loading patient workspace...
        </div>
      </div>
    </section>
  `;

  let patients = [];
  let analyses = [];
  const patientCounts = new Map(); // patient_id -> { ml, dl, multimodal, total }

  const searchInput = document.querySelector('#patientSearchInput');
  const modalitySelect = document.querySelector('#modalityFilterSelect');
  const sortSelect = document.querySelector('#patientSortSelect');
  const openAddBtn = document.querySelector('#openAddPatientBtn');
  const modalHost = document.querySelector('#modalHost');
  const listEl = document.querySelector('#patientList');

  openAddBtn?.addEventListener('click', () => openPatientModal());

  // Close modal on Escape
  window.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeModal();
  });

  async function loadData() {
    try {
      const [patientList, historyList] = await Promise.all([
        patientService.list(),
        predictionService.history().catch(() => []),
      ]);

      patients = Array.isArray(patientList) ? patientList : [];
      analyses = Array.isArray(historyList) ? historyList : [];

      // Compute counts
      patientCounts.clear();
      analyses.forEach((a) => {
        if (!a.patient_id) return;
        const pId = Number(a.patient_id);
        const current = patientCounts.get(pId) || { ml: 0, dl: 0, multimodal: 0, total: 0 };
        const type = a.prediction_type || 'ml';
        if (type === 'ml') current.ml++;
        else if (type === 'dl') current.dl++;
        else if (type === 'multimodal') current.multimodal++;
        current.total++;
        patientCounts.set(pId, current);
      });

      updateMetrics();
      renderList();
    } catch (err) {
      listEl.innerHTML = `
        <div class="studio-card error" style="padding: 1.5rem; color: #b91c1c;">
          <strong>Failed to load patient records:</strong> ${esc(err.message || 'Server error')}
        </div>
      `;
    }
  }

  function updateMetrics() {
    const totalPatientsEl = document.querySelector('#metricTotalPatients');
    const totalAnalysesEl = document.querySelector('#metricTotalAnalyses');
    const mlEl = document.querySelector('#metricMlAnalyses');
    const dlEl = document.querySelector('#metricDlAnalyses');
    const fusionEl = document.querySelector('#metricFusionAnalyses');

    const totalPatients = patients.length;
    let totalLinkedAnalyses = 0;
    let mlTotal = 0;
    let dlTotal = 0;
    let fusionTotal = 0;

    analyses.forEach((a) => {
      if (!a.patient_id) return;
      totalLinkedAnalyses++;
      if (a.prediction_type === 'ml') mlTotal++;
      else if (a.prediction_type === 'dl') dlTotal++;
      else if (a.prediction_type === 'multimodal') fusionTotal++;
    });

    if (totalPatientsEl) totalPatientsEl.textContent = totalPatients;
    if (totalAnalysesEl) totalAnalysesEl.textContent = totalLinkedAnalyses;
    if (mlEl) mlEl.textContent = mlTotal;
    if (dlEl) dlEl.textContent = dlTotal;
    if (fusionEl) fusionEl.textContent = fusionTotal;
  }

  function renderList() {
    const query = (searchInput?.value || '').trim().toLowerCase();
    const modalityFilter = modalitySelect?.value || 'all';
    const sortBy = sortSelect?.value || 'updated-desc';

    let filtered = patients.filter((p) => {
      // Query filter
      if (query) {
        const matchesName = (p.full_name || '').toLowerCase().includes(query);
        const matchesId = String(p.id).includes(query);
        const matchesNotes = (p.notes || '').toLowerCase().includes(query);
        if (!matchesName && !matchesId && !matchesNotes) return false;
      }

      // Modality filter
      const counts = patientCounts.get(p.id) || { ml: 0, dl: 0, multimodal: 0, total: 0 };
      if (modalityFilter === 'ml' && counts.ml === 0) return false;
      if (modalityFilter === 'dl' && counts.dl === 0) return false;
      if (modalityFilter === 'multimodal' && counts.multimodal === 0) return false;
      if (modalityFilter === 'any' && counts.total === 0) return false;
      if (modalityFilter === 'none' && counts.total > 0) return false;

      return true;
    });

    // Sorting
    filtered.sort((a, b) => {
      if (sortBy === 'name-asc') return (a.full_name || '').localeCompare(b.full_name || '');
      if (sortBy === 'name-desc') return (b.full_name || '').localeCompare(a.full_name || '');
      if (sortBy === 'analyses-desc') {
        const countA = (patientCounts.get(a.id)?.total) || 0;
        const countB = (patientCounts.get(b.id)?.total) || 0;
        return countB - countA;
      }
      if (sortBy === 'created-asc') {
        return new Date(a.created_at || 0) - new Date(b.created_at || 0);
      }
      // Default: updated-desc
      return new Date(b.updated_at || b.created_at || 0) - new Date(a.updated_at || a.created_at || 0);
    });

    if (filtered.length === 0) {
      listEl.innerHTML = `
        <div class="studio-card" style="text-align: center; padding: 3rem 1.5rem;">
          <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">📋</div>
          <h3 style="font-size: 1.125rem; font-weight: 700; color: var(--slate-800); margin-bottom: 0.25rem;">
            ${query || modalityFilter !== 'all' ? 'No matching patients found' : 'No patients in registry'}
          </h3>
          <p style="font-size: 0.875rem; color: var(--slate-500); max-width: 400px; margin: 0 auto 1.25rem;">
            ${query || modalityFilter !== 'all'
              ? 'Try adjusting your search query or modality filters to locate patient records.'
              : 'Register your first patient record to track Wisconsin cytology, mammography scans, and multimodal research records.'}
          </p>
          ${!query && modalityFilter === 'all' ? `
            <button type="button" class="studio-btn studio-btn-primary studio-btn-sm" id="emptyAddPatientBtn">
              + Register First Patient
            </button>
          ` : ''}
        </div>
      `;
      document.querySelector('#emptyAddPatientBtn')?.addEventListener('click', () => openPatientModal());
      return;
    }

    listEl.innerHTML = `
      <div class="patient-grid">
        ${filtered.map((p) => patientCardHtml(p, patientCounts.get(p.id) || {})).join('')}
      </div>
    `;

    // Wire action buttons
    listEl.querySelectorAll('[data-edit-patient]').forEach((btn) => {
      btn.addEventListener('click', () => {
        const id = Number(btn.getAttribute('data-edit-patient'));
        const p = patients.find((x) => x.id === id);
        if (p) openPatientModal(p);
      });
    });

    listEl.querySelectorAll('[data-delete-patient]').forEach((btn) => {
      btn.addEventListener('click', () => {
        const id = Number(btn.getAttribute('data-delete-patient'));
        const p = patients.find((x) => x.id === id);
        if (p) openDeleteModal(p);
      });
    });
  }

  let activeModalCleanup = null;

  function closeModal() {
    if (activeModalCleanup) {
      activeModalCleanup();
      activeModalCleanup = null;
    }
    modalHost.innerHTML = '';
  }

  function openPatientModal(patient = null) {
    closeModal();
    modalHost.innerHTML = patientModalHtml(patient);

    const form = document.querySelector('#patientForm');
    const closeBtn = document.querySelector('#closePatientModalBtn');
    const cancelBtn = document.querySelector('#cancelPatientModalBtn');
    const overlay = document.querySelector('#patientModalOverlay');
    const errorEl = document.querySelector('#patientFormError');
    const submitBtn = document.querySelector('#savePatientSubmitBtn');

    activeModalCleanup = bindModalAccessibility(overlay, closeModal);

    closeBtn?.addEventListener('click', closeModal);
    cancelBtn?.addEventListener('click', closeModal);
    overlay?.addEventListener('click', (e) => {
      if (e.target === overlay) closeModal();
    });

    form?.addEventListener('submit', async (e) => {
      e.preventDefault();
      if (errorEl) {
        errorEl.style.display = 'none';
        errorEl.textContent = '';
      }

      const fullName = form.full_name?.value.trim();
      const dateOfBirth = form.date_of_birth?.value || null;
      const gender = form.gender?.value || null;
      const notes = form.notes?.value.trim() || null;
      const id = form.id?.value;

      if (!fullName) {
        if (errorEl) {
          errorEl.textContent = 'Please provide a valid patient full name.';
          errorEl.style.display = 'block';
        }
        form.full_name?.focus();
        return;
      }

      const payload = {
        full_name: fullName,
        date_of_birth: dateOfBirth,
        gender: gender,
        notes: notes,
      };

      submitBtn.disabled = true;
      submitBtn.textContent = 'Saving...';

      try {
        if (id) {
          await patientService.update(id, payload);
          toast('Patient record updated successfully.', 'success');
        } else {
          await patientService.create(payload);
          toast('New patient registered successfully.', 'success');
        }
        closeModal();
        await loadData();
      } catch (err) {
        if (errorEl) {
          errorEl.textContent = err.message || 'Failed to save patient record.';
          errorEl.style.display = 'block';
        }
        submitBtn.disabled = false;
        submitBtn.textContent = id ? 'Save Changes' : 'Create Patient';
      }
    });
  }

  function openDeleteModal(patient) {
    closeModal();
    modalHost.innerHTML = deleteConfirmModalHtml(patient);

    const closeBtn = document.querySelector('#closeDeleteModalBtn');
    const cancelBtn = document.querySelector('#cancelDeleteModalBtn');
    const confirmBtn = document.querySelector('#confirmDeleteModalBtn');
    const overlay = document.querySelector('#deleteModalOverlay');

    activeModalCleanup = bindModalAccessibility(overlay, closeModal);

    closeBtn?.addEventListener('click', closeModal);
    cancelBtn?.addEventListener('click', closeModal);
    overlay?.addEventListener('click', (e) => {
      if (e.target === overlay) closeModal();
    });

    confirmBtn?.addEventListener('click', async () => {
      confirmBtn.disabled = true;
      confirmBtn.textContent = 'Deleting...';
      try {
        await patientService.remove(patient.id);
        toast(`Patient record ${patient.full_name} deleted. Saved analysis records preserved.`, 'info');
        closeModal();
        await loadData();
      } catch (err) {
        toast(err.message || 'Failed to delete patient record.', 'error');
        confirmBtn.disabled = false;
        confirmBtn.textContent = 'Delete Patient Record';
      }
    });
  }

  // Bind input events
  searchInput?.addEventListener('input', renderList);
  modalitySelect?.addEventListener('change', renderList);
  sortSelect?.addEventListener('change', renderList);

  // Initial load
  loadData();
}
