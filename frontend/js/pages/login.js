import { guestOnly } from '../core/guards.js';
import { authService } from '../services/auth.service.js';
import { toast } from '../components/toast.js';
import { cleanAuthUrl } from '../core/config.js';
import { openGoogleRoleModal } from '../components/role-modal.js';
import { renderLanguageSwitcher, bindLanguageSwitcherEvents } from '../core/i18n.js';

cleanAuthUrl();

if (guestOnly('index.html')) {
  initLoginPage();
}

function initLoginPage() {
  const langSlot = document.getElementById('authLangSlot');
  function updateLangSlot() {
    if (langSlot) {
      langSlot.innerHTML = renderLanguageSwitcher();
      bindLanguageSwitcherEvents(langSlot);
    }
  }
  updateLangSlot();
  window.addEventListener('bcai:languageChanged', updateLangSlot);

  const form = document.getElementById('loginForm');
  const alertBox = document.getElementById('authAlert');
  const togglePassBtn = document.getElementById('togglePassword');
  const passInput = document.getElementById('loginPassword');
  const submitBtn = document.getElementById('submitBtn');
  const googleBtnContainer = document.getElementById('googleBtnContainer');
  const googleFallbackBtn = document.getElementById('googleFallbackBtn');

  function showAlert(message, type = 'error') {
    if (alertBox) {
      alertBox.textContent = message;
      alertBox.className = `auth-alert-box ${type}`;
      alertBox.style.display = 'block';
    }
    toast(message, type === 'error' ? 'error' : 'info');
  }

  function hideAlert() {
    if (!alertBox) return;
    alertBox.style.display = 'none';
    alertBox.textContent = '';
  }

  // Password visibility toggle
  if (togglePassBtn && passInput) {
    togglePassBtn.addEventListener('click', () => {
      const isPassword = passInput.type === 'password';
      passInput.type = isPassword ? 'text' : 'password';
      togglePassBtn.textContent = isPassword ? 'Hide' : 'Show';
    });
  }

  // Form submission
  if (form) {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      hideAlert();

      const email = form.email.value.trim();
      const password = form.password.value;

      if (!email || !password) {
        showAlert('Please enter both email address and password.');
        return;
      }

      submitBtn.disabled = true;
      submitBtn.textContent = 'Signing in...';

      try {
        await authService.login({ email, password });
        window.location.assign('index.html');
      } catch (err) {
        showAlert(err.message || 'Authentication failed. Please check your credentials.');
      } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Sign in';
      }
    });
  }

  // Google Sign-In setup
  initGoogleAuth();

  async function initGoogleAuth() {
    try {
      const config = await authService.googleConfig();
      if (config && (config.enabled || config.client_id) && config.client_id) {
        mountGoogleGsi(config.client_id);
      } else {
        mountGoogleNotice();
      }
    } catch (err) {
      console.warn('Google auth configuration query:', err);
      mountGoogleNotice();
    }
  }

  function mountGoogleGsi(clientId) {
    let attempts = 0;
    const checkGsi = () => {
      attempts++;
      if (window.google && window.google.accounts && window.google.accounts.id) {
        try {
          window.google.accounts.id.initialize({
            client_id: clientId,
            callback: handleGoogleCredential,
            auto_select: false,
            cancel_on_tap_outside: true,
          });

          if (googleBtnContainer) {
            googleBtnContainer.innerHTML = '';
            window.google.accounts.id.renderButton(googleBtnContainer, {
              type: 'standard',
              theme: 'outline',
              size: 'large',
              text: 'continue_with',
              shape: 'rectangular',
              logo_alignment: 'left',
              width: googleBtnContainer.offsetWidth || 340,
            });
          }
        } catch (e) {
          console.error('Failed to initialize Google Identity Services:', e);
          mountGoogleNotice();
        }
      } else if (attempts < 30) {
        setTimeout(checkGsi, 100);
      } else {
        mountGoogleNotice();
      }
    };
    checkGsi();
  }

  function mountGoogleNotice() {
    if (googleFallbackBtn) {
      googleFallbackBtn.addEventListener('click', () => {
        showAlert(
          'Google Sign-In integration is active. Please configure GOOGLE_CLIENT_ID in your environment for live OAuth verification.',
          'info'
        );
      });
    }
  }

  async function handleGoogleCredential(response) {
    if (!response || !response.credential) {
      showAlert('Google sign-in did not return a valid credential.');
      return;
    }

    hideAlert();
    showAlert('Verifying Google credentials with research studio...', 'info');

    try {
      const result = await authService.googleLogin(response.credential);
      if (result && result.needs_role_selection) {
        hideAlert();
        openGoogleRoleModal({
          credential: response.credential,
          user: result.user,
          onSelect: async (selectedRole) => {
            showAlert('Creating account with selected role...', 'info');
            try {
              await authService.googleLogin(response.credential, selectedRole);
              window.location.assign('index.html');
            } catch (err) {
              showAlert(err.message || 'Failed to complete registration.');
            }
          },
          onCancel: () => {
            hideAlert();
          },
        });
        return;
      }
      window.location.assign('index.html');
    } catch (err) {
      showAlert(err.message || 'Google authentication failed.');
    }
  }
}
