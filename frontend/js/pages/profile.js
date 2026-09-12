import { requireAuth } from '../core/guards.js';
import { mountShell } from '../components/shell.js';
import { authService } from '../services/auth.service.js';
import { auth } from '../core/auth.js';
import { toast } from '../components/toast.js';
import { bindModalAccessibility } from '../components/workspace.js';

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
  const app = document.querySelector('#app');
  app.innerHTML = `
    <section class="research-main">
      <header class="research-hero">
        <span class="eyebrow">Authenticated Account</span>
        <h1>Account &amp; Security</h1>
        <p>Manage your account identity, role capabilities, connected authentications, and session security.</p>
      </header>
      <div id="profileModalHost"></div>
      <div id="profile" class="profile-grid">
        <section class="studio-card">Loading profile...</section>
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
        <h2>Account Type &amp; Capabilities</h2>

        <div class="profile-account-type-banner ${isDoctor ? 'doctor' : 'personal'}">
          <div>
            <div style="font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.25rem;">
              ${isDoctor ? 'Clinician Workspace' : 'Individual Assessment'}
            </div>
            <strong style="font-size: 1.125rem;">
              ${isDoctor ? 'Doctor / Clinician Account' : 'Personal Analysis Account'}
            </strong>
          </div>
          <span class="v2-badge ${isDoctor ? 'primary' : ''}">
            ${isDoctor ? 'Doctor Role' : 'Personal User'}
          </span>
        </div>

        <div class="profile-account-capabilities">
          <p style="margin: 0 0 0.5rem 0; font-weight: 600; color: var(--slate-800);">Active Capabilities:</p>
          <ul style="margin: 0; padding-left: 1.25rem; color: var(--slate-600); display: flex; flex-direction: column; gap: 0.25rem;">
            <li>Wisconsin Cytology Structured Machine Learning evaluations</li>
            <li>CBIS-DDSM Mammography Deep Learning &amp; Grad-CAM visual explainability</li>
            <li>Experimental Multimodal Decision-Level Fusion analysis</li>
            <li>Personal activity logs and print-ready research reports</li>
            ${
              isDoctor
                ? '<li style="color: #1e40af; font-weight: 600;">Full Patient Registry management (Add / Edit / Delete patients)</li><li style="color: #1e40af; font-weight: 600;">Patient-associated diagnostic evaluations and longitudinal timelines</li>'
                : '<li style="color: var(--slate-500); font-style: italic;">Patient Registry disabled (Personal use only)</li>'
            }
          </ul>
        </div>

        <div class="profile-disclaimer-card">
          <strong>Research &amp; Educational Prototype:</strong>
          This application is strictly designed for research and educational purposes. It does not provide medical licensing, clinical accreditation, or autonomous diagnostic capability. All decisions must be validated by certified medical professionals.
        </div>
      </section>

      <!-- Account Identity -->
      <section class="studio-card">
        <h2>Account Identity</h2>
        <form id="account">
          <label class="v2-field">Full name
            <input class="v2-input" name="full_name" value="${esc(user.full_name || '')}" required>
          </label>
          <label class="v2-field">Email address
            <input class="v2-input" type="email" value="${esc(user.email || '')}" readonly style="background: #f8fafc; color: var(--slate-600);">
          </label>
          <p id="accountStatus" role="status" style="font-size: 0.875rem;"></p>
          <button class="v2-button">Save profile name</button>
        </form>
      </section>

      <!-- Connected Accounts (Google OAuth) -->
      <section class="studio-card">
        <h2>Connected Accounts</h2>
        <p style="color:var(--slate-600);font-size:0.875rem;margin-bottom:1rem;">Link external Google identity for quick sign-in.</p>
        <div id="googleConnection"></div>
        <p id="connectionStatus" role="status" style="margin-top:0.75rem;font-size:0.875rem;"></p>
      </section>

      <!-- Password Security -->
      <section class="studio-card">
        <h2>Password Security</h2>
        <form id="password">
          <label class="v2-field">Current password
            <input class="v2-input" name="current_password" type="password" autocomplete="current-password" required>
          </label>
          <label class="v2-field">New password (8+ characters)
            <input class="v2-input" name="new_password" type="password" minlength="8" autocomplete="new-password" required>
          </label>
          <p id="passwordStatus" role="status" style="font-size: 0.875rem;"></p>
          <button class="v2-button">Change password</button>
        </form>
      </section>

      <!-- Session Security & Logout -->
      <section class="studio-card">
        <h2>Session &amp; Device Security</h2>
        <p style="font-size: 0.875rem; color: var(--slate-600); margin-bottom: 1.25rem;">
          Manage your active research sessions across browsers and workstations.
        </p>

        <div style="display: flex; gap: 0.75rem; flex-wrap: wrap;">
          <button id="logoutThisDeviceBtn" class="v2-button secondary" type="button">
            Sign out (this device)
          </button>
          <button id="logoutAllDevicesBtn" class="v2-button secondary" type="button" style="color: #b91c1c; border-color: #fecaca; background: #fef2f2;">
            Sign out all devices...
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
