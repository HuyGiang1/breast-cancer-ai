import { auth } from '../core/auth.js';
const links = [['dashboard.html','Overview'],['research.html','Research Center'],['model-comparison.html','Model Comparison'],['datasets.html','Datasets'],['explainability.html','Explainability'],['calibration.html','Calibration'],['../index.html','Public site']];
export function mountShell(title) {
  const active = location.pathname.split('/').pop() || 'index.html';
  document.body.insertAdjacentHTML('afterbegin', `<aside class="v2-sidebar"><a class="v2-brand" href="dashboard.html">BC <span>BreastCare AI</span></a><nav>${links.map(([href,label]) => `<a class="${href === active ? 'active' : ''}" href="${href}">${label}</a>`).join('')}</nav><small>Research / Educational<br>Not for clinical diagnosis</small></aside><header class="v2-header"><div><span>Research workspace</span><strong>${title}</strong></div><a href="${auth.user() ? 'profile.html' : '../login.html'}">${auth.user()?.full_name || 'Sign in'}</a></header>`);
}
