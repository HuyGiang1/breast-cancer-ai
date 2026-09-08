// Backward-compatibility redirect for legacy /pages/dashboard.html route
const target = '../index.html' + (location.search || '') + (location.hash || '');
window.location.replace(target);
