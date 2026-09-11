import { requireAuth } from '../core/guards.js';
import { mountShell } from '../components/shell.js';
import { advisorService } from '../services/advisor.service.js';
import { addMessage } from '../components/support.js';

if (requireAuth('../login.html')) {
  mountShell('AI Information Assistant');
  const app = document.querySelector('#app');

  // Check contextual handoff from structured analysis or other pages
  let contextData = null;
  try {
    const raw = sessionStorage.getItem('bcai_advisor_context');
    if (raw) contextData = JSON.parse(raw);
  } catch {}

  let contextBannerHtml = '';
  let dynamicSuggestions = [
    'Explain this model result',
    'What does calibration mean?',
    'What is SHAP?',
    'What is Grad-CAM?',
    'Why are ML and DL not directly comparable?',
    'What are the study limitations?',
    'What does the DL threshold 0.515 mean?',
    'Why is multimodal experimental?',
  ];

  if (contextData) {
    const isFusion = contextData.analysis_type === 'fusion';
    const isDl = contextData.analysis_type === 'dl';
    const pId = contextData.prediction_id ? `#${contextData.prediction_id}` : 'Recent Session';

    if (isFusion) {
      const mlProbStr = (Number(contextData.ml_raw_probability ?? 0) * 100).toFixed(1);
      const dlProbStr = (Number(contextData.dl_raw_probability ?? 0) * 100).toFixed(1);
      const combinedScoreStr = (Number(contextData.combined_malignant_score ?? 0) * 100).toFixed(1);
      const agreeText = contextData.branch_agreement ? 'Branches Agree' : 'Branches Disagree';
      const agreeColor = contextData.branch_agreement ? '#0f766e' : '#b45309';

      contextBannerHtml = `
        <div style="background:#f0fdfa;border:1.5px solid #99f6e4;border-radius:8px;padding:12px 16px;margin-bottom:16px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px;">
          <div>
            <span style="background:#0f766e;color:#fff;font-size:0.75rem;font-weight:700;padding:2px 8px;border-radius:4px;text-transform:uppercase;margin-right:8px;">
              Active Context
            </span>
            <strong style="color:#0f766e;">Discussing Experimental Fusion ${pId}</strong>:
            ML: ${contextData.ml_classification} (${mlProbStr}%), DL: ${contextData.dl_classification} (${dlProbStr}%), Combined: ${combinedScoreStr}%
            <span style="display:inline-block;margin-left:8px;font-size:0.75rem;font-weight:700;color:${agreeColor};">
              (${agreeText})
            </span>
          </div>
          <button id="clearContextBtn" class="v2-button secondary btn-xs" type="button" style="padding:4px 8px;font-size:0.75rem;">
            Clear Context
          </button>
        </div>
      `;

      dynamicSuggestions = [
        'Why can the ML and DL branches produce disagreeing outputs?',
        'Explain how the 40/60 weighted combination was calculated.',
        'Why are WDBC and CBIS-DDSM unpaired datasets?',
        'How should I interpret the 0.50 software decision midpoint?',
        'Explain the Grad-CAM heatmap from the DL branch.',
        'Why can this software combination NOT be used as a clinical diagnosis?',
      ];
    } else {
      const probStr = (Number(contextData.raw_probability) * 100).toFixed(1);
      const contextTitle = isDl ? `Mammography Analysis ${pId}` : `Structured Analysis ${pId}`;
      contextBannerHtml = `
        <div style="background:#f0fdfa;border:1.5px solid #99f6e4;border-radius:8px;padding:12px 16px;margin-bottom:16px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px;">
          <div>
            <span style="background:#0f766e;color:#fff;font-size:0.75rem;font-weight:700;padding:2px 8px;border-radius:4px;text-transform:uppercase;margin-right:8px;">
              Active Context
            </span>
            <strong style="color:#0f766e;">Discussing ${contextTitle}</strong>:
            ${contextData.classification} (${probStr}% raw probability vs threshold ${contextData.threshold})
          </div>
          <button id="clearContextBtn" class="v2-button secondary btn-xs" type="button" style="padding:4px 8px;font-size:0.75rem;">
            Clear Context
          </button>
        </div>
      `;

      if (isDl) {
        dynamicSuggestions = [
          `Explain why the model predicted ${contextData.classification}`,
          `What does the raw probability of ${probStr}% mean relative to threshold ${contextData.threshold}?`,
          'How should the Grad-CAM model-attention heatmap be interpreted?',
          'Why does Grad-CAM not establish tumor localization or boundaries?',
          'What does Platt calibration mean for this mammogram?',
          ...dynamicSuggestions.slice(0, 3),
        ];
      } else {
        dynamicSuggestions = [
          `Explain why the model predicted ${contextData.classification}`,
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
        <span class="eyebrow">Research and educational support</span>
        <h1>AI Information Assistant</h1>
        <p>This assistant provides research information only. It does not diagnose cancer, recommend treatment, replace a clinician, or interpret pathology clinically.</p>
      </header>
      ${contextBannerHtml}
      <div class="support-layout">
        <section class="studio-card chat-panel">
          <div class="chat-toolbar">
            <strong>Conversation</strong>
            <button id="clear" class="v2-button secondary" type="button">New conversation</button>
          </div>
          <div id="messages" class="support-messages" aria-live="polite">
            <p class="v2-empty" id="empty">Ask about this project's methods, model outputs, or limitations.</p>
          </div>
          <p id="status" role="status"></p>
          <form id="composer" class="chat-composer">
            <label for="message">Your research question</label>
            <textarea id="message" class="v2-input" rows="3" required></textarea>
            <button class="v2-button">Send question</button>
          </form>
        </section>
        <aside class="studio-card prompt-panel">
          <h2>Suggested topics</h2>
          <div id="suggestedPromptsList">
            ${dynamicSuggestions.map((q, i) => `
              <button class="suggested-prompt" type="button" data-prompt="${q.replace(/"/g, '&quot;')}">${q}</button>
            `).join('')}
          </div>
        </aside>
      </div>
    </section>
  `;

  const messages = document.querySelector('#messages');
  const status = document.querySelector('#status');
  const form = document.querySelector('#composer');
  const input = document.querySelector('#message');
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
    status.textContent = 'Assistant is responding.';
    form.querySelector('button').disabled = true;

    try {
      // If we have active context, prepend subtle non-clinical system grounding to the question
      let payloadMessage = clean;
      if (contextData && turns.length <= 1) {
        if (contextData.analysis_type === 'dl') {
          payloadMessage = `[Context: Mammography DL Analysis on CBIS-DDSM; Model=EfficientNet-B0; Classification=${contextData.classification}; Raw probability=${(contextData.raw_probability * 100).toFixed(1)}%; Cutoff=${contextData.threshold}; Grad-CAM=${contextData.gradcam_status || 'available'}] ${clean}`;
        } else {
          payloadMessage = `[Context: Structured ML Analysis on WDBC; Classification=${contextData.classification}; Raw probability=${(contextData.raw_probability * 100).toFixed(1)}%; Cutoff=${contextData.threshold}] ${clean}`;
        }
      }

      const result = await advisorService.ask(payloadMessage, turns.slice(-10, -1));
      pending.remove();
      addMessage(messages, 'assistant', result.answer, `${result.provider} · ${result.model}`);
      turns.push({ role: 'assistant', content: result.answer });
      status.textContent = 'Response received.';
    } catch (error) {
      pending.remove();
      addMessage(messages, 'assistant', `Unable to answer: ${error.message}`);
      status.textContent = 'The request could not be completed.';
    } finally {
      form.querySelector('button').disabled = false;
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
    empty.textContent = 'Start a new local conversation. Saved server history is unchanged.';
    messages.append(empty);
    status.textContent = 'Local conversation cleared.';
  });

  try {
    const saved = await advisorService.history();
    saved.slice().reverse().forEach((row) => {
      removeEmpty();
      addMessage(messages, 'user', row.question);
      addMessage(messages, 'assistant', row.answer, row.created_at);
      turns.push({ role: 'user', content: row.question }, { role: 'assistant', content: row.answer });
    });
    turns = turns.slice(-10);
  } catch (error) {
    status.textContent = `History unavailable: ${error.message}`;
  }
}
