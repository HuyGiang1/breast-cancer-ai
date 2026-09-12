import { requireAuth } from '../core/guards.js';
import { mountShell } from '../components/shell.js';
import { auth } from '../core/auth.js';
import { patientService } from '../services/patient.service.js';
import { reportService } from '../services/report.service.js';
import { toast } from '../components/toast.js';
import {
  patientModalHtml,
  timelineEntryHtml,
  accessRestrictedHtml,
  bindModalAccessibility,
  formatDate,
  calculateAge,
  getInitials,
  esc,
} from '../components/workspace.js';

if (requireAuth('../login.html?v=auth-v3')) {
  mountShell('Patient Detail');
  initPatientDetailPage();
}

async function initPatientDetailPage() {
  const app = document.querySelector('#app');
  const user = auth.user();

  if (user?.role !== 'doctor') {
    app.innerHTML = `
      <section class="research-main">
        <header class="research-hero">
          <span class="eyebrow">Doctor Workspace</span>
          <h1>Patient Record</h1>
          <p>Research patient longitudinal analysis timelines and multi-modality evaluation history.</p>
        </header>
        ${accessRestrictedHtml({
          title: 'Patient Record Access Restricted',
          message: 'Individual patient detail records and analysis timelines are accessible only to authenticated Doctor / Clinician Workspace accounts.',
          returnUrl: 'history.html',
          returnLabel: 'Go to My Activity',
        })}
      </section>
    `;
    return;
  }

  const searchParams = new URLSearchParams(location.search);
  const patientId = searchParams.get('id');

  if (!patientId || !/^\d+$/.test(patientId)) {
    renderNotFound('Invalid or missing patient identifier.');
    return;
  }

  app.innerHTML = `
    <section class="research-main">
      <div id="modalHost"></div>
      <div id="patientDetailContent">
        <div class="studio-card" style="text-align: center; padding: 3rem; color: var(--slate-500);">
          Loading patient clinical record...
        </div>
      </div>
    </section>
  `;

  const modalHost = document.querySelector('#modalHost');
  const contentEl = document.querySelector('#patientDetailContent');

  let currentPatient = null;
  let historyList = [];

  // Close modal on Escape
  window.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeModal();
  });

  async function loadPatient() {
    try {
      const [patient, history] = await Promise.all([
        patientService.get(patientId),
        patientService.history(patientId).catch(() => []),
      ]);

      currentPatient = patient;
      historyList = Array.isArray(history) ? history : [];
      renderPatientView();
    } catch (err) {
      if (err.status === 404) {
        renderNotFound('The requested patient record was not found in your clinical registry.');
      } else {
        renderNotFound(err.message || 'Failed to retrieve patient record.');
      }
    }
  }

  function renderNotFound(message) {
    app.innerHTML = `
      <section class="research-main">
        <div class="studio-card" style="text-align: center; padding: 3rem 1.5rem; max-width: 520px; margin: 3rem auto;">
          <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">🔍</div>
          <h2 style="font-size: 1.25rem; font-weight: 700; color: var(--slate-900); margin-bottom: 0.5rem;">Patient Not Found</h2>
          <p style="font-size: 0.875rem; color: var(--slate-600); margin-bottom: 1.5rem;">${esc(message)}</p>
          <a href="patients.html" class="studio-btn studio-btn-primary">Return to Patient Registry</a>
        </div>
      </section>
    `;
  }

  function renderPatientView() {
    const p = currentPatient;
    const age = calculateAge(p.date_of_birth);
    const initials = getInitials(p.full_name);

    let mlCount = 0;
    let dlCount = 0;
    let fusionCount = 0;

    historyList.forEach((r) => {
      const type = r.prediction_type || 'ml';
      if (type === 'ml') mlCount++;
      else if (type === 'dl') dlCount++;
      else if (type === 'multimodal') fusionCount++;
    });

    const totalAnalyses = historyList.length;

    contentEl.innerHTML = `
      <!-- Breadcrumb Navigation -->
      <nav class="patient-breadcrumb" aria-label="Breadcrumb">
        <a href="patients.html">← Patient Registry</a>
        <span>/</span>
        <span style="color: var(--slate-800); font-weight: 600;">${esc(p.full_name)}</span>
      </nav>

      <!-- Patient Header Banner -->
      <header class="patient-detail-header">
        <div class="patient-detail-profile-row">
          <div class="patient-detail-main-info">
            <div class="patient-detail-avatar">${esc(initials)}</div>
            <div class="patient-detail-title-group">
              <h1>${esc(p.full_name)}</h1>
              <div class="patient-detail-demographics">
                <span class="patient-id-badge">ID: ${esc(p.id)}</span>
                ${age != null ? `<span>${age} years old</span> · ` : ''}
                <span>${esc(p.gender || 'Unspecified Gender')}</span>
                ${p.date_of_birth ? `<span>· DOB: ${formatDate(p.date_of_birth)}</span>` : ''}
                <span>· Registered: ${formatDate(p.created_at)}</span>
              </div>
            </div>
          </div>

          <div>
            <button type="button" class="studio-btn studio-btn-outline studio-btn-sm" id="editDemographicsBtn" style="display: inline-flex; align-items: center; gap: 0.375rem;">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
              </svg>
              <span>Edit Demographic Info</span>
            </button>
          </div>
        </div>

        <!-- 3-Modality Quick Launch Strip -->
        <div class="patient-launch-strip">
          <span style="font-size: 0.8125rem; font-weight: 700; color: var(--slate-700); align-self: center; margin-right: 0.5rem;">
            New Analysis for this Patient:
          </span>
          <a href="ml-analysis.html?patient_id=${esc(p.id)}" class="patient-launch-btn ml" title="Perform Wisconsin Cytology Structured ML Analysis">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
              <line x1="3" y1="9" x2="21" y2="9"></line>
              <line x1="9" y1="21" x2="9" y2="9"></line>
            </svg>
            <span>Run Wisconsin Structured ML</span>
          </a>
          <a href="dl-analysis.html?patient_id=${esc(p.id)}" class="patient-launch-btn dl" title="Perform CBIS-DDSM Mammography Deep Learning Analysis">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
              <circle cx="8.5" cy="8.5" r="1.5"></circle>
              <polyline points="21 15 16 10 5 21"></polyline>
            </svg>
            <span>Run Mammography DL</span>
          </a>
          <a href="multimodal.html?patient_id=${esc(p.id)}" class="patient-launch-btn fusion" title="Perform Experimental Multimodal Fusion Analysis">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polygon points="12 2 2 7 12 12 22 7 12 2"></polygon>
              <polyline points="2 17 12 22 22 17"></polyline>
              <polyline points="2 12 12 17 22 12"></polyline>
            </svg>
            <span>Run Multimodal Fusion</span>
          </a>
        </div>
      </header>

      <!-- Main Layout: Timeline & Notes Sidebar -->
      <div class="patient-detail-grid">
        <!-- Left: Chronological Analysis Timeline -->
        <section>
          <div class="timeline-section-title">
            <span>Diagnostic &amp; Research Timeline (${totalAnalyses})</span>
            <a href="history.html?patient_id=${esc(p.id)}" class="studio-btn studio-btn-outline studio-btn-sm">
              Full Activity History →
            </a>
          </div>

          ${
            historyList.length === 0
              ? `
              <div class="studio-card" style="text-align: center; padding: 2.5rem 1.5rem;">
                <div style="font-size: 2rem; margin-bottom: 0.5rem;">🔬</div>
                <h3 style="font-size: 1.0625rem; font-weight: 700; color: var(--slate-800); margin-bottom: 0.375rem;">
                  No Analyses Recorded
                </h3>
                <p style="font-size: 0.8125rem; color: var(--slate-500); max-width: 380px; margin: 0 auto 1rem;">
                  No prediction records have been logged for this patient yet. Use the quick launch buttons above to run Wisconsin ML, Mammography DL, or Multimodal Fusion.
                </p>
              </div>
            `
              : `
              <div class="timeline-feed">
                ${historyList.map((r) => timelineEntryHtml(r, reportService.url(r.id))).join('')}
              </div>
            `
          }
        </section>

        <!-- Right: Research Notes & Cohort Summary -->
        <aside>
          <div class="studio-card" style="margin-bottom: 1rem;">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.75rem;">
              <h3 style="font-size: 1rem; font-weight: 700; color: var(--slate-900); margin: 0;">Research Notes</h3>
              <button type="button" class="btn-icon-action" id="editNotesBtn" title="Edit Research Notes">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                  <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                </svg>
              </button>
            </div>
            <p style="font-size: 0.875rem; color: var(--slate-600); line-height: 1.5; white-space: pre-wrap; margin: 0;">
              ${esc(p.notes || 'No research notes recorded for this patient.')}
            </p>
          </div>

          <div class="studio-card">
            <h3 style="font-size: 1rem; font-weight: 700; color: var(--slate-900); margin-bottom: 0.75rem;">
              Modality Summary
            </h3>
            <div style="display: flex; flex-direction: column; gap: 0.5rem; font-size: 0.8125rem;">
              <div style="display: flex; justify-content: space-between; padding-bottom: 0.375rem; border-bottom: 1px solid var(--border-subtle);">
                <span style="color: var(--slate-600);">Structured ML Runs:</span>
                <strong style="color: var(--teal-800);">${mlCount}</strong>
              </div>
              <div style="display: flex; justify-content: space-between; padding-bottom: 0.375rem; border-bottom: 1px solid var(--border-subtle);">
                <span style="color: var(--slate-600);">Mammography Scans:</span>
                <strong style="color: #1d4ed8;">${dlCount}</strong>
              </div>
              <div style="display: flex; justify-content: space-between; padding-bottom: 0.375rem; border-bottom: 1px solid var(--border-subtle);">
                <span style="color: var(--slate-600);">Multimodal Fusions:</span>
                <strong style="color: #7e22ce;">${fusionCount}</strong>
              </div>
              <div style="display: flex; justify-content: space-between; padding-top: 0.25rem;">
                <span style="color: var(--slate-800); font-weight: 700;">Total Analyses:</span>
                <strong style="color: var(--slate-900);">${totalAnalyses}</strong>
              </div>
            </div>
          </div>
        </aside>
      </div>
    `;

    document.querySelector('#editDemographicsBtn')?.addEventListener('click', openEditModal);
    document.querySelector('#editNotesBtn')?.addEventListener('click', openEditModal);

    // Authenticated View report delegation
    contentEl.querySelectorAll('.btn-view-report').forEach((btn) => {
      btn.addEventListener('click', () => {
        const pid = btn.getAttribute('data-prediction-id');
        if (pid) reportService.open(pid);
      });
    });

    // Authenticated Print report delegation
    contentEl.querySelectorAll('.btn-print-report').forEach((btn) => {
      btn.addEventListener('click', () => {
        const pid = btn.getAttribute('data-prediction-id');
        if (pid) reportService.print(pid);
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

  function openEditModal() {
    closeModal();
    modalHost.innerHTML = patientModalHtml(currentPatient);

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
        await patientService.update(currentPatient.id, payload);
        toast('Patient record updated successfully.', 'success');
        closeModal();
        await loadPatient();
      } catch (err) {
        if (errorEl) {
          errorEl.textContent = err.message || 'Failed to update patient record.';
          errorEl.style.display = 'block';
        }
        submitBtn.disabled = false;
        submitBtn.textContent = 'Save Changes';
      }
    });
  }

  // Initial load
  loadPatient();
}
