import { auth } from './auth.js';
export function requireAuth(next = '../login.html?v=auth-v3') { if (!auth.user()) { location.assign(next); return false; } return true; }
export function guestOnly(next = 'index.html') { if (auth.user()) { location.assign(next); return false; } return true; }
export function requireDoctor(fallback = 'history.html') {
  if (!requireAuth()) return false;
  const user = auth.user();
  if (user?.role !== 'doctor') {
    location.assign(fallback);
    return false;
  }
  return true;
}
