import { requireAuth } from '../core/guards.js';
import { mountShell } from '../components/shell.js';
import { authService } from '../services/auth.service.js';
import { auth } from '../core/auth.js';

const esc = (s) =>
  String(s || '').replace(/[&<>"']/g, (c) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[c]));

if (requireAuth()) {
  mountShell('Profile');
  const app = document.querySelector('#app');
  app.innerHTML = `
    <section class="research-main">
      <header class="research-hero">
        <span class="eyebrow">Authenticated account</span>
        <h1>Your profile</h1>
        <p>Account identity, connected authentication, and security for this research prototype.</p>
      </header>
      <div id="profile" class="profile-grid">
        <section class="v2-card">Loading profile...</section>
      </div>
    </section>
  `;
  initProfile();
}

async function initProfile() {
  const root = document.querySelector('#profile');
  try {
    const [user, googleConfig] = await Promise.all([
      authService.me(),
      authService.googleConfig().catch(() => ({ enabled: false })),
    ]);

    root.innerHTML = `
      <section class="v2-card">
        <h2>Account</h2>
        <form id="account">
          <label class="v2-field">Full name
            <input class="v2-input" name="full_name" required>
          </label>
          <label class="v2-field">Email
            <input class="v2-input" type="email" readonly>
          </label>
          <p id="accountStatus" role="status"></p>
          <button class="v2-button">Save name</button>
        </form>
      </section>

      <section class="v2-card">
        <h2>Role / access</h2>
        <dl>
          <div>
            <dt>Role</dt>
            <dd id="role"></dd>
          </div>
        </dl>
        <p>The backend remains the authority for all permissions.</p>
      </section>

      <section class="v2-card">
        <h2>Connected accounts</h2>
        <p style="color:var(--slate-600);font-size:0.875rem;margin-bottom:1rem;">Link external identities to sign in with one click.</p>
        <div id="googleConnection"></div>
        <p id="connectionStatus" role="status" style="margin-top:0.75rem;font-size:0.875rem;"></p>
      </section>

      <section class="v2-card">
        <h2>Security</h2>
        <form id="password">
          <label class="v2-field">Current password
            <input class="v2-input" name="current_password" type="password" autocomplete="current-password" required>
          </label>
          <label class="v2-field">New password
            <input class="v2-input" name="new_password" type="password" minlength="8" autocomplete="new-password" required>
          </label>
          <p id="passwordStatus" role="status"></p>
          <button class="v2-button">Change password</button>
        </form>
      </section>

      <section class="v2-card">
        <h2>Research prototype</h2>
        <p>This account provides access to research and educational workflows. It does not enable clinical diagnosis.</p>
        <button id="logout" class="v2-button secondary" type="button">Sign out</button>
      </section>
    `;

    // Populate Account form
    const account = document.querySelector('#account');
    account.full_name.value = user.full_name || '';
    account.querySelector('input[type=email]').value = user.email || '';
    document.querySelector('#role').textContent = user.role || 'user';

    account.addEventListener('submit', async (event) => {
      event.preventDefault();
      const status = document.querySelector('#accountStatus');
      try {
        const updated = await authService.updateProfile({ full_name: account.full_name.value });
        auth.save({ access_token: auth.token(), user: updated });
        status.textContent = 'Profile name updated.';
      } catch (error) {
        status.textContent = error.message;
      }
    });

    // Populate Password form
    const password = document.querySelector('#password');
    password.addEventListener('submit', async (event) => {
      event.preventDefault();
      const status = document.querySelector('#passwordStatus');
      try {
        const result = await authService.changePassword(Object.fromEntries(new FormData(password)));
        status.textContent = result.message;
        password.reset();
      } catch (error) {
        status.textContent = error.message;
      }
    });

    // Render Connected Accounts
    renderGoogleConnection(user, googleConfig);

    // Logout
    document.querySelector('#logout').addEventListener('click', async () => {
      await authService.logout();
      location.assign('../login.html?v=auth-v3');
    });
  } catch (error) {
    root.innerHTML = `<section class="v2-card"><h2>Profile unavailable</h2><p>${esc(error.message)}</p></section>`;
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
    // Not connected
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
      } catch (e) {
        // Fallback to manual notice
      }
    } else if (connectBtn) {
      connectBtn.onclick = () => {
        statusEl.textContent = config?.client_id
          ? 'Initializing Google Sign-In...'
          : 'Google Sign-In is not configured on this server (GOOGLE_CLIENT_ID required).';
      };
    }
  }
}
