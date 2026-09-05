export function setActiveNavigation() { document.querySelectorAll('[data-nav]').forEach(link => link.classList.toggle('active', link.getAttribute('href') === location.pathname.split('/').pop())); }
export function toggleMobileNavigation() { document.querySelector('.v2-sidebar')?.classList.toggle('open'); }
