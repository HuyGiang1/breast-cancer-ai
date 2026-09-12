/* Breast Health Studio — AI Support & Safe Chat Rendering */

function appendFormattedInline(parent, text) {
  // Safe inline formatter: parses **bold** and `code` into DOM nodes without innerHTML
  const regex = /(\*\*.*?\*\*|`.*?`)/g;
  let lastIdx = 0;
  let match;
  while ((match = regex.exec(text)) !== null) {
    if (match.index > lastIdx) {
      parent.appendChild(document.createTextNode(text.substring(lastIdx, match.index)));
    }
    const token = match[0];
    if (token.startsWith('**') && token.endsWith('**')) {
      const strong = document.createElement('strong');
      strong.textContent = token.slice(2, -2);
      parent.appendChild(strong);
    } else if (token.startsWith('`') && token.endsWith('`')) {
      const code = document.createElement('code');
      code.textContent = token.slice(1, -1);
      code.style.background = 'rgba(0,0,0,0.06)';
      code.style.padding = '2px 4px';
      code.style.borderRadius = '4px';
      code.style.fontSize = '0.85em';
      parent.appendChild(code);
    }
    lastIdx = regex.lastIndex;
  }
  if (lastIdx < text.length) {
    parent.appendChild(document.createTextNode(text.substring(lastIdx)));
  }
}

export function renderSafeContent(container, text) {
  if (!text) return;
  const blocks = text.trim().split(/\n\s*\n/);
  for (const block of blocks) {
    const trimmed = block.trim();
    if (!trimmed) continue;

    // Small Headings (###, ##, #)
    if (trimmed.startsWith('#')) {
      const headingText = trimmed.replace(/^#+\s*/, '');
      const h = document.createElement('h4');
      h.style.margin = '0.75rem 0 0.25rem';
      h.style.fontSize = '0.9375rem';
      h.style.fontWeight = '700';
      h.style.color = 'var(--slate-900, #0f172a)';
      appendFormattedInline(h, headingText);
      container.appendChild(h);
      continue;
    }

    const lines = trimmed.split('\n');
    const isBulletList = lines.every((l) => /^\s*[-*•]\s+/.test(l));
    const isNumberedList = lines.every((l) => /^\s*\d+\.\s+/.test(l));

    if (isBulletList) {
      const ul = document.createElement('ul');
      ul.style.margin = '0.5rem 0';
      ul.style.paddingLeft = '1.25rem';
      for (const line of lines) {
        const li = document.createElement('li');
        li.style.marginBottom = '0.25rem';
        const itemText = line.replace(/^\s*[-*•]\s+/, '');
        appendFormattedInline(li, itemText);
        ul.appendChild(li);
      }
      container.appendChild(ul);
    } else if (isNumberedList) {
      const ol = document.createElement('ol');
      ol.style.margin = '0.5rem 0';
      ol.style.paddingLeft = '1.25rem';
      for (const line of lines) {
        const li = document.createElement('li');
        li.style.marginBottom = '0.25rem';
        const itemText = line.replace(/^\s*\d+\.\s+/, '');
        appendFormattedInline(li, itemText);
        ol.appendChild(li);
      }
      container.appendChild(ol);
    } else {
      const p = document.createElement('p');
      p.style.margin = '0.5rem 0';
      p.style.lineHeight = '1.55';
      appendFormattedInline(p, trimmed);
      container.appendChild(p);
    }
  }
}

export function addMessage(container, role, content, meta = '') {
  const article = document.createElement('article');
  article.className = `support-message ${role}`;

  const header = document.createElement('div');
  header.style.display = 'flex';
  header.style.justifyContent = 'space-between';
  header.style.alignItems = 'center';
  header.style.marginBottom = '0.25rem';

  const label = document.createElement('strong');
  label.textContent = role === 'user' ? 'You' : 'AI Guide';
  header.appendChild(label);

  if (role === 'assistant' && content && !content.startsWith('Preparing a research response')) {
    const copyBtn = document.createElement('button');
    copyBtn.type = 'button';
    copyBtn.className = 'btn-copy-response';
    copyBtn.style.cssText =
      'background:none;border:none;cursor:pointer;color:var(--slate-400);font-size:0.75rem;padding:2px 6px;border-radius:4px;';
    copyBtn.textContent = 'Copy';
    copyBtn.title = 'Copy answer to clipboard';
    copyBtn.addEventListener('click', async () => {
      try {
        await navigator.clipboard.writeText(content);
        copyBtn.textContent = 'Copied!';
        setTimeout(() => {
          copyBtn.textContent = 'Copy';
        }, 2000);
      } catch (_) {
        copyBtn.textContent = 'Failed';
      }
    });
    header.appendChild(copyBtn);
  }

  article.appendChild(header);

  const contentWrap = document.createElement('div');
  contentWrap.className = 'message-content';

  if (role === 'assistant') {
    renderSafeContent(contentWrap, content);
  } else {
    const p = document.createElement('p');
    p.textContent = content;
    p.style.margin = '0';
    p.style.lineHeight = '1.55';
    contentWrap.appendChild(p);
  }

  article.appendChild(contentWrap);

  if (meta) {
    const small = document.createElement('small');
    small.className = 'message-meta';
    small.textContent = meta;
    small.style.display = 'block';
    small.style.marginTop = '0.375rem';
    small.style.color = 'var(--slate-400)';
    small.style.fontSize = '0.75rem';
    article.appendChild(small);
  }

  container.appendChild(article);
  container.scrollTop = container.scrollHeight;
  return article;
}

export function statusCard(title, data, details) {
  const healthy = data?.status === 'research_demo';
  const verified = data?.artifact_verified === true;
  return `<article class="studio-card status-card"><header><div><span class="eyebrow">${title}</span><h2>${details.model}</h2></div><span class="status-label ${healthy ? 'healthy' : 'unavailable'}">${healthy ? 'Healthy · Research Demo' : 'Unavailable'}</span></header><dl><div><dt>Dataset</dt><dd>${details.dataset}</dd></div><div><dt>Probability</dt><dd>${details.probability}</dd></div><div><dt>Threshold</dt><dd>${details.threshold}</dd></div><div><dt>Artifact</dt><dd>${verified ? 'Verified' : 'Not verified'}</dd></div><div><dt>Clinical use</dt><dd>${data?.clinical_use === false ? 'false' : 'Unavailable'}</dd></div></dl>${healthy ? '' : '<p>Final research runtime unavailable. No fallback is used.</p>'}</article>`;
}
