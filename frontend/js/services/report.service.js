import { API_BASE } from '../core/config.js';
import { auth } from '../core/auth.js';
import { request } from '../core/api.js';

export const reportService = {
  url: (id) => `${API_BASE}/predictions/${encodeURIComponent(id)}/report/`,
  history: () => request('/predictions/history/'),

  async fetchBlob(id) {
    const token = auth.token();
    const endpoint = this.url(id);
    const headers = {};
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    const res = await fetch(endpoint, {
      method: 'GET',
      headers,
    });
    if (!res.ok) {
      if (res.status === 401) {
        auth.clear();
      }
      let errDetail = 'Failed to fetch analysis report.';
      try {
        const body = await res.json();
        errDetail = body.detail || body.message || errDetail;
      } catch (_) {
        // ignore parse error if not JSON
      }
      throw new Error(errDetail);
    }
    const htmlText = await res.text();
    return new Blob([htmlText], { type: 'text/html;charset=utf-8' });
  },

  async open(id) {
    // 1. Synchronously open placeholder window to prevent popup blockers
    let targetWin = null;
    try {
      targetWin = window.open('about:blank', '_blank');
      if (targetWin) {
        targetWin.document.title = 'Loading Report...';
        targetWin.document.body.innerHTML = `
          <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; color: #334155;">
            <div style="border: 4px solid #f1f5f9; border-top: 4px solid #0284c7; border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; margin-bottom: 16px;"></div>
            <p style="font-size: 15px; font-weight: 500;">Loading authenticated report...</p>
            <style>@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }</style>
          </div>
        `;
      }
    } catch (e) {
      console.warn('Direct window.open unavailable:', e);
    }

    try {
      const blob = await this.fetchBlob(id);
      const blobUrl = URL.createObjectURL(blob);
      if (targetWin && !targetWin.closed) {
        targetWin.location.replace(blobUrl);
        targetWin.addEventListener('unload', () => {
          setTimeout(() => URL.revokeObjectURL(blobUrl), 2000);
        }, { once: true });
      } else {
        const a = document.createElement('a');
        a.href = blobUrl;
        a.target = '_blank';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        setTimeout(() => URL.revokeObjectURL(blobUrl), 60000);
      }
      return targetWin;
    } catch (err) {
      if (targetWin && !targetWin.closed) {
        targetWin.document.body.innerHTML = `
          <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; padding: 40px; text-align: center; color: #b91c1c;">
            <h3>Unable to load report</h3>
            <p>${err.message}</p>
          </div>
        `;
      }
      throw err;
    }
  },

  async print(id) {
    // 1. Synchronously open placeholder window
    let targetWin = null;
    try {
      targetWin = window.open('about:blank', '_blank');
      if (targetWin) {
        targetWin.document.title = 'Preparing for Print...';
        targetWin.document.body.innerHTML = `
          <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; color: #334155;">
            <div style="border: 4px solid #f1f5f9; border-top: 4px solid #0284c7; border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; margin-bottom: 16px;"></div>
            <p style="font-size: 15px; font-weight: 500;">Loading authenticated report for printing...</p>
            <style>@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }</style>
          </div>
        `;
      }
    } catch (e) {
      console.warn('Direct window.open unavailable:', e);
    }

    try {
      const blob = await this.fetchBlob(id);
      const blobUrl = URL.createObjectURL(blob);
      if (targetWin && !targetWin.closed) {
        targetWin.location.replace(blobUrl);
        const triggerPrint = () => {
          try {
            targetWin.focus();
            targetWin.print();
          } catch (printErr) {
            console.warn('Auto-print invocation:', printErr);
          }
        };

        targetWin.addEventListener('load', () => {
          setTimeout(triggerPrint, 500);
        }, { once: true });
        setTimeout(triggerPrint, 1200);

        targetWin.addEventListener('unload', () => {
          setTimeout(() => URL.revokeObjectURL(blobUrl), 2000);
        }, { once: true });
      } else {
        const a = document.createElement('a');
        a.href = blobUrl;
        a.target = '_blank';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        setTimeout(() => URL.revokeObjectURL(blobUrl), 60000);
      }
      return targetWin;
    } catch (err) {
      if (targetWin && !targetWin.closed) {
        targetWin.document.body.innerHTML = `
          <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; padding: 40px; text-align: center; color: #b91c1c;">
            <h3>Unable to print report</h3>
            <p>${err.message}</p>
          </div>
        `;
      }
      throw err;
    }
  }
};
