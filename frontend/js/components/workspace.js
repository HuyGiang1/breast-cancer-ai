/* Breast Health Intelligence Studio — V4 Workspace UI Components */

export const esc = (v) =>
  String(v ?? '').replace(/[&<>"']/g, (c) => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;',
  }[c]));

export function formatDate(dateStr) {
  if (!dateStr) return '—';
  try {
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return String(dateStr);
    return d.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  } catch (e) {
    return String(dateStr);
  }
}

export function formatDateTime(dateStr) {
  if (!dateStr) return '—';
  try {
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return String(dateStr);
    return d.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch (e) {
    return String(dateStr);
  }
}

export function calculateAge(dobStr) {
  if (!dobStr) return null;
  const dob = new Date(dobStr);
  if (isNaN(dob.getTime())) return null;
  const diffMs = Date.now() - dob.getTime();
  const ageDate = new Date(diffMs);
  return Math.abs(ageDate.getUTCFullYear() - 1970);
}

export function getInitials(name) {
  if (!name) return 'PT';
  const parts = name.trim().split(/\s+/);
  if (parts.length === 1) return parts[0].substring(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

/**
 * Add / Edit Patient Modal Dialog
 */
export function patientModalHtml(p = {}) {
  const isEdit = Boolean(p && p.id);
  return `
    <div class="workspace-modal-overlay" id="patientModalOverlay" role="dialog" aria-modal="true" aria-labelledby="patientModalTitle">
      <div class="workspace-modal">
        <div class="workspace-modal-header">
          <h2 class="workspace-modal-title" id="patientModalTitle">${isEdit ? 'Edit Patient Record' : 'Register New Patient'}</h2>
          <button type="button" class="workspace-modal-close" id="closePatientModalBtn" aria-label="Close dialog">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>
        <form id="patientForm" novalidate>
          <div class="workspace-modal-body">
            <input type="hidden" name="id" value="${esc(p.id || '')}">

            <div class="form-group" style="margin-bottom: 1rem;">
              <label class="form-label" for="patFullName">Full Name *</label>
              <input type="text" id="patFullName" name="full_name" class="form-input" value="${esc(p.full_name || '')}" placeholder="e.g. Jane M. Doe" required autocomplete="off">
            </div>

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1rem;">
              <div class="form-group">
                <label class="form-label" for="patDob">Date of Birth</label>
                <input type="date" id="patDob" name="date_of_birth" class="form-input" value="${esc(p.date_of_birth || '')}">
              </div>
              <div class="form-group">
                <label class="form-label" for="patGender">Gender</label>
                <select id="patGender" name="gender" class="workspace-select" style="width: 100%;">
                  <option value="" ${!p.gender ? 'selected' : ''}>Select gender...</option>
                  <option value="Female" ${p.gender === 'Female' ? 'selected' : ''}>Female</option>
                  <option value="Male" ${p.gender === 'Male' ? 'selected' : ''}>Male</option>
                  <option value="Other" ${p.gender === 'Other' ? 'selected' : ''}>Other</option>
                  <option value="Unspecified" ${p.gender === 'Unspecified' ? 'selected' : ''}>Unspecified</option>
                </select>
              </div>
            </div>

            <div class="form-group">
              <label class="form-label" for="patNotes">Clinical &amp; Research Notes</label>
              <textarea id="patNotes" name="notes" class="form-input" rows="3" placeholder="Enter relevant baseline cytology history, mammographic findings, or research trial identifiers...">${esc(p.notes || '')}</textarea>
            </div>

            <div id="patientFormError" class="auth-alert-box error" style="display: none; margin-top: 1rem;" role="alert"></div>
          </div>
          <div class="workspace-modal-footer">
            <button type="button" class="studio-btn studio-btn-outline" id="cancelPatientModalBtn">Cancel</button>
            <button type="submit" class="studio-btn studio-btn-primary" id="savePatientSubmitBtn">
              ${isEdit ? 'Save Changes' : 'Create Patient'}
            </button>
          </div>
        </form>
      </div>
    </div>
  `;
}

/**
 * Safety-explicit Delete Confirmation Modal Dialog
 */
export function deleteConfirmModalHtml(patient) {
  return `
    <div class="workspace-modal-overlay" id="deleteModalOverlay" role="dialog" aria-modal="true" aria-labelledby="deleteModalTitle">
      <div class="workspace-modal">
        <div class="workspace-modal-header" style="border-bottom-color: #fee2e2;">
          <h2 class="workspace-modal-title" id="deleteModalTitle" style="color: #b91c1c;">Confirm Patient Deletion</h2>
          <button type="button" class="workspace-modal-close" id="closeDeleteModalBtn" aria-label="Close dialog">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>
        <div class="workspace-modal-body">
          <div class="delete-patient-name-confirm">
            Are you sure you want to delete patient <strong>${esc(patient.full_name)}</strong> (ID: <code>${esc(patient.id)}</code>)?
          </div>

          <div class="delete-safety-warning">
            <div class="delete-safety-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
                <line x1="12" y1="9" x2="12" y2="13"></line>
                <line x1="12" y1="17" x2="12.01" y2="17"></line>
              </svg>
            </div>
            <div class="delete-safety-text">
              <strong>Patient Demographic Unlinking</strong>
              Deleting this patient record removes the demographic registry entry. All historical prediction records, model telemetry runs, and generated reports are <strong>preserved in system logs</strong>, but will no longer be associated with this patient.
            </div>
          </div>
        </div>
        <div class="workspace-modal-footer">
          <button type="button" class="studio-btn studio-btn-outline" id="cancelDeleteModalBtn">Cancel</button>
          <button type="button" class="studio-btn studio-btn-danger" id="confirmDeleteModalBtn" style="background:#dc2626;color:#ffffff;border:none;padding:0.625rem 1.125rem;border-radius:8px;font-weight:600;cursor:pointer;">Delete Patient Record</button>
        </div>
      </div>
    </div>
  `;
}

/**
 * Patient Card Component
 */
export function patientCardHtml(p, counts = {}) {
  const age = calculateAge(p.date_of_birth);
  const initials = getInitials(p.full_name);
  const mlCount = counts.ml || 0;
  const dlCount = counts.dl || 0;
  const fusionCount = counts.multimodal || 0;
  const totalAnalyses = mlCount + dlCount + fusionCount;

  return `
    <article class="patient-card" data-patient-id="${esc(p.id)}">
      <div>
        <div class="patient-card-header">
          <div class="patient-avatar" aria-hidden="true">${esc(initials)}</div>
          <div class="patient-info">
            <a href="patient-detail.html?id=${esc(p.id)}" class="patient-name-link">${esc(p.full_name)}</a>
            <div class="patient-meta-line">
              <span class="patient-id-badge">ID: ${esc(p.id)}</span>
              ${age != null ? `<span>${age} yrs</span> · ` : ''}
              <span>${esc(p.gender || 'Unspecified')}</span>
              ${p.date_of_birth ? `<span>· DOB: ${formatDate(p.date_of_birth)}</span>` : ''}
            </div>
          </div>
        </div>

        ${p.notes ? `<div class="patient-notes-snippet" title="${esc(p.notes)}">${esc(p.notes)}</div>` : ''}

        <div class="patient-metrics-badges">
          <span class="patient-modality-pill ${totalAnalyses > 0 ? 'has-analyses' : ''}">
            ${totalAnalyses} ${totalAnalyses === 1 ? 'Analysis' : 'Analyses'}
          </span>
          ${mlCount > 0 ? `<span class="patient-modality-pill has-analyses">${mlCount} ML</span>` : ''}
          ${dlCount > 0 ? `<span class="patient-modality-pill has-analyses">${dlCount} DL</span>` : ''}
          ${fusionCount > 0 ? `<span class="patient-modality-pill has-analyses">${fusionCount} Fusion</span>` : ''}
        </div>
      </div>

      <div class="patient-card-actions">
        <div class="patient-quick-launches">
          <a href="ml-analysis.html?patient_id=${esc(p.id)}" class="btn-launch-modality btn-launch-ml" title="Run Wisconsin Structured ML Analysis">
            <span>ML</span>
          </a>
          <a href="dl-analysis.html?patient_id=${esc(p.id)}" class="btn-launch-modality btn-launch-dl" title="Run Mammography Deep Learning Analysis">
            <span>DL</span>
          </a>
          <a href="multimodal.html?patient_id=${esc(p.id)}" class="btn-launch-modality btn-launch-fusion" title="Run Experimental Multimodal Fusion Analysis">
            <span>Fusion</span>
          </a>
        </div>

        <div class="patient-manage-actions">
          <a href="patient-detail.html?id=${esc(p.id)}" class="btn-icon-action" title="View Patient Details &amp; History">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
              <circle cx="12" cy="12" r="3"></circle>
            </svg>
          </a>
          <button type="button" class="btn-icon-action" data-edit-patient="${esc(p.id)}" title="Edit Patient Record">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
              <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
            </svg>
          </button>
          <button type="button" class="btn-icon-action delete" data-delete-patient="${esc(p.id)}" title="Delete Patient Record">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="3 6 5 6 21 6"></polyline>
              <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
            </svg>
          </button>
        </div>
      </div>
    </article>
  `;
}

/**
 * Timeline Entry Component for Patient Detail
 */
export function timelineEntryHtml(r, reportUrl = '') {
  const isMalignant = (r.diagnosis || '').toLowerCase().includes('malignant');
  const modality = r.prediction_type || 'ml';
  const typeLabel = modality === 'multimodal' ? 'Fusion' : modality.toUpperCase();
  const rawProb = r.raw_probability != null ? (Number(r.raw_probability) * 100).toFixed(1) + '%' : null;

  return `
    <div class="timeline-entry">
      <div class="timeline-node">
        <div class="timeline-node-icon ${isMalignant ? 'malignant' : 'benign'}">
          ${isMalignant ? 'M' : 'B'}
        </div>
      </div>
      <article class="timeline-card">
        <div class="timeline-header">
          <div style="display: flex; align-items: center; gap: 0.5rem;">
            <span class="timeline-type-badge ${esc(modality)}">${esc(typeLabel)}</span>
            <span class="patient-id-badge">#${esc(r.id)}</span>
          </div>
          <time class="timeline-date">${formatDateTime(r.created_at)}</time>
        </div>

        <div class="timeline-result-row">
          <div class="timeline-diagnosis ${isMalignant ? 'malignant' : 'benign'}">
            <span>${esc(r.diagnosis || 'Unspecified Result')}</span>
          </div>
          ${rawProb ? `
            <div style="display: flex; align-items: center; gap: 0.5rem;">
              <small style="color: var(--slate-500); font-weight: 600;">${esc(rawProb)}</small>
              <div class="timeline-probability-bar-wrap">
                <div class="timeline-probability-bar ${isMalignant ? 'malignant' : ''}" style="width: ${esc(rawProb)}"></div>
              </div>
            </div>
          ` : ''}
        </div>

        <div class="timeline-meta-grid">
          <div><strong>Model:</strong> ${esc(r.model_name || 'Standard Production')}</div>
          ${r.notes ? `<div style="margin-top: 0.25rem;"><strong>Notes:</strong> ${esc(r.notes)}</div>` : ''}
        </div>

        <div class="timeline-actions">
          ${reportUrl ? `
            <a href="${reportUrl}" target="_blank" rel="noopener" class="studio-btn studio-btn-outline studio-btn-sm" style="display: inline-flex; align-items: center; gap: 0.375rem;">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                <polyline points="14 2 14 8 20 8"></polyline>
              </svg>
              <span>View Report</span>
            </a>
            <button type="button" class="studio-btn studio-btn-outline studio-btn-sm btn-print-report" data-report-url="${reportUrl}" style="display: inline-flex; align-items: center; gap: 0.375rem;">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="6 9 6 2 18 2 18 9"></polyline>
                <path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"></path>
                <rect x="6" y="14" width="12" height="8"></rect>
              </svg>
              <span>Print</span>
            </button>
          ` : ''}
        </div>
      </article>
    </div>
  `;
}

/**
 * Rich Activity Card for History Page
 */
export function activityCardHtml(r, reportUrl = '', patientName = '') {
  const isMalignant = (r.diagnosis || '').toLowerCase().includes('malignant');
  const modality = r.prediction_type || 'ml';
  const typeLabel = modality === 'multimodal' ? 'Fusion' : modality.toUpperCase();
  const rawProb = r.raw_probability != null ? (Number(r.raw_probability) * 100).toFixed(1) + '%' : null;

  return `
    <article class="activity-card" data-prediction-id="${esc(r.id)}">
      <div class="activity-main-info">
        <div class="activity-icon-badge ${esc(modality)}">
          ${esc(typeLabel)}
        </div>
        <div class="activity-text-group">
          <div class="activity-title-row">
            <span class="activity-diagnosis ${isMalignant ? 'malignant' : 'benign'}">
              ${esc(r.diagnosis || 'Result Available')}
            </span>
            <span class="patient-id-badge">#${esc(r.id)}</span>
            ${patientName ? `<span style="font-size:0.8125rem; font-weight:600; color:var(--teal-800);">Patient: ${esc(patientName)}</span>` : ''}
          </div>
          <div class="activity-subline">
            <span>${esc(r.model_name || 'Standard Model')}</span>
            ${rawProb ? ` · <span>Probability: ${esc(rawProb)}</span>` : ''}
            <span> · ${formatDateTime(r.created_at)}</span>
          </div>
        </div>
      </div>

      <div class="activity-actions">
        ${reportUrl ? `
          <a href="${reportUrl}" target="_blank" rel="noopener" class="studio-btn studio-btn-outline studio-btn-sm" style="display: inline-flex; align-items: center; gap: 0.375rem;">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
              <polyline points="14 2 14 8 20 8"></polyline>
            </svg>
            <span>View Report</span>
          </a>
          <button type="button" class="studio-btn studio-btn-outline studio-btn-sm btn-print-report" data-report-url="${reportUrl}" style="display: inline-flex; align-items: center; gap: 0.375rem;">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="6 9 6 2 18 2 18 9"></polyline>
              <path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"></path>
              <rect x="6" y="14" width="12" height="8"></rect>
            </svg>
            <span>Print</span>
          </button>
        ` : ''}
      </div>
    </article>
  `;
}

/**
 * Report Card for Reports Page
 */
export function reportCardHtml(r, reportUrl = '', patientName = '') {
  const isMalignant = (r.diagnosis || '').toLowerCase().includes('malignant');
  const modality = r.prediction_type || 'ml';
  const typeLabel = modality === 'multimodal' ? 'Multimodal Fusion' : (modality === 'dl' ? 'Mammography DL' : 'Wisconsin ML');
  const rawProb = r.raw_probability != null ? (Number(r.raw_probability) * 100).toFixed(1) + '%' : 'N/A';

  return `
    <article class="report-card" data-report-id="${esc(r.id)}">
      <div class="activity-main-info">
        <div class="activity-icon-badge ${esc(modality)}">
          ${modality === 'multimodal' ? 'FUS' : modality.toUpperCase()}
        </div>
        <div class="activity-text-group">
          <div class="activity-title-row">
            <strong style="font-size: 1rem; color: var(--slate-900);">Report #${esc(r.id)} — ${esc(typeLabel)}</strong>
            <span class="activity-diagnosis ${isMalignant ? 'malignant' : 'benign'}">
              ${esc(r.diagnosis || 'Result Logged')}
            </span>
          </div>
          <div class="activity-subline">
            ${patientName ? `<span><strong>Patient:</strong> ${esc(patientName)}</span> · ` : ''}
            <span><strong>Model:</strong> ${esc(r.model_name || 'Standard Model')}</span> ·
            <span><strong>Probability:</strong> ${esc(rawProb)}</span> ·
            <span>${formatDateTime(r.created_at)}</span>
          </div>
        </div>
      </div>

      <div class="activity-actions">
        ${reportUrl ? `
          <a href="${reportUrl}" target="_blank" rel="noopener" class="studio-btn studio-btn-primary studio-btn-sm" style="display: inline-flex; align-items: center; gap: 0.375rem;">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
              <circle cx="12" cy="12" r="3"></circle>
            </svg>
            <span>View Full Report</span>
          </a>
          <button type="button" class="studio-btn studio-btn-outline studio-btn-sm btn-print-report" data-report-url="${reportUrl}" style="display: inline-flex; align-items: center; gap: 0.375rem;">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="6 9 6 2 18 2 18 9"></polyline>
              <path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"></path>
              <rect x="6" y="14" width="12" height="8"></rect>
            </svg>
            <span>Print / Save PDF</span>
          </button>
        ` : ''}
      </div>
    </article>
  `;
}

/**
 * Access Restricted Notice for Personal Accounts
 */
export function accessRestrictedHtml({
  title = 'Doctor Workspace Access Restricted',
  message = 'The Patient Registry and multi-patient management tools are exclusive to Doctor and Clinician accounts. Personal accounts are designed for independent self-analysis and direct model exploration.',
  returnUrl = 'history.html',
  returnLabel = 'Go to My Activity',
} = {}) {
  return `
    <div class="access-restricted-card">
      <div class="access-restricted-icon">
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
          <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
        </svg>
      </div>
      <h2 class="access-restricted-title">${esc(title)}</h2>
      <p class="access-restricted-desc">${esc(message)}</p>
      <div style="display: flex; gap: 0.75rem; justify-content: center; flex-wrap: wrap;">
        <a href="${esc(returnUrl)}" class="studio-btn studio-btn-primary">${esc(returnLabel)}</a>
        <a href="dashboard.html" class="studio-btn studio-btn-outline">Return to Overview</a>
      </div>
    </div>
  `;
}

// Backward compatibility legacy export for tests
export const patientForm = (p = {}) => patientModalHtml(p);
export const predictionRow = (r, reportUrl) => activityCardHtml(r, reportUrl);
