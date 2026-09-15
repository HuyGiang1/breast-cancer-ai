import { API_BASE } from './config.js';
import { auth } from './auth.js';
import { t } from './i18n.js';

export async function request(path, options = {}) {
  const headers = new Headers(options.headers || {});
  if (auth.token()) headers.set('Authorization', `Bearer ${auth.token()}`);
  const response = await fetch(`${API_BASE}${path}`, { ...options, headers });
  const data = response.status === 204 ? null : await response.json().catch(() => null);
  if (!response.ok) {
    if (response.status === 401) auth.clear();
    if (data?.detail) {
      throw new Error(typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail));
    }
    if (data?.message) {
      throw new Error(String(data.message));
    }
    if (response.status === 413) {
      throw new Error(t('errors.payloadTooLarge', { defaultValue: 'Image upload is too large. Maximum upload size is 20 MB (HTTP 413).' }));
    }
    if (response.status === 502) {
      throw new Error(t('errors.badGateway', { defaultValue: 'Service temporarily unavailable (HTTP 502 Bad Gateway).' }));
    }
    if (response.status === 504) {
      throw new Error(t('errors.gatewayTimeout', { defaultValue: 'Gateway timeout. Analysis request took too long (HTTP 504).' }));
    }
    if (response.status === 500) {
      throw new Error(t('errors.internalError', { defaultValue: 'Internal server error occurred (HTTP 500).' }));
    }
    throw new Error(t('errors.requestFailed', { status: response.status, defaultValue: `Request failed (HTTP ${response.status}${response.statusText ? ` ${response.statusText}` : ''}).` }));
  }
  return data;
}
