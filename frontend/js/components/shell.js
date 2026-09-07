import { auth } from '../core/auth.js';
const esc=value=>String(value??'').replace(/[&<>"']/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
const groups = [['Overview',[['dashboard.html','Dashboard']]],['AI Analysis',[['ml-analysis.html','Structured ML'],['dl-analysis.html','Mammography DL'],['multimodal.html','Experimental Fusion']]],['Research',[['research.html','Research Center'],['model-comparison.html','Model Comparison'],['datasets.html','Datasets'],['explainability.html','Explainability'],['calibration.html','Calibration']]],['Workspace',[['patients.html','Patients'],['history.html','Prediction History'],['reports.html','Reports']]],['Assistant',[['advisor.html','AI Advisor']]],['System',[['model-status.html','Model Status'],['profile.html','Profile']]]];
export function mountShell(title) {
  if (!auth.user()) { document.documentElement.hidden=true; location.replace('../login.html'); return false; }
  const active = location.pathname.split('/').pop() || 'index.html';
  document.body.insertAdjacentHTML('afterbegin', `<aside class="v2-sidebar" id="v2Sidebar"><button class="v2-nav-close" type="button" aria-label="Close navigation">&times;</button><a class="v2-brand" href="dashboard.html">BC <span>BreastCare AI</span></a><nav>${groups.map(([group,links])=>`<section><strong>${group}</strong>${links.map(([href,label]) => `<a class="${href === active ? 'active' : ''}" href="${href}">${label}</a>`).join('')}</section>`).join('')}</nav><small>Research / Educational<br>Not for clinical diagnosis</small></aside><header class="v2-header"><button class="v2-menu" type="button" aria-label="Open navigation" aria-controls="v2Sidebar" aria-expanded="false">Menu</button><div><span>Research workspace</span><strong>${esc(title)}</strong></div><a href="${auth.user() ? 'profile.html' : '../login.html'}">${esc(auth.user()?.full_name || 'Sign in')}</a></header>`);
  const sidebar=document.querySelector('#v2Sidebar'),menu=document.querySelector('.v2-menu');
  const closeMenu=()=>{sidebar?.classList.remove('open');menu?.setAttribute('aria-expanded','false');};
  menu?.addEventListener('click',()=>{const open=sidebar?.classList.toggle('open');menu.setAttribute('aria-expanded',String(Boolean(open)));});
  document.querySelector('.v2-nav-close')?.addEventListener('click',()=>{closeMenu();menu?.focus()});
  sidebar?.querySelector('nav')?.addEventListener('click',event=>{if(event.target.closest('a'))closeMenu()});
  document.addEventListener('keydown',event=>{if(event.key==='Escape'&&sidebar?.classList.contains('open')){closeMenu();menu?.focus()}});
  document.addEventListener('click',async event=>{const link=event.target.closest('a[href*="/predictions/"][href$="/report/"]');if(!link)return;event.preventDefault();try{const response=await fetch(link.href,{headers:{Authorization:`Bearer ${auth.token()}`}});if(!response.ok)throw new Error('Unable to open report.');const url=URL.createObjectURL(await response.blob());window.open(url,'_blank','noopener');setTimeout(()=>URL.revokeObjectURL(url),60000)}catch(error){link.textContent=error.message}});
  return true;
}
