import { request } from '../core/api.js';
export const advisorService = {
  ask: (message, history = []) => request('/chat/ask/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, history }),
  }),
  history: () => request('/chat/history/'),
};
