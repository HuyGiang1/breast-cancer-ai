import { requireAuth } from '../core/guards.js';
import { mountShell } from '../components/shell.js';
import { advisorService } from '../services/advisor.service.js';
import { addMessage } from '../components/support.js';
import { esc } from '../components/workspace.js';
import { t, getLanguage } from '../core/i18n.js';

if (requireAuth('../login.html?v=auth-v3')) {
  mountShell('AI Guide');
  initAdvisorPage();
}

async function initAdvisorPage() {
  const app = document.querySelector('#app');
  const isVi = getLanguage() === 'vi';

  // Check contextual handoff from structured analysis, mammography, or fusion
  let contextData = null;
  try {
    const raw = sessionStorage.getItem('bcai_advisor_context');
    if (raw) contextData = JSON.parse(raw);
  } catch (_) {
    contextData = null;
  }

  let contextBannerHtml = '';
  let pageHeaderTitle = t('advisor.title', 'AI Guide');
  let dynamicSuggestions = isVi ? [
    'Giải thích cách mô hình đưa ra dự đoán',
    'Hiệu chuẩn xác suất (Platt Calibration) có ý nghĩa gì?',
    'Đặc trưng hình thái nhân đóng góp như thế nào (SHAP)?',
    'Bản đồ nhiệt Grad-CAM nên được diễn giải như thế nào?',
    'Tại sao nhánh tế bào học WDBC và ảnh nhũ ảnh không so sánh trực tiếp được?',
    'Những giới hạn nghiên cứu chính của tập dữ liệu là gì?',
    'Ngưỡng quyết định 0.515 của mô hình DL thể hiện điều gì?',
    'Tại sao kết hợp đa nhánh lại được xem là thực nghiệm?',
  ] : [
    'Explain how model predictions are generated',
    'What does probability calibration mean?',
    'What is SHAP feature attribution?',
    'How should Grad-CAM attention heatmaps be interpreted?',
    'Why are Wisconsin ML and Mammography DL not directly comparable?',
    'What are the key research dataset limitations?',
    'What does the DL decision threshold 0.515 represent?',
    'Why is multimodal fusion considered experimental?',
  ];

  if (contextData) {
    const isFusion = contextData.analysis_type === 'fusion';
    const isDl = contextData.analysis_type === 'dl';
    const pId = contextData.prediction_id ? `#${contextData.prediction_id}` : 'Recent Session';

    if (isFusion) {
      pageHeaderTitle = 'AI Guide — Multimodal Analysis Context';
      const mlProbStr = (Number(contextData.ml_raw_probability ?? 0) * 100).toFixed(1);
      const dlProbStr = (Number(contextData.dl_raw_probability ?? 0) * 100).toFixed(1);
      const combinedScoreStr = (Number(contextData.combined_malignant_score ?? 0) * 100).toFixed(1);
      const agreeText = contextData.branch_agreement ? 'Branch Agreement' : 'Branch Disagreement';
      const agreeColor = contextData.branch_agreement ? 'var(--teal-700, #0f766e)' : 'var(--amber-700, #b45309)';

      contextBannerHtml = `
        <div class="advisor-context-banner" style="background:#f0fdfa;border:1.5px solid #99f6e4;border-radius:10px;padding:14px 18px;margin-bottom:1.25rem;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;">
          <div>
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;flex-wrap:wrap;">
              <span style="background:#0f766e;color:#fff;font-size:0.75rem;font-weight:700;padding:2px 8px;border-radius:4px;text-transform:uppercase;">
                Active Context
              </span>
              <strong style="color:#0f766e;font-size:0.9375rem;">Experimental Fusion ${esc(pId)}</strong>
              <span style="font-size:0.8125rem;font-weight:700;color:${agreeColor};">(${esc(agreeText)})</span>
            </div>
            <div style="font-size:0.875rem;color:var(--slate-700);">
              <span>Structured ML: <strong>${esc(contextData.ml_classification || 'N/A')}</strong> (${mlProbStr}%)</span> ·
              <span>Mammography DL: <strong>${esc(contextData.dl_classification || 'N/A')}</strong> (${dlProbStr}%)</span> ·
              <span>Combined Score: <strong>${combinedScoreStr}%</strong> (0.50 software midpoint)</span>
            </div>
            <div style="font-size:0.75rem;color:var(--slate-500);margin-top:4px;">
              Experimental combination of unpaired WDBC and CBIS-DDSM models; not a validated multimodal diagnosis.
            </div>
          </div>
          <button id="clearContextBtn" class="studio-btn studio-btn-outline studio-btn-sm" type="button">
            Dismiss Context
          </button>
        </div>
      `;

      dynamicSuggestions = [
        'Why can the ML and DL branches produce disagreeing outputs?',
        'Explain how the 40/60 weighted combination was calculated.',
        'Why are WDBC and CBIS-DDSM considered unpaired datasets?',
        'How should I interpret the 0.50 software decision midpoint?',
        'Explain the Grad-CAM heatmap from the DL branch.',
        'Why can this software combination NOT be used as a clinical diagnosis?',
      ];
    } else {
      const probStr = (Number(contextData.raw_probability ?? 0) * 100).toFixed(1);
      const contextTitle = isDl ? `Mammography DL Analysis ${pId}` : `Structured ML Analysis ${pId}`;
      pageHeaderTitle = isDl ? 'AI Guide — Mammography Context' : 'AI Guide — Structured Feature Context';

      contextBannerHtml = `
        <div class="advisor-context-banner" style="background:#f0fdfa;border:1.5px solid #99f6e4;border-radius:10px;padding:14px 18px;margin-bottom:1.25rem;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;">
          <div>
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;flex-wrap:wrap;">
              <span style="background:#0f766e;color:#fff;font-size:0.75rem;font-weight:700;padding:2px 8px;border-radius:4px;text-transform:uppercase;">
                Active Context
              </span>
              <strong style="color:#0f766e;font-size:0.9375rem;">${esc(contextTitle)}</strong>
            </div>
            <div style="font-size:0.875rem;color:var(--slate-700);">
              Classification: <strong>${esc(contextData.classification || 'N/A')}</strong> ·
              Raw Malignant Probability: <strong>${probStr}%</strong> (Threshold: ${esc(contextData.threshold)})
              ${contextData.calibrated_probability != null ? ` · Calibrated: <strong>${(Number(contextData.calibrated_probability) * 100).toFixed(1)}%</strong>` : ''}
              ${contextData.gradcam_status ? ` · Grad-CAM: <strong>${esc(contextData.gradcam_status)}</strong>` : ''}
            </div>
          </div>
          <button id="clearContextBtn" class="studio-btn studio-btn-outline studio-btn-sm" type="button">
            Dismiss Context
          </button>
        </div>
      `;

      if (isDl) {
        dynamicSuggestions = [
          `Explain why the DL model predicted ${contextData.classification}`,
          `What does the raw probability of ${probStr}% mean relative to threshold ${contextData.threshold}?`,
          'How should the Grad-CAM model-attention heatmap be interpreted?',
          'Why does Grad-CAM not establish tumor localization or boundaries?',
          'What does Platt calibration mean for this mammogram?',
          ...dynamicSuggestions.slice(0, 3),
        ];
      } else {
        dynamicSuggestions = [
          `Explain why the ML model predicted ${contextData.classification}`,
          'Which nuclear morphology features contributed most to this result?',
          `What does the raw probability of ${probStr}% mean relative to threshold ${contextData.threshold}?`,
          ...dynamicSuggestions.slice(0, 5),
        ];
      }
    }
  }

  app.innerHTML = `
    <section class="research-main">
      <header class="research-hero">
        <span class="eyebrow">${t('advisor.eyebrow')}</span>
        <h1 id="advisorHeading">${esc(pageHeaderTitle)}</h1>
        <p>${t('advisor.desc')}</p>
      </header>

      ${contextBannerHtml}

      <div class="support-layout">
        <section class="studio-card chat-panel">
          <div class="chat-toolbar" style="display:flex;align-items:center;justify-content:space-between;margin-bottom:1rem;border-bottom:1px solid var(--border-subtle);padding-bottom:0.75rem;">
            <div style="display:flex;align-items:center;gap:8px;">
              <strong style="color:var(--slate-800);">${t('advisor.conversation')}</strong>
              <span style="font-size:0.75rem;color:var(--slate-500);">${t('advisor.historyUnchanged')}</span>
            </div>
            <button id="clear" class="studio-btn studio-btn-outline studio-btn-sm" type="button">${t('advisor.newConversation')}</button>
          </div>

          <div id="messages" class="support-messages" aria-live="polite" style="max-height:480px;overflow-y:auto;padding-right:4px;">
            <p class="v2-empty" id="empty">${t('advisor.emptyHint')}</p>
          </div>

          <p id="status" role="status" style="font-size:0.8125rem;color:var(--slate-500);margin:0.5rem 0;min-height:1.25rem;"></p>

          <form id="composer" class="chat-composer" style="margin-top:0.5rem;">
            <label for="message" style="display:block;font-size:0.875rem;font-weight:600;margin-bottom:0.375rem;color:var(--slate-700);">${t('advisor.questionLabel')}</label>
            <textarea id="message" class="form-input" rows="3" placeholder="${t('advisor.chatPlaceholder')}" required style="width:100%;resize:vertical;"></textarea>
            <div style="display:flex;justify-content:space-between;align-items:center;margin-top:0.625rem;">
              <span style="font-size:0.75rem;color:var(--slate-400);">${t('advisor.enterHint')}</span>
              <button class="studio-btn studio-btn-primary" id="btnSendMessage" type="submit">${t('advisor.sendBtn')}</button>
            </div>
          </form>
        </section>

        <aside class="studio-card prompt-panel">
          <h2 style="font-size:1rem;font-weight:700;color:var(--slate-800);margin-bottom:0.75rem;">${t('advisor.suggestedTopics')}</h2>
          <div id="suggestedPromptsList" style="display:flex;flex-direction:column;gap:0.5rem;">
            ${dynamicSuggestions
              .map(
                (q) => `
              <button class="suggested-prompt studio-btn studio-btn-outline studio-btn-sm" type="button" data-prompt="${esc(q)}" style="text-align:left;white-space:normal;line-height:1.35;font-size:0.8125rem;padding:0.5rem 0.75rem;">
                ${esc(q)}
              </button>
            `
              )
              .join('')}
          </div>
        </aside>
      </div>
    </section>
  `;

  const messages = document.querySelector('#messages');
  const status = document.querySelector('#status');
  const form = document.querySelector('#composer');
  const input = document.querySelector('#message');
  const sendBtn = document.querySelector('#btnSendMessage');
  let turns = [];

  const removeEmpty = () => document.querySelector('#empty')?.remove();

  async function send(message) {
    const clean = message.trim();
    if (!clean) return;
    removeEmpty();
    addMessage(messages, 'user', clean);
    turns.push({ role: 'user', content: clean });
    input.value = '';

    const pending = addMessage(messages, 'assistant', 'Preparing a research response...');
    status.textContent = 'Assistant is generating response...';
    if (sendBtn) sendBtn.disabled = true;

    try {
      // Grounding: Build explicit contextual system wrapper for first turns
      let payloadMessage = clean;
      if (contextData && turns.length <= 2) {
        if (contextData.analysis_type === 'fusion') {
          const mlProbStr = (Number(contextData.ml_raw_probability ?? 0) * 100).toFixed(1);
          const dlProbStr = (Number(contextData.dl_raw_probability ?? 0) * 100).toFixed(1);
          const combinedScoreStr = (Number(contextData.combined_malignant_score ?? 0) * 100).toFixed(1);
          const agreeText = contextData.branch_agreement ? 'Branch Agreement' : 'Branch Disagreement';
          payloadMessage = `[Context: Experimental Fusion Analysis; Structured Branch: Model=${contextData.ml_model || 'Logistic Regression'}, Classification=${contextData.ml_classification || 'N/A'}, Raw prob=${mlProbStr}%, Threshold=0.360; Mammography Branch: Model=EfficientNet-B0, Classification=${contextData.dl_classification || 'N/A'}, Raw prob=${dlProbStr}%, Threshold=0.515, Grad-CAM=${contextData.dl_gradcam || 'available'}; Combined Malignant Score=${combinedScoreStr}%, Midpoint=0.50; Branch Agreement=${agreeText}; Unpaired Branches=true. Mandatory Limitation: Experimental software combination of unpaired WDBC and CBIS-DDSM outputs; not a validated multimodal diagnosis.] ${clean}`;
        } else if (contextData.analysis_type === 'dl') {
          const probStr = (Number(contextData.raw_probability ?? 0) * 100).toFixed(1);
          const calProbStr = contextData.calibrated_probability != null ? `${(Number(contextData.calibrated_probability) * 100).toFixed(1)}%` : 'N/A';
          payloadMessage = `[Context: Mammography Research Analysis on CBIS-DDSM; Model=EfficientNet-B0; Classification=${contextData.classification}; Raw probability=${probStr}%; Threshold=0.515; Calibrated probability=${calProbStr}; Grad-CAM=${contextData.gradcam_status || 'available'}] ${clean}`;
        } else {
          const probStr = (Number(contextData.raw_probability ?? 0) * 100).toFixed(1);
          payloadMessage = `[Context: Structured Feature Analysis on WDBC; Model=${contextData.model || 'Logistic Regression'}; Classification=${contextData.classification}; Raw probability=${probStr}%; Threshold=0.360] ${clean}`;
        }
      }

      const result = await advisorService.ask(payloadMessage, turns.slice(-10, -1));
      pending.remove();
      addMessage(messages, 'assistant', result.answer, `${result.provider} · ${result.model}`);
      turns.push({ role: 'assistant', content: result.answer });
      status.textContent = 'Response received.';
    } catch (error) {
      pending.remove();
      const errArticle = addMessage(messages, 'assistant', `Unable to answer: ${error.message}`);
      const retryBtn = document.createElement('button');
      retryBtn.type = 'button';
      retryBtn.className = 'studio-btn studio-btn-outline studio-btn-sm';
      retryBtn.style.marginTop = '0.5rem';
      retryBtn.textContent = 'Retry Question';
      retryBtn.addEventListener('click', () => {
        errArticle.remove();
        send(clean);
      });
      errArticle.querySelector('.message-content')?.appendChild(retryBtn);
      status.textContent = 'The request could not be completed.';
    } finally {
      if (sendBtn) sendBtn.disabled = false;
      input.focus();
    }
  }

  form.addEventListener('submit', (event) => {
    event.preventDefault();
    send(input.value);
  });

  input.addEventListener('keydown', (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      form.requestSubmit();
    }
  });

  document.querySelectorAll('.suggested-prompt').forEach((button) => {
    button.addEventListener('click', () => {
      send(button.dataset.prompt);
    });
  });

  document.querySelector('#clearContextBtn')?.addEventListener('click', () => {
    sessionStorage.removeItem('bcai_advisor_context');
    window.location.reload();
  });

  document.querySelector('#clear').addEventListener('click', () => {
    turns = [];
    messages.replaceChildren();
    const empty = document.createElement('p');
    empty.id = 'empty';
    empty.className = 'v2-empty';
    empty.textContent = 'Local conversation reset. Saved account history is unchanged.';
    messages.append(empty);
    status.textContent = 'Local conversation reset.';
  });

  // Load and render past conversation history
  try {
    const saved = await advisorService.history();
    if (Array.isArray(saved) && saved.length > 0) {
      removeEmpty();

      // Progressive disclosure: render divider for past history
      const divider = document.createElement('div');
      divider.className = 'chat-history-divider';
      divider.style.cssText = 'display:flex;align-items:center;margin:1rem 0;color:var(--slate-400);font-size:0.75rem;';
      divider.innerHTML = `
        <hr style="flex:1;border:none;border-top:1px solid var(--border-subtle);">
        <span style="padding:0 0.75rem;font-weight:600;text-transform:uppercase;letter-spacing:0.05em;">Previous Saved Conversations</span>
        <hr style="flex:1;border:none;border-top:1px solid var(--border-subtle);">
      `;
      messages.appendChild(divider);

      saved.slice().reverse().forEach((row) => {
        addMessage(messages, 'user', row.question);
        addMessage(messages, 'assistant', row.answer, row.created_at);
        turns.push({ role: 'user', content: row.question }, { role: 'assistant', content: row.answer });
      });
      turns = turns.slice(-10);
    }
  } catch (error) {
    status.textContent = `History unavailable: ${error.message}`;
  }
}

window.addEventListener('bcai:languageChanged', () => {
  initAdvisorPage();
});
