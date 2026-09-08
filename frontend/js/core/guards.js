import { auth } from './auth.js';
export function requireAuth(next = '../login.html?v=auth-v3') { if (!auth.user()) { location.assign(next); return false; } return true; }
export function guestOnly(next = 'index.html') { if (auth.user()) { location.assign(next); return false; } return true; }
