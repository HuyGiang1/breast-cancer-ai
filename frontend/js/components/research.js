import { t } from '../core/i18n.js';

export const percent = (v) => (v == null ? '—' : `${(Number(v) * 100).toFixed(1)}%`);

export const researchTable = (title, rows, modelKey = 'model') => `
<section class="studio-card">
  <h2>${title}</h2>
  <div class="table-wrap">
    <table class="studio-table">
      <thead>
        <tr>
          <th>${t('research.model', 'Model')}</th>
          <th>${t('research.accuracy', 'Accuracy')}</th>
          <th>${t('research.sensitivity', 'Sensitivity')}</th>
          <th>${t('research.specificity', 'Specificity')}</th>
          <th>${t('research.balancedAccuracy', 'Balanced accuracy')}</th>
          <th>ROC-AUC</th>
          <th>PR-AUC</th>
        </tr>
      </thead>
      <tbody>
        ${rows
          .map(
            (r) => `<tr>
          <th>${r[modelKey] || r.Model}</th>
          <td>${percent(r.accuracy || r.Accuracy)}</td>
          <td>${percent(r.sensitivity || r.Sensitivity)}</td>
          <td>${percent(r.specificity || r.Specificity)}</td>
          <td>${percent(r.balanced_accuracy || r['Balanced Accuracy'])}</td>
          <td>${percent(r.roc_auc || r['ROC-AUC'])}</td>
          <td>${percent(r.pr_auc || r['PR-AUC'])}</td>
        </tr>`
          )
          .join('')}
      </tbody>
    </table>
  </div>
</section>`;

export const limitation = (items) => `
<section class="safety-note">
  <strong>${t('research.limitations', 'Research limitations')}</strong>
  <ul>${items.map((x) => `<li>${x}</li>`).join('')}</ul>
</section>`;

