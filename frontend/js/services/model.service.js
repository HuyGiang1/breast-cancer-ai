import { request } from '../core/api.js';
export const modelService = {
  finalStatus: () => request('/models/final/status/'),
  evidence: () => request('/research/evidence/'),
  benchmarks: () => request('/models/benchmarks/'),
  models: () => request('/models/'),
  dlModels: () => request('/models/dl/'),
};
