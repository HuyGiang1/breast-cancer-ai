import { auth } from './auth.js';
export function requireAuth(next = '../login.html') { if (!auth.user()) { location.assign(next); return false; } return true; }
export function guestOnly(next = 'pages/dashboard.html') { if (auth.user()) { location.assign(next); return false; } return true; }
