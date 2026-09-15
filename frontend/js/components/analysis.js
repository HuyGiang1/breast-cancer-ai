import { featureLabel } from '../config/ml-features.js';
import { probabilityBar } from './probability-bar.js';
import { t } from '../core/i18n.js';

const esc = (value) =>
  String(value ?? '').replace(/[&<>"']/g, (char) => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;',
  }[char]));

export const featureSection = (title, features) =>
  `<section class="feature-section"><h2>${title}</h2><div class="feature-fields">${features.map((key) => `<label class="v2-field" for="${key}">${featureLabel(key)}<input class="v2-input" id="${key}" name="${key}" type="number" min="0" step="any" required></label>`).join('')}</div></section>`;

export const resultCard = (r, { dataset, threshold, calibrated = false } = {}) => {
  const isMalignant = r.diagnosis === 'Malignant';
  const diagLabel = isMalignant ? t('common.malignant', { defaultValue: 'Malignant' }) : t('common.benign', { defaultValue: 'Benign' });

  return `<section class="studio-card studio-result" aria-live="polite">
    <span class="eyebrow">${t('common.prediction', { defaultValue: 'Model prediction' })}</span>
    <h2>${diagLabel} (${esc(r.diagnosis)})</h2>
    <p><strong>${t('common.rawProbability', { defaultValue: 'Raw malignant probability' })}:</strong> ${(Number(r.raw_probability ?? r.probability) * 100).toFixed(1)}%</p>
    ${probabilityBar(r.raw_probability ?? r.probability, threshold, t('common.rawProbability', { defaultValue: 'Raw malignant probability' }))}
    <p>${t('common.threshold', { defaultValue: 'Decision threshold' })}: ${threshold} raw</p>
    ${calibrated ? `<hr><p><strong>${t('common.calibratedProbability', { defaultValue: 'Reliability-adjusted display probability' })}:</strong> ${(Number(r.calibrated_probability ?? r.probability) * 100).toFixed(1)}%</p><p>Platt calibration · display/reliability only</p>` : ''}
    <dl>
      <dt>Model</dt><dd>${esc(r.model_name)}</dd>
      <dt>Dataset</dt><dd>${esc(dataset)}</dd>
      <dt>Clinical use</dt><dd>false</dd>
    </dl>
    <p class="safety-note">${t('common.educationalNotice', { defaultValue: 'Research / Educational Prototype. Not for clinical diagnosis.' })}</p>
  </section>`;
};

export const collectFeatures = (form, features) =>
  Object.fromEntries(features.map((key) => [key, Number(form.elements[key].value)]));

