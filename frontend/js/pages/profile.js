import { requireAuth } from '../core/guards.js';
import { mountShell } from '../components/shell.js';
import { authService } from '../services/auth.service.js';
import { auth } from '../core/auth.js';
import { toast } from '../components/toast.js';
import { bindModalAccessibility } from '../components/workspace.js';
import { t } from '../core/i18n.js';

const esc = (s) =>
  String(s || '').replace(/[&<>"']/g, (c) => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;',
  }[c]));

if (requireAuth()) {
  mountShell('Profile');
  initProfilePage();
}

window.addEventListener('bcai:languageChanged', () => {
  initProfilePage();
});

function initProfilePage() {
  const app = document.querySelector('#app');
  app.innerHTML = `
    <section class="research-main">
      <header class="research-hero">
        <span class="eyebrow">${t('profile.title')}</span>
        <h1>${t('profile.title')}</h1>
        <p>${t('profile.subtitle')}</p>
      </header>
      <div id="profileModalHost"></div>
      <div id="profile" class="profile-grid">
        <section class="studio-card">${t('common.loading')}</section>
      </div>
    </section>
  `;
  initProfile();
}

async function initProfile() {
  const root = document.querySelector('#profile');
  const modalHost = document.querySelector('#profileModalHost');

  try {
    const [user, googleConfig] = await Promise.all([
      authService.me(),
      authService.googleConfig().catch(() => ({ enabled: false })),
    ]);

    const isDoctor = user.role === 'doctor';

    root.innerHTML = `
      <!-- Account Type & Capabilities -->
      <section class="studio-card">
        <h2>${t('profile.role')}</h2>

        <div class="profile-account-type-banner ${isDoctor ? 'doctor' : 'personal'}">
          <div>
            <div style="font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.25rem;">
              ${isDoctor ? t('profile.clinicianAccount') : t('profile.personalAccount')}
            </div>
            <strong style="font-size: 1.125rem;">
              ${isDoctor ? t('auth.roleDoctorTitle') : t('auth.roleUserTitle')}
            </strong>
          </div>
          <span class="v2-badge ${isDoctor ? 'primary' : ''}">
            ${isDoctor ? 'Doctor' : 'User'}
          </span>
        </div>

        <div class="profile-account-capabilities">
          <p style="margin: 0 0 0.5rem 0; font-weight: 600; color: var(--slate-800);">Active Capabilities:</p>
          <ul style="margin: 0; padding-left: 1.25rem; color: var(--slate-600); display: flex; flex-direction: column; gap: 0.25rem;">
            <li>${t('nav.structuredAnalysis')} (WDBC)</li>
            <li>${t('nav.mammographyAnalysis')} (CBIS-DDSM)</li>
            <li>${t('fusion.title')}</li>
            <li>${t('history.title')}</li>
            ${
              isDoctor
                ? `<li style="color: #1e40af; font-weight: 600;">${t('patients.title')}</li>`
                : `<li style="color: var(--slate-500); font-style: italic;">${t('auth.roleUserDesc')}</li>`
            }
          </ul>
        </div>

        <div class="profile-disclaimer-card">
          <strong>${t('common.educationalNotice')}</strong>
        </div>

        <!-- Role Immutability Policy: permanent self-selected role -->
        <div style="margin-top: 0.75rem; font-size: 0.8125rem; color: var(--slate-600); background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 0.75rem 1rem;">
          <strong style="color: #0f172a;">${t('profile.immutableRoleInfo')}</strong>
          <p style="margin: 4px 0 0;">${t('auth.roleImmutableNotice')}</p>
        </div>
      </section>

      <!-- Account Identity -->
      <section class="studio-card">
        <h2>${t('profile.title')}</h2>
        <form id="account">
          <label class="v2-field">${t('profile.fullName')}
            <input class="v2-input" name="full_name" value="${esc(user.full_name || '')}" required>
          </label>
          <label class="v2-field">${t('profile.email')}
            <input class="v2-input" type="email" value="${esc(user.email || '')}" readonly style="background: #f8fafc; color: var(--slate-600);">
          </label>
          <p id="accountStatus" role="status" style="font-size: 0.875rem;"></p>
          <button class="v2-button">${t('common.save')}</button>
        </form>
      </section>

      <!-- Connected Accounts (Google OAuth) -->
      <section class="studio-card">
        <h2>Google OAuth</h2>
        <div id="googleConnection"></div>
        <p id="connectionStatus" role="status" style="margin-top:0.75rem;font-size:0.875rem;"></p>
      </section>

      <!-- Password Security -->
      <section class="studio-card">
        <h2>${t('profile.changePassword')}</h2>
        <form id="password">
          <label class="v2-field">${t('profile.currentPassword')}
            <input class="v2-input" name="current_password" type="password" autocomplete="current-password" required>
          </label>
          <label class="v2-field">${t('profile.newPassword')}
            <input class="v2-input" name="new_password" type="password" minlength="8" autocomplete="new-password" required>
          </label>
          <p id="passwordStatus" role="status" style="font-size: 0.875rem;"></p>
          <button class="v2-button">${t('profile.updatePasswordBtn')}</button>
        </form>
      </section>

      <!-- Session Security & Logout -->
      <section class="studio-card">
        <h2>${t('common.logout')}</h2>
        <div style="display: flex; gap: 0.75rem; flex-wrap: wrap;">
          <button id="logoutThisDeviceBtn" class="v2-button secondary" type="button">
            ${t('common.logout')}
          </button>
          <button id="logoutAllDevicesBtn" class="v2-button secondary" type="button" style="color: #b91c1c; border-color: #fecaca; background: #fef2f2;">
            ${t('common.logout')} (All devices)
          </button>
        </div>
      </section>
    `;

    // Populate Account form
    const accountForm = document.querySelector('#account');
    accountForm.addEventListener('submit', async (event) => {
      event.preventDefault();
      const status = document.querySelector('#accountStatus');
      try {
        const updated = await authService.updateProfile({ full_name: accountForm.full_name.value });
        auth.save({ access_token: auth.token(), user: updated }, true);
        status.style.color = '#15803d';
        status.textContent = 'Profile name updated successfully.';
        toast('Profile name updated.', 'success');
      } catch (error) {
        status.style.color = '#b91c1c';
        status.textContent = error.message;
      }
    });

    // Populate Password form
    const passwordForm = document.querySelector('#password');
    passwordForm.addEventListener('submit', async (event) => {
      event.preventDefault();
      const status = document.querySelector('#passwordStatus');
      try {
        const result = await authService.changePassword(Object.fromEntries(new FormData(passwordForm)));
        status.style.color = '#15803d';
        status.textContent = result.message;
        toast(result.message, 'success');
        passwordForm.reset();
      } catch (error) {
        status.style.color = '#b91c1c';
        status.textContent = error.message;
      }
    });

    // Render Connected Accounts
    renderGoogleConnection(user, googleConfig);

    // Logout this device
    document.querySelector('#logoutThisDeviceBtn')?.addEventListener('click', async () => {
      await authService.logout();
      location.assign('../login.html?v=auth-v3');
    });

    // Logout all devices
    document.querySelector('#logoutAllDevicesBtn')?.addEventListener('click', () => {
      openLogoutAllModal();
    });

    function openLogoutAllModal() {
      modalHost.innerHTML = `
        <div class="workspace-modal-overlay" id="logoutAllModalOverlay" role="dialog" aria-modal="true" aria-labelledby="logoutAllTitle">
          <div class="workspace-modal">
            <div class="workspace-modal-header" style="border-bottom-color: #fee2e2;">
              <h2 class="workspace-modal-title" id="logoutAllTitle" style="color: #b91c1c;">Sign out all devices?</h2>
              <button type="button" class="workspace-modal-close" id="closeLogoutAllBtn" aria-label="Close dialog">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <line x1="18" y1="6" x2="6" y2="18"></line>
                  <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
              </button>
            </div>
            <div class="workspace-modal-body">
              <p style="font-size: 0.9375rem; color: var(--slate-700); line-height: 1.5; margin: 0 0 1rem 0;">
                This revokes all active Breast Health Studio sessions for this account.
              </p>
              <p style="font-size: 0.8125rem; color: var(--slate-500); margin: 0;">
                You will be required to re-authenticate with your credentials on every device.
              </p>
            </div>
            <div class="workspace-modal-footer">
              <button type="button" class="studio-btn studio-btn-outline" id="cancelLogoutAllBtn">Cancel</button>
              <button type="button" class="studio-btn studio-btn-danger" id="confirmLogoutAllBtn" style="background:#dc2626;color:#ffffff;border:none;padding:0.625rem 1.125rem;border-radius:8px;font-weight:600;cursor:pointer;">Sign out everywhere</button>
            </div>
          </div>
        </div>
      `;

      const closeBtn = document.querySelector('#closeLogoutAllBtn');
      const cancelBtn = document.querySelector('#cancelLogoutAllBtn');
      const confirmBtn = document.querySelector('#confirmLogoutAllBtn');
      const overlay = document.querySelector('#logoutAllModalOverlay');

      let modalCleanup = null;
      const close = () => {
        if (modalCleanup) { modalCleanup(); modalCleanup = null; }
        modalHost.innerHTML = '';
      };

      if (overlay) {
        modalCleanup = bindModalAccessibility(overlay, close);
      }

      closeBtn?.addEventListener('click', close);
      cancelBtn?.addEventListener('click', close);
      overlay?.addEventListener('click', (e) => {
        if (e.target === overlay) close();
      });

      confirmBtn?.addEventListener('click', async () => {
        confirmBtn.disabled = true;
        confirmBtn.textContent = 'Signing out...';
        try {
          await authService.logoutAll();
          location.assign('../login.html?v=auth-v3');
        } catch (err) {
          toast(err.message || 'Failed to sign out of all devices.', 'error');
          close();
        }
      });
    }
  } catch (error) {
    root.innerHTML = `<section class="studio-card"><h2>Profile unavailable</h2><p>${esc(error.message)}</p></section>`;
  }
}

