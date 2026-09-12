import { storage } from './storage.js';

export const auth = {
  token: () => localStorage.getItem('bcai_token') || '',
  user: () => storage.get('bcai_user'),
  clearTransientContext() {
    try {
      sessionStorage.removeItem('bcai_advisor_context');
      sessionStorage.removeItem('bcai_active_analysis');
      sessionStorage.removeItem('bcai_patient_context');
    } catch (e) {
      // safe fallback if storage unavailable
    }
  },
  save(payload, keepTransient = false) {
    if (!keepTransient) {
      this.clearTransientContext();
    }
    localStorage.setItem('bcai_token', payload.access_token);
    storage.set('bcai_user', payload.user);
  },
  clear() {
    this.clearTransientContext();
    localStorage.removeItem('bcai_token');
    storage.remove('bcai_user');
  },
};
