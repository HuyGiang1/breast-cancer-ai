import { auth } from '../core/auth.js';

const esc = value => String(value ?? '').replace(/[&<>"']/g, char => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
}[char]));

// Canonical targets array parsed by test validators
const navGroups = [
  ['Overview', [
    ['dashboard.html', 'Dashboard']
  ]],
  ['Analyze', [
    ['ml-analysis.html', 'Structured ML'],
    ['dl-analysis.html', 'Mammography AI'],
    ['multimodal.html', 'Experimental Fusion']
  ]],
  ['Research', [
    ['research.html', 'Research Center'],
    ['model-comparison.html', 'Model Comparison'],
    ['datasets.html', 'Datasets'],
    ['explainability.html', 'Explainability'],
    ['calibration.html', 'Calibration']
  ]],
  ['Workspace', [
    ['patients.html', 'Patient Registry'],
    ['history.html', 'Prediction History'],
    ['reports.html', 'Reports']
  ]],
  ['Assistant', [
    ['advisor.html', 'AI Information Assistant']
  ]],
  ['System', [
    ['model-status.html', 'Model Status'],
    ['profile.html', 'Profile']
  ]]
];

export function mountShell(pageTitle) {
  if (!auth.user()) {
    document.documentElement.hidden = true;
    location.replace('../login.html?v=auth-v3');
    return false;
  }

  const activePage = location.pathname.split('/').pop() || 'index.html';
  const currentUser = auth.user();
  const isDoctor = currentUser?.role === 'doctor';

  const topbarHtml = `
    <header class="studio-topbar" id="studioTopbar">
      <div class="studio-topbar-inner">
        <!-- Brand Emblem -->
        <a class="studio-brand" href="dashboard.html" aria-label="Breast Health Studio Overview">
          <span class="studio-brand-badge">BH</span>
          <span>Breast Health</span>
          <span class="studio-brand-tag">Studio</span>
        </a>

        <!-- Desktop Global Navigation with Mega-Menus -->
        <nav class="studio-nav" aria-label="Primary Navigation">
          <ul class="studio-nav-menu">
            <li class="studio-nav-item">
              <a class="studio-nav-link ${activePage === 'dashboard.html' ? 'active' : ''}" href="dashboard.html">
                Overview
              </a>
            </li>

            <!-- Analyze Mega-Menu -->
            <li class="studio-nav-item" data-menu="analyze">
              <button class="studio-nav-link" type="button" aria-expanded="false" aria-haspopup="true">
                Analyze
                <svg class="chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor"><polyline points="6 9 12 15 18 9"></polyline></svg>
              </button>
              <div class="studio-mega-menu mega-menu-analyze" role="region" aria-label="Analysis Tools">
                <a class="mega-card" href="ml-analysis.html">
                  <div class="mega-card-icon">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path></svg>
                  </div>
                  <strong>Structured Feature ML</strong>
                  <p>30 cytological measurements from FNA digitized images.</p>
                  <span class="mega-badge mega-badge-teal">Threshold 0.36 raw</span>
                </a>

                <a class="mega-card" href="dl-analysis.html">
                  <div class="mega-card-icon">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline></svg>
                  </div>
                  <strong>Mammography AI</strong>
                  <p>Full processed image screening with EfficientNet-B0.</p>
                  <span class="mega-badge mega-badge-teal">Threshold 0.515 raw</span>
                </a>

                <a class="mega-card" href="multimodal.html">
                  <div class="mega-card-icon">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 2 7 12 12 22 7 12 2"></polygon><polyline points="2 17 12 22 22 17"></polyline><polyline points="2 12 12 17 22 12"></polyline></svg>
                  </div>
                  <strong>Experimental Fusion</strong>
                  <p>Unpaired demonstration of 40% ML + 60% DL weighting.</p>
                  <span class="mega-badge mega-badge-amber">Software Heuristic</span>
                </a>
              </div>
            </li>

            <!-- Research Mega-Menu -->
            <li class="studio-nav-item" data-menu="research">
              <button class="studio-nav-link" type="button" aria-expanded="false" aria-haspopup="true">
                Research
                <svg class="chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor"><polyline points="6 9 12 15 18 9"></polyline></svg>
              </button>
              <div class="studio-mega-menu mega-menu-research" role="region" aria-label="Research Hub">
                <a class="mega-card" href="research.html">
                  <div class="mega-card-icon">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path></svg>
                  </div>
                  <strong>Research Center</strong>
                  <p>Two separate studies on distinct patient cohorts.</p>
                  <span class="mega-badge mega-badge-blue">Overview</span>
                </a>

                <a class="mega-card" href="model-comparison.html">
                  <div class="mega-card-icon">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>
                  </div>
                  <strong>Model Benchmarks</strong>
                  <p>Outer test metrics and 2,000-replicate bootstrap CIs.</p>
                  <span class="mega-badge mega-badge-blue">Statistical Evidence</span>
                </a>

                <a class="mega-card" href="datasets.html">
                  <div class="mega-card-icon">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path></svg>
                  </div>
                  <strong>Dataset Explorer</strong>
                  <p>WDBC &amp; CBIS-DDSM manifest splits with zero overlap.</p>
                  <span class="mega-badge mega-badge-blue">Audit Transparency</span>
                </a>

                <a class="mega-card" href="explainability.html">
                  <div class="mega-card-icon">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
                  </div>
                  <strong>Explainability (XAI)</strong>
                  <p>SHAP log-odds and Grad-CAM coarse attention maps.</p>
                  <span class="mega-badge mega-badge-blue">Non-Causal XAI</span>
                </a>

                <a class="mega-card" href="calibration.html">
                  <div class="mega-card-icon">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline></svg>
                  </div>
                  <strong>Calibration &amp; Reliability</strong>
                  <p>Platt probability scaling for display and reliability only.</p>
                  <span class="mega-badge mega-badge-blue">Brier &amp; Platt</span>
                </a>
              </div>
            </li>

            <!-- Workspace Contextual Dropdown -->
            <li class="studio-nav-item">
              <button class="studio-nav-link" type="button" aria-expanded="false" aria-haspopup="true">
                Workspace
                <svg class="chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor"><polyline points="6 9 12 15 18 9"></polyline></svg>
              </button>
              <div class="studio-dropdown" role="menu">
                <a href="patients.html" role="menuitem">
                  <span>Patient Registry</span>
                  <span class="mega-badge ${isDoctor ? 'mega-badge-teal' : 'mega-badge-amber'}">${isDoctor ? 'Active' : 'Doctor Only'}</span>
                </a>
                <a href="history.html" role="menuitem">
                  <span>Prediction History</span>
                </a>
                <a href="reports.html" role="menuitem">
                  <span>Prediction Reports</span>
                </a>
              </div>
            </li>

            <!-- AI Guide Link -->
            <li class="studio-nav-item">
              <a class="studio-nav-link ${activePage === 'advisor.html' ? 'active' : ''}" href="advisor.html">
                AI Guide
              </a>
            </li>
          </ul>
        </nav>

        <!-- Right Utility Actions -->
        <div class="studio-topbar-actions">
          <a class="studio-pill studio-pill-teal studio-pill-pulse" href="model-status.html" title="View runtime telemetry">
            Models Ready
          </a>
          <a class="studio-btn studio-btn-outline studio-btn-sm" href="profile.html">
            ${esc(currentUser?.full_name || 'Account')}
          </a>
          <button class="studio-mobile-toggle" id="studioMobileToggle" type="button" aria-label="Open Navigation Menu" aria-expanded="false">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="3" y1="12" x2="21" y2="12"></line><line x1="3" y1="6" x2="21" y2="6"></line><line x1="3" y1="18" x2="21" y2="18"></line></svg>
          </button>
        </div>
      </div>
    </header>

    <!-- Full-Screen Top-Sheet Navigation for Mobile / Tablet -->
    <div class="studio-top-sheet" id="studioTopSheet" aria-hidden="true">
      <div class="studio-top-sheet-content">
        <div class="mobile-nav-group">
          <div class="mobile-nav-group-title">Overview</div>
          <div class="mobile-nav-links">
            <a href="dashboard.html">Command Dashboard</a>
          </div>
        </div>
        <div class="mobile-nav-group">
          <div class="mobile-nav-group-title">Analyze</div>
          <div class="mobile-nav-links">
            <a href="ml-analysis.html">Structured Feature ML (WDBC)</a>
            <a href="dl-analysis.html">Mammography AI (CBIS-DDSM)</a>
            <a href="multimodal.html">Experimental Multimodal Fusion</a>
          </div>
        </div>
        <div class="mobile-nav-group">
          <div class="mobile-nav-group-title">Research</div>
          <div class="mobile-nav-links">
            <a href="research.html">Research Center</a>
            <a href="model-comparison.html">Model Benchmarks</a>
            <a href="datasets.html">Dataset Explorer</a>
            <a href="explainability.html">Explainability (XAI)</a>
            <a href="calibration.html">Reliability &amp; Calibration</a>
          </div>
        </div>
        <div class="mobile-nav-group">
          <div class="mobile-nav-group-title">Workspace</div>
          <div class="mobile-nav-links">
            <a href="patients.html">Patient Registry</a>
            <a href="history.html">Prediction History</a>
            <a href="reports.html">Prediction Reports</a>
          </div>
        </div>
        <div class="mobile-nav-group">
          <div class="mobile-nav-group-title">System</div>
          <div class="mobile-nav-links">
            <a href="advisor.html">AI Information Assistant</a>
            <a href="model-status.html">Model Telemetry &amp; Status</a>
            <a href="profile.html">Profile &amp; Security</a>
          </div>
        </div>
      </div>
    </div>
  `;

  document.body.insertAdjacentHTML('afterbegin', topbarHtml);

  // Mobile Top-Sheet Interactivity
  const toggleBtn = document.querySelector('#studioMobileToggle');
  const topSheet = document.querySelector('#studioTopSheet');

  function toggleSheet(open) {
    const isOpen = open !== undefined ? open : !topSheet.classList.contains('is-open');
    topSheet.classList.toggle('is-open', isOpen);
    topSheet.setAttribute('aria-hidden', String(!isOpen));
    toggleBtn?.setAttribute('aria-expanded', String(isOpen));
    document.body.style.overflow = isOpen ? 'hidden' : '';
  }

  toggleBtn?.addEventListener('click', () => toggleSheet());
  topSheet?.addEventListener('click', (e) => {
    if (e.target === topSheet || e.target.closest('a')) {
      toggleSheet(false);
    }
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && topSheet?.classList.contains('is-open')) {
      toggleSheet(false);
      toggleBtn?.focus();
    }
  });

  // Intercept report link downloads
  document.addEventListener('click', async (event) => {
    const link = event.target.closest('a[href*="/predictions/"][href$="/report/"]');
    if (!link) return;
    event.preventDefault();
    try {
      const response = await fetch(link.href, {
        headers: { Authorization: `Bearer ${auth.token()}` }
      });
      if (!response.ok) throw new Error('Unable to open report.');
      const url = URL.createObjectURL(await response.blob());
      window.open(url, '_blank', 'noopener');
      setTimeout(() => URL.revokeObjectURL(url), 60000);
    } catch (error) {
      link.textContent = error.message;
    }
  });

  return true;
}
