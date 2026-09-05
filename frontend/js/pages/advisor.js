import { requireAuth } from '../core/guards.js';
import { mountShell } from '../components/shell.js';
import { advisorService } from '../services/advisor.service.js';
import { addMessage } from '../components/support.js';

if (requireAuth('../login.html')) {
  mountShell('AI Information Assistant');
  const app = document.querySelector('#app');
  const suggestions = ['Explain this model result','What does calibration mean?','What is SHAP?','What is Grad-CAM?','Why are ML and DL not directly comparable?','What are the study limitations?','What does the DL threshold 0.515 mean?','Why is multimodal experimental?'];
  app.innerHTML = `<section class="research-main"><header class="research-hero"><span class="eyebrow">Research and educational support</span><h1>AI Information Assistant</h1><p>This assistant provides research information only. It does not diagnose cancer, recommend treatment, replace a clinician, or interpret pathology clinically.</p></header><div class="support-layout"><section class="v2-card chat-panel"><div class="chat-toolbar"><strong>Conversation</strong><button id="clear" class="v2-button secondary" type="button">New conversation</button></div><div id="messages" class="support-messages" aria-live="polite"><p class="v2-empty" id="empty">Ask about this project's methods, model outputs, or limitations.</p></div><p id="status" role="status"></p><form id="composer" class="chat-composer"><label for="message">Your research question</label><textarea id="message" class="v2-input" rows="3" required></textarea><button class="v2-button">Send question</button></form></section><aside class="v2-card prompt-panel"><h2>Suggested topics</h2><div>${suggestions.map((q,i)=>`<button class="suggested-prompt" type="button" data-index="${i}">${q}</button>`).join('')}</div></aside></div></section>`;
  const messages=document.querySelector('#messages'),status=document.querySelector('#status'),form=document.querySelector('#composer'),input=document.querySelector('#message');
  let turns=[];
  const removeEmpty=()=>document.querySelector('#empty')?.remove();
  try { const saved=await advisorService.history(); saved.slice().reverse().forEach(row=>{removeEmpty();addMessage(messages,'user',row.question);addMessage(messages,'assistant',row.answer,row.created_at);turns.push({role:'user',content:row.question},{role:'assistant',content:row.answer})}); turns=turns.slice(-10); }
  catch (error) { status.textContent=`History unavailable: ${error.message}`; }
  async function send(message) {
    const clean=message.trim(); if(!clean)return;
    removeEmpty(); addMessage(messages,'user',clean); turns.push({role:'user',content:clean}); input.value='';
    const pending=addMessage(messages,'assistant','Preparing a research response...'); status.textContent='Assistant is responding.'; form.querySelector('button').disabled=true;
    try { const result=await advisorService.ask(clean,turns.slice(-10,-1)); pending.remove(); addMessage(messages,'assistant',result.answer,`${result.provider} · ${result.model}`); turns.push({role:'assistant',content:result.answer}); status.textContent='Response received.'; }
    catch(error){ pending.remove(); addMessage(messages,'assistant',`Unable to answer: ${error.message}`); status.textContent='The request could not be completed.'; }
    finally { form.querySelector('button').disabled=false; input.focus(); }
  }
  form.addEventListener('submit',event=>{event.preventDefault();send(input.value)});
  input.addEventListener('keydown',event=>{if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();form.requestSubmit();}});
  document.querySelectorAll('[data-index]').forEach(button=>button.addEventListener('click',()=>send(suggestions[Number(button.dataset.index)])));
  document.querySelector('#clear').addEventListener('click',()=>{turns=[];messages.replaceChildren();const empty=document.createElement('p');empty.id='empty';empty.className='v2-empty';empty.textContent='Start a new local conversation. Saved server history is unchanged.';messages.append(empty);status.textContent='Local conversation cleared.';});
}
