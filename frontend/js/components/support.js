export function addMessage(container, role, content, meta = '') {
  const article = document.createElement('article');
  article.className = `support-message ${role}`;
  const label = document.createElement('strong');
  label.textContent = role === 'user' ? 'You' : 'AI Information Assistant';
  const body = document.createElement('p');
  body.textContent = content;
  article.append(label, body);
  if (meta) { const small=document.createElement('small'); small.textContent=meta; article.append(small); }
  container.append(article);
  container.scrollTop = container.scrollHeight;
  return article;
}

export function statusCard(title, data, details) {
  const healthy = data?.status === 'research_demo';
  const verified = data?.artifact_verified === true;
  return `<article class="v2-card status-card"><header><div><span class="eyebrow">${title}</span><h2>${details.model}</h2></div><span class="status-label ${healthy?'healthy':'unavailable'}">${healthy?'Healthy · Research Demo':'Unavailable'}</span></header><dl><div><dt>Dataset</dt><dd>${details.dataset}</dd></div><div><dt>Probability</dt><dd>${details.probability}</dd></div><div><dt>Threshold</dt><dd>${details.threshold}</dd></div><div><dt>Artifact</dt><dd>${verified?'Verified':'Not verified'}</dd></div><div><dt>Clinical use</dt><dd>${data?.clinical_use===false?'false':'Unavailable'}</dd></div></dl>${healthy?'':'<p>Final research runtime unavailable. No fallback is used.</p>'}</article>`;
}
