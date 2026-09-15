import { requireAuth } from '../core/guards.js';
import { mountShell } from '../components/shell.js';
import { modelService } from '../services/model.service.js';
import { statusCard } from '../components/support.js';
import { t } from '../core/i18n.js';

if (requireAuth('../login.html')) {
  mountShell('Model Status');
  const app = document.querySelector('#app');

  function renderSkeleton() {
    app.innerHTML = `
      <section class="research-main">
        <header class="research-hero">
          <span class="eyebrow">${t('modelStatus.runtimeRegistry')}</span>
          <h1>${t('modelStatus.title')}</h1>
          <p>${t('modelStatus.subtitle')}</p>
          <button id="refresh" class="v2-button" type="button">${t('modelStatus.refreshStatus')}</button>
          <small id="checked"></small>
        </header>
        <div id="registry" class="status-grid">
          <section class="studio-card">${t('modelStatus.loadingStatus')}</section>
        </div>
        <section id="health" class="studio-card">${t('modelStatus.loadingReadiness')}</section>
      </section>
    `;
  }

  renderSkeleton();

  const registry = document.querySelector('#registry');
  const health = document.querySelector('#health');
  const checked = document.querySelector('#checked');

  async function load() {
    registry.innerHTML = `<section class="studio-card">${t('modelStatus.loadingStatus')}</section>`;
    health.textContent = t('modelStatus.loadingReadiness');
    try {
      const [status, ready] = await Promise.all([modelService.finalStatus(), modelService.readiness()]);
      registry.innerHTML =
        statusCard('Final ML', status.ml, {
          model: 'Logistic Regression',
          dataset: 'WDBC',
          probability: 'Raw',
          threshold: '0.36',
        }) +
        statusCard('Final DL', status.dl, {
          model: 'EfficientNet-B0',
          dataset: 'CBIS-DDSM',
          probability: 'Raw decision; Platt display/reliability only',
          threshold: '0.515',
        }) +
        `<article class="studio-card status-card">
          <header>
            <div>
              <span class="eyebrow">${t('fusion.title')}</span>
              <h2>${t('fusion.title')}</h2>
            </div>
            <span class="status-label experimental">${t('fusion.badge')}</span>
          </header>
          <dl>
            <div><dt>${t('modelStatus.weights')}</dt><dd>ML 40% · DL 60%</dd></div>
            <div><dt>${t('modelStatus.validation')}</dt><dd>${t('modelStatus.validationDesc')}</dd></div>
            <div><dt>${t('modelStatus.apiStatus')}</dt><dd>${status.multimodal_status === 'experimental_only' ? 'experimental_only' : t('modelStatus.unavailable')}</dd></div>
            <div><dt>${t('modelStatus.clinicalUse')}</dt><dd>${status.clinical_use === false ? 'false' : t('modelStatus.unavailable')}</dd></div>
          </dl>
        </article>`;

      health.innerHTML = `
        <h2>${t('modelStatus.systemReadiness')}</h2>
        <div class="health-grid">
          <span><strong>${t('modelStatus.service')}</strong>${ready.status}</span>
          <span><strong>${t('modelStatus.database')}</strong>${ready.database}</span>
          <span><strong>Final ML</strong>${ready.final_ml}</span>
          <span><strong>Final DL</strong>${ready.final_dl}</span>
        </div>
      `;
      checked.textContent = `${t('modelStatus.lastChecked')} ${new Date().toLocaleString()}`;
    } catch (error) {
      registry.innerHTML = `
        <section class="studio-card">
          <h2>${t('modelStatus.unavailable')}</h2>
          <p>Final research runtime unavailable. No fallback is used.</p>
          <button id="retry" class="v2-button" type="button">Retry</button>
        </section>
      `;
      health.textContent = error.message;
      document.querySelector('#retry')?.addEventListener('click', load);
    }
  }

  document.querySelector('#refresh')?.addEventListener('click', load);
  window.addEventListener('bcai:languageChanged', () => {
    renderSkeleton();
    load();
  });

  load();
}
