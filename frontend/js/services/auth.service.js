import { request } from '../core/api.js';
import { auth } from '../core/auth.js';

export const authService = {
  async login(payload) {
    const result = await request('/auth/login/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    auth.save(result);
    return result;
  },

  async register(payload) {
    const result = await request('/auth/register/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    auth.save(result);
    return result;
  },

  googleConfig: () => request('/auth/google/config/'),

  async googleLogin(credential, role = null) {
    const payload = { credential };
    if (role) {
      payload.role = role;
    }
    const result = await request('/auth/google/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (result.access_token) {
      auth.save(result);
    }
    return result;
  },

  linkGoogle: (credential) =>
    request('/auth/google/link/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ credential }),
    }),

  unlinkGoogle: () =>
    request('/auth/google/unlink/', {
      method: 'POST',
    }),

  me: () => request('/auth/me/'),
  updateProfile: (payload) =>
    request('/auth/profile/', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }),
  changePassword: (payload) =>
    request('/auth/change-password/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }),
  logout: () => request('/auth/logout/', { method: 'POST' }).finally(() => auth.clear()),
  logoutAll: () => request('/auth/logout-all/', { method: 'POST' }).finally(() => auth.clear()),
  forgot: (email) =>
    request('/auth/forgot-password/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email }),
    }),
  reset: (payload) =>
    request('/auth/reset-password/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }),
};
