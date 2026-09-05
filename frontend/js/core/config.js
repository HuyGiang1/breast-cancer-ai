const localPorts = new Set(['3000', '4173', '5500', '8080']);
const localStatic = localPorts.has(window.location.port);
const origin = localStatic ? `${window.location.protocol}//${window.location.hostname}:8000` : window.location.origin;
export const API_BASE = `${origin}/api/v1`;
export const APP_NAME = 'BreastCare AI';
