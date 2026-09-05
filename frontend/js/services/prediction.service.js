import { request } from '../core/api.js';
export const predictionService = {
  ml: (payload, model) => request(`/predict/${model ? `?model_name=${encodeURIComponent(model)}` : ''}`, { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(payload) }),
  dl: (file, model) => { const body = new FormData(); body.append('image', file); if (model) body.append('model_name', model); return request('/predict/image/', { method: 'POST', body }); },
  history: () => request('/predictions/history/'),
};
