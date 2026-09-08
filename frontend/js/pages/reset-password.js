import { authService } from '../services/auth.service.js';
import { toast } from '../components/toast.js';

document.addEventListener('DOMContentLoaded', () => {
  initResetPasswordPage();
});

if (document.readyState !== 'loading') {
  initResetPasswordPage();
}

function initResetPasswordPage() {
  const form = document.getElementById('resetForm');
  if (!form || form.dataset.initialized) return;
  form.dataset.initialized = 'true';

  const alertBox = document.getElementById('authAlert');
  const togglePassBtn = document.getElementById('toggleNewPassword');
  const passInput = document.getElementById('newPassword');
  const confirmInput = document.getElementById('confirmPassword');
  const submitBtn = document.getElementById('submitBtn');
  const invalidActions = document.getElementById('invalidTokenActions');
  const titleEl = document.getElementById('resetTitle');
  const subtitleEl = document.getElementById('resetSubtitle');

  // 1. Capture token into memory immediately from URL query parameters
  const urlParams = new URLSearchParams(window.location.search);
  const token = urlParams.get('token');

  // 2. Clean URL without reloading so token is not exposed in address bar
  if (token) {
    try {
      const u = new URL(window.location.href);
      u.searchParams.delete('token');
      u.searchParams.delete('v');
      const q = u.searchParams.toString();
      window.history.replaceState(window.history.state, '', u.pathname + (q ? '?' + q : '') + u.hash);
    } catch (e) {
      // Graceful fallback
    }
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

  // 3. If token is missing, show controlled invalid link state
  if (!token) {
    if (titleEl) titleEl.textContent = 'Invalid reset link';
    if (subtitleEl) subtitleEl.textContent = 'This password reset link is missing a security token.';
    form.style.display = 'none';
    if (invalidActions) invalidActions.style.display = 'block';
    showAlert('Reset link is invalid or incomplete. Please request a new password reset link.', 'error');
    return;
  }

  // Toggle password visibility
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

  // Submit new password
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    hideAlert();

    const newPassword = passInput.value;
    const confirmPassword = confirmInput.value;

    if (!newPassword || newPassword.length < 8) {
      showAlert('Password must be at least 8 characters long.');
      return;
    }

    if (newPassword !== confirmPassword) {
      showAlert('Passwords do not match. Please verify and try again.');
      return;
    }

    submitBtn.disabled = true;
    submitBtn.textContent = 'Updating password...';

    try {
      const result = await authService.reset({
        token: token,
        new_password: newPassword,
      });

      showAlert(result.message || 'Password updated successfully! Redirecting to sign in...', 'info');
      passInput.disabled = true;
      confirmInput.disabled = true;
      submitBtn.textContent = 'Password Updated';

      setTimeout(() => {
        window.location.assign('login.html?v=auth-v3');
      }, 1200);
    } catch (err) {
      submitBtn.disabled = false;
      submitBtn.textContent = 'Reset password';
      const msg = err.message || 'Failed to update password. The link may have expired.';
      showAlert(msg, 'error');
      if (msg.toLowerCase().includes('expired') || msg.toLowerCase().includes('invalid')) {
        if (invalidActions) invalidActions.style.display = 'block';
      }
    }
  });
}
