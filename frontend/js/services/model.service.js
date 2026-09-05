import { request } from '../core/api.js';
import { API_BASE } from '../core/config.js';
export const modelService = {
  finalStatus: () => request('/models/final/status/'),
  readiness: async () => {
    const response = await fetch(`${API_BASE.replace(/\/api\/v1$/, '')}/readyz`);
    if (!response.ok) throw new Error('Readiness status is unavailable.');
    return response.json();
  },
  evidence: () => request('/research/evidence/'),
  benchmarks: () => request('/models/benchmarks/'),
  models: () => request('/models/'),
  dlModels: () => request('/models/dl/'),
};
