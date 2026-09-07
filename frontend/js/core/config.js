const localPorts = new Set(['3000', '4173', '5500', '8080']);
const localStatic = localPorts.has(window.location.port);
const origin = localStatic ? `${window.location.protocol}//${window.location.hostname}:8000` : window.location.origin;
export const API_BASE = `${origin}/api/v1`;
export const APP_NAME = 'BreastCare AI';
export const AUTH_UI_REVISION = 'auth-v3';

export function cleanAuthUrl() {
  try {
    const url = new URL(window.location.href);
    if (url.searchParams.has('v')) {
      url.searchParams.delete('v');
      const cleanSearch = url.searchParams.toString();
      const newUrl = url.pathname + (cleanSearch ? `?${cleanSearch}` : '') + url.hash;
      window.history.replaceState(window.history.state, '', newUrl);
    }
  } catch (e) {
    // Graceful fallback
  }
}
