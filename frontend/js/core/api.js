import { API_BASE } from './config.js';
import { auth } from './auth.js';
export async function request(path, options = {}) {
  const headers = new Headers(options.headers || {});
  if (auth.token()) headers.set('Authorization', `Bearer ${auth.token()}`);
  const response = await fetch(`${API_BASE}${path}`, { ...options, headers });
  const data = response.status === 204 ? null : await response.json().catch(() => null);
  if (!response.ok) { if (response.status === 401) auth.clear(); throw new Error(data?.detail || data?.message || 'Request failed.'); }
  return data;
}
