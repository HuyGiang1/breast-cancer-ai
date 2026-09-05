export const metricCard=({label,value,detail=''})=>`<article class="v2-card"><span class="eyebrow">${label}</span><h2>${value}</h2><p>${detail}</p></article>`;
export const emptyState=(title,detail)=>`<section class="v2-card"><h2>${title}</h2><p>${detail}</p></section>`;
export const errorState=(message)=>`<section class="v2-card"><h2>Unable to load</h2><p>${message}</p></section>`;
export const loading=()=>'<section class="v2-card" aria-busy="true">Loading research workspace…</section>';
