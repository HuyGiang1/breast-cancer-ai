import { authService } from '../services/auth.service.js';
import { toast } from '../components/toast.js';
import { cleanAuthUrl } from '../core/config.js';

cleanAuthUrl();

document.addEventListener('DOMContentLoaded', () => {
  initForgotPasswordPage();
});

// Run immediately in case DOM is already parsed
if (document.readyState !== 'loading') {
  initForgotPasswordPage();
}

function initForgotPasswordPage() {
  const form = document.getElementById('forgotForm');
  if (!form || form.dataset.initialized) return;
  form.dataset.initialized = 'true';

  const alertBox = document.getElementById('authAlert');
  const emailInput = document.getElementById('forgotEmail');
  const submitBtn = document.getElementById('submitBtn');

  // Pre-fill email from query parameter if present
  const params = new URLSearchParams(window.location.search);
  const prefillEmail = params.get('email');
  if (prefillEmail && emailInput) {
    emailInput.value = prefillEmail;
  }

  function showAlert(message, type = 'error', htmlContent = null) {
    if (alertBox) {
      if (htmlContent) {
        alertBox.innerHTML = htmlContent;
      } else {
        alertBox.textContent = message;
      }
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

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    hideAlert();

    const email = emailInput.value.trim();
    if (!email) {
      showAlert('Please enter your email address.');
      return;
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      showAlert('Please enter a valid email address format.');
      return;
    }

    submitBtn.disabled = true;
    submitBtn.textContent = 'Sending reset link...';

    try {
      const result = await authService.forgot(email);
      const genericMsg = 'If an account exists for this email, a password reset link has been sent.';

      if (result.reset_token) {
        // Development Outbox helper (visible only when APP_MAIL_MODE=file)
        const devUrl = `reset-password.html?token=${encodeURIComponent(result.reset_token)}&v=auth-v3`;
        const html = `
          <div>
            <strong>${genericMsg}</strong>
            <div style="margin-top: 0.75rem; padding: 0.625rem; background: rgba(0, 0, 0, 0.05); border-radius: 6px; font-size: 0.8125rem;">
              <span style="font-weight: 600; color: var(--teal-800, #115e59);">[Development Outbox]</span><br>
              Direct link generated: <a href="${devUrl}" style="color: var(--teal-700, #0f766e); font-weight: 600; text-decoration: underline;">Open Reset Password Page →</a>
            </div>
          </div>
        `;
        showAlert(genericMsg, 'info', html);
      } else {
        showAlert(genericMsg, 'info');
      }

      form.reset();
    } catch (err) {
      // Even on failure, maintain safe response to prevent account enumeration
      showAlert('If an account exists for this email, a password reset link has been sent.', 'info');
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = 'Send reset link';
    }
  });
}
