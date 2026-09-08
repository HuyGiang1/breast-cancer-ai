import { guestOnly } from '../core/guards.js';
import { authService } from '../services/auth.service.js';
import { toast } from '../components/toast.js';
import { cleanAuthUrl } from '../core/config.js';

cleanAuthUrl();

if (guestOnly('index.html')) {
  initRegisterPage();
}

function initRegisterPage() {
  const form = document.getElementById('registerForm');
  const alertBox = document.getElementById('authAlert');
  const togglePassBtn = document.getElementById('toggleRegPassword');
  const passInput = document.getElementById('regPassword');
  const confirmInput = document.getElementById('regConfirm');
  const submitBtn = document.getElementById('submitBtn');
  const googleBtnContainer = document.getElementById('googleBtnContainer');
  const googleFallbackBtn = document.getElementById('googleFallbackBtn');

  function escapeHtml(str) {
    return String(str || '').replace(/[&<>"']/g, c => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[c]));
  }

  function showResolutionAlert(email) {
    if (alertBox) {
      alertBox.className = 'auth-alert-box warning account-resolution-card';
      alertBox.innerHTML = `
        <div class="resolution-content">
          <div class="resolution-title">This email already has an account.</div>
          <p class="resolution-desc">An account for <code>${escapeHtml(email)}</code> is already registered in Breast Health Studio.</p>
          <div class="resolution-actions">
            <a href="login.html?v=auth-v3" class="studio-btn studio-btn-primary studio-btn-sm">Sign in</a>
            <a href="forgot-password.html?v=auth-v3" class="studio-btn studio-btn-outline studio-btn-sm">Reset password</a>
          </div>
          <p class="resolution-note">
            <small><strong>Note on Google:</strong> If this account was created with a password, sign in with your password first, then connect Google in Profile / Account Settings.</small>
          </p>
        </div>
      `;
      alertBox.style.display = 'block';
    }
    toast('This email already has an account.', 'info');
  }

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
      if (confirmInput) {
        confirmInput.type = isPassword ? 'text' : 'password';
      }
      togglePassBtn.textContent = isPassword ? 'Hide' : 'Show';
    });
  }

  // Form submission
  if (form) {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      hideAlert();

      const fullName = form.full_name.value.trim();
      const email = form.email.value.trim();
      const password = form.password.value;
      const confirm = form.confirm.value;

      if (!fullName) {
        showAlert('Please enter your full name.');
        return;
      }

      if (!email) {
        showAlert('Please enter a valid email address.');
        return;
      }

      // Simple email validation regex
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(email)) {
        showAlert('Please enter a valid email address format.');
        return;
      }

      if (password.length < 8) {
        showAlert('Password must be at least 8 characters long.');
        return;
      }

      if (password !== confirm) {
        showAlert('Passwords do not match. Please verify and try again.');
        return;
      }

      submitBtn.disabled = true;
      submitBtn.textContent = 'Creating account...';

      try {
        // Public registration always assigns role='user' on server
        await authService.register({
          full_name: fullName,
          email: email,
          password: password,
        });

        // Auto-login session saved in authService.register; redirect to overview
        window.location.assign('index.html');
      } catch (err) {
        const msg = String(err.message || '');
        if (msg.toLowerCase().includes('already registered') || err.status === 409) {
          showResolutionAlert(email);
        } else {
          showAlert(msg || 'Account creation failed. Please try again.');
        }
      } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Create account';
      }
    });
  }

  // Google Sign-In setup
  initGoogleAuth();

  async function initGoogleAuth() {
    try {
      const config = await authService.googleConfig();
      if (config && config.enabled && config.client_id) {
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
    showAlert('Creating and verifying research workspace session with Google...', 'info');

    try {
      await authService.googleLogin(response.credential);
      window.location.assign('index.html');
    } catch (err) {
      showAlert(err.message || 'Google account authentication failed.');
    }
  }
}
