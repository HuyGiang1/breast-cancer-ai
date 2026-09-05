import { requireAuth } from '../core/guards.js';
import { mountShell } from '../components/shell.js';
import { authService } from '../services/auth.service.js';
import { auth } from '../core/auth.js';

if (requireAuth('../login.html')) {
  mountShell('Profile');
  const app=document.querySelector('#app');
  app.innerHTML='<section class="research-main"><header class="research-hero"><span class="eyebrow">Authenticated account</span><h1>Your profile</h1><p>Account identity and security for this research prototype.</p></header><div id="profile" class="profile-grid"><section class="v2-card">Loading profile...</section></div></section>';
  const root=document.querySelector('#profile');
  try {
    const user=await authService.me();
    root.innerHTML=`<section class="v2-card"><h2>Account</h2><form id="account"><label class="v2-field">Full name<input class="v2-input" name="full_name" required></label><label class="v2-field">Email<input class="v2-input" type="email" readonly></label><p id="accountStatus" role="status"></p><button class="v2-button">Save name</button></form></section><section class="v2-card"><h2>Role / access</h2><dl><div><dt>Role</dt><dd id="role"></dd></div></dl><p>The backend remains the authority for all permissions.</p></section><section class="v2-card"><h2>Security</h2><form id="password"><label class="v2-field">Current password<input class="v2-input" name="current_password" type="password" autocomplete="current-password" required></label><label class="v2-field">New password<input class="v2-input" name="new_password" type="password" minlength="8" autocomplete="new-password" required></label><p id="passwordStatus" role="status"></p><button class="v2-button">Change password</button></form></section><section class="v2-card"><h2>Research prototype</h2><p>This account provides access to research and educational workflows. It does not enable clinical diagnosis.</p><button id="logout" class="v2-button secondary" type="button">Sign out</button></section>`;
    const account=document.querySelector('#account'); account.full_name.value=user.full_name||''; account.querySelector('input[type=email]').value=user.email||''; document.querySelector('#role').textContent=user.role||'user';
    account.addEventListener('submit',async event=>{event.preventDefault();const status=document.querySelector('#accountStatus');try{const updated=await authService.updateProfile({full_name:account.full_name.value});auth.save({access_token:auth.token(),user:updated});status.textContent='Profile name updated.';}catch(error){status.textContent=error.message;}});
    const password=document.querySelector('#password'); password.addEventListener('submit',async event=>{event.preventDefault();const status=document.querySelector('#passwordStatus');try{const result=await authService.changePassword(Object.fromEntries(new FormData(password)));status.textContent=result.message;password.reset();}catch(error){status.textContent=error.message;}});
    document.querySelector('#logout').addEventListener('click',async()=>{await authService.logout();location.assign('../login.html');});
  } catch(error){root.innerHTML='<section class="v2-card"><h2>Profile unavailable</h2><p></p></section>';root.querySelector('p').textContent=error.message;}
}
