function esc(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

export function openGoogleRoleModal({ credential, user = {}, onSelect, onCancel }) {
  let modalHost = document.getElementById('googleRoleModalHost');
  if (!modalHost) {
    modalHost = document.createElement('div');
    modalHost.id = 'googleRoleModalHost';
    document.body.appendChild(modalHost);
  }

  const email = user.email || '';
  const fullName = user.full_name || 'Google User';

  modalHost.innerHTML = `
    <div class="auth-modal-overlay" id="googleRoleModalOverlay" role="dialog" aria-modal="true" aria-labelledby="googleRoleModalTitle">
      <div class="auth-modal">
        <div class="auth-modal-header">
          <div>
            <h2 class="auth-modal-title" id="googleRoleModalTitle">Choose how you want to use Breast Health Studio</h2>
            <div class="auth-modal-subtitle">
              Welcome, <strong>${esc(fullName)}</strong>${email ? ` (<code>${esc(email)}</code>)` : ''}
            </div>
          </div>
          <button type="button" class="auth-modal-close" id="closeRoleModalBtn" aria-label="Cancel registration">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>

        <div class="auth-modal-body">
          <button type="button" class="auth-modal-role-card" id="selectUserRoleBtn">
            <span class="account-type-badge">Individual Assessment</span>
            <strong class="account-type-title">Regular User</strong>
            <p class="account-type-desc">
              For personal health assessments, running dual-engine ML/DL evaluations, and saving personal reports.
            </p>
          </button>

          <button type="button" class="auth-modal-role-card doctor" id="selectDoctorRoleBtn">
            <span class="account-type-badge doctor">Clinician Workspace</span>
            <strong class="account-type-title">Doctor / Healthcare Professional</strong>
            <p class="account-type-desc">
              For practitioner workflows, patient registry management, multi-patient timelines, and clinical research records.
            </p>
          </button>

          <div class="auth-modal-disclaimer">
            <strong>Research &amp; Educational Notice:</strong><br>
            Doctor role is self-declared for research and demonstration purposes. Professional credentials are not verified.
          </div>

          <p style="font-size: 0.75rem; color: #64748b; margin: 0; line-height: 1.35; text-align: center;">
            Role selection is permanent from your account's perspective. It cannot be changed after account creation.
          </p>
        </div>

        <div class="auth-modal-footer">
          <button type="button" class="studio-btn studio-btn-outline" id="cancelRoleModalBtn" style="padding: 0.5rem 1rem; font-size: 0.8125rem; border-radius: 6px; border: 1px solid #cbd5e1; background: #fff; cursor: pointer;">
            Cancel
          </button>
        </div>
      </div>
    </div>
  `;

  const overlay = document.getElementById('googleRoleModalOverlay');
  const closeBtn = document.getElementById('closeRoleModalBtn');
  const cancelBtn = document.getElementById('cancelRoleModalBtn');
  const userBtn = document.getElementById('selectUserRoleBtn');
  const doctorBtn = document.getElementById('selectDoctorRoleBtn');

  function close() {
    modalHost.innerHTML = '';
    document.removeEventListener('keydown', handleKeyDown);
    if (typeof onCancel === 'function') {
      onCancel();
    }
  }

  function handleKeyDown(e) {
    if (e.key === 'Escape') {
      close();
    }
  }

  document.addEventListener('keydown', handleKeyDown);

  closeBtn?.addEventListener('click', close);
  cancelBtn?.addEventListener('click', close);
  overlay?.addEventListener('click', (e) => {
    if (e.target === overlay) close();
  });

  userBtn?.addEventListener('click', () => {
    modalHost.innerHTML = '';
    document.removeEventListener('keydown', handleKeyDown);
    if (typeof onSelect === 'function') {
      onSelect('user');
    }
  });

  doctorBtn?.addEventListener('click', () => {
    modalHost.innerHTML = '';
    document.removeEventListener('keydown', handleKeyDown);
    if (typeof onSelect === 'function') {
      onSelect('doctor');
    }
  });
}
