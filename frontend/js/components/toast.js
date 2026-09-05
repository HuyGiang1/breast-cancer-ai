export function toast(message, tone = 'info') {
  let host = document.querySelector('#toastHost');
  if (!host) { host = document.createElement('div'); host.id = 'toastHost'; host.className = 'toast-host'; document.body.append(host); }
  const item = document.createElement('div'); item.className = `toast toast-${tone}`; item.textContent = message; host.append(item); setTimeout(() => item.remove(), 4200);
}