function renderGoogleConnection(user, config) {
  const container = document.querySelector('#googleConnection');
  const statusEl = document.querySelector('#connectionStatus');
  if (!container) return;

  const googleAccount = user.oauth_accounts?.find((a) => a.provider === 'google');

  if (googleAccount) {
    container.innerHTML = `
      <div style="display:flex;align-items:center;justify-content:space-between;gap:1rem;flex-wrap:wrap;padding:0.875rem 1rem;background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;">
        <div>
          <div style="display:flex;align-items:center;gap:0.5rem;">
            <strong style="color:#0f172a;">Google</strong>
            <span style="display:inline-block;padding:0.125rem 0.5rem;background:#ecfdf5;color:#065f46;border-radius:999px;font-size:0.75rem;font-weight:600;">Connected</span>
          </div>
          <div style="font-size:0.8125rem;color:#475569;margin-top:0.25rem;">Linked account: <code>${esc(googleAccount.email)}</code></div>
        </div>
        <div>
          ${
            user.has_password
              ? `<button id="disconnectGoogleBtn" class="v2-button secondary" type="button" style="font-size:0.8125rem;padding:0.375rem 0.75rem;">Disconnect</button>`
              : `<small style="color:#64748b;">Set a password to disconnect</small>`
          }
        </div>
      </div>
    `;

    const disconnectBtn = document.querySelector('#disconnectGoogleBtn');
    if (disconnectBtn) {
      disconnectBtn.onclick = async () => {
        if (!confirm('Are you sure you want to disconnect this Google account?')) return;
        try {
          disconnectBtn.disabled = true;
          statusEl.textContent = 'Disconnecting Google account...';
          await authService.unlinkGoogle();
          statusEl.textContent = 'Google account disconnected successfully.';
          const updatedUser = await authService.me();
          renderGoogleConnection(updatedUser, config);
        } catch (err) {
          statusEl.textContent = err.message || 'Failed to disconnect.';
          disconnectBtn.disabled = false;
        }
      };
    }
  } else {
    container.innerHTML = `
      <div style="padding:0.875rem 1rem;background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;">
        <div style="margin-bottom:0.75rem;">
          <div style="display:flex;align-items:center;gap:0.5rem;">
            <strong style="color:#0f172a;">Google</strong>
            <span style="display:inline-block;padding:0.125rem 0.5rem;background:#f1f5f9;color:#64748b;border-radius:999px;font-size:0.75rem;">Not connected</span>
          </div>
          <p style="font-size:0.8125rem;color:#475569;margin:0.375rem 0 0;">Connect your personal Google account to sign in seamlessly.</p>
        </div>
        <div id="googleConnectBtnContainer">
          <button id="connectGoogleFallbackBtn" class="v2-button" type="button" style="font-size:0.8125rem;padding:0.375rem 0.875rem;">Connect Google</button>
        </div>
      </div>
    `;

    const connectBtn = document.querySelector('#connectGoogleFallbackBtn');
    const btnContainer = document.querySelector('#googleConnectBtnContainer');

    if (config && config.client_id && window.google?.accounts?.id) {
      try {
        window.google.accounts.id.initialize({
          client_id: config.client_id,
          callback: async (response) => {
            if (!response || !response.credential) return;
            statusEl.textContent = 'Connecting Google account...';
            try {
              await authService.linkGoogle(response.credential);
              statusEl.textContent = 'Google account connected successfully!';
              const updatedUser = await authService.me();
              renderGoogleConnection(updatedUser, config);
            } catch (err) {
              statusEl.textContent = err.message || 'Failed to connect Google account.';
            }
          },
        });
        window.google.accounts.id.renderButton(btnContainer, {
          type: 'standard',
          theme: 'outline',
          size: 'medium',
          text: 'continue_with',
          shape: 'rectangular',
        });
      } catch (e) {}
    } else if (connectBtn) {
      connectBtn.onclick = () => {
        statusEl.textContent = config?.client_id
          ? 'Initializing Google Sign-In...'
          : 'Google Sign-In is not configured on this server (GOOGLE_CLIENT_ID required).';
      };
    }
  }
}
