import { request } from '../core/api.js';

export const patientService = {
  list: () => request('/patients/'),
  get: (id) => request(`/patients/${encodeURIComponent(id)}/`),
  create: (data) =>
    request('/patients/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }),
  update: (id, data) =>
    request(`/patients/${encodeURIComponent(id)}/`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }),
  remove: (id) =>
    request(`/patients/${encodeURIComponent(id)}/`, {
      method: 'DELETE',
    }),
  history: (id) =>
    request(`/predictions/history/?patient_id=${encodeURIComponent(id)}`),
};
