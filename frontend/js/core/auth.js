import { storage } from './storage.js';
export const auth = {
  token: () => localStorage.getItem('bcai_token') || '',
  user: () => storage.get('bcai_user'),
  save(payload) { localStorage.setItem('bcai_token', payload.access_token); storage.set('bcai_user', payload.user); },
  clear() { localStorage.removeItem('bcai_token'); storage.remove('bcai_user'); },
};
