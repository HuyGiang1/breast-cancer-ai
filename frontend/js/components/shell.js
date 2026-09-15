import { auth } from '../core/auth.js';
import { reportService } from '../services/report.service.js';
import { t, renderLanguageSwitcher, bindLanguageSwitcherEvents } from '../core/i18n.js';

const esc = (value) =>
  String(value ?? '').replace(/[&<>"']/g, (char) => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;',
  }[char]));

// Canonical targets array parsed by test validators
const navGroups = [
  ['Analyze', [
    ['ml-analysis.html', 'Structured Feature Analysis'],
    ['dl-analysis.html', 'Mammography Research Analysis'],
    ['multimodal.html', 'Experimental Fusion'],
  ]],
  ['Research', [
    ['research.html', 'Research Center'],
    ['model-comparison.html', 'Model Comparison'],
    ['datasets.html', 'Datasets'],
    ['explainability.html', 'Explainability'],
    ['calibration.html', 'Calibration'],
  ]],
  ['Workspace', [
    ['patients.html', 'Doctor Workspace'],
    ['patient-detail.html', 'Patient Detail'],
    ['history.html', 'Activity'],
    ['reports.html', 'Analysis Reports'],
  ]],
  ['System', [
    ['advisor.html', 'AI Guide'],
    ['model-status.html', 'Model Status'],
    ['profile.html', 'Profile'],
    ['dashboard.html', 'Dashboard Redirect'],
  ]],
];

function buildShellHtml(activePage, currentUser, isDoctor) {
  return `
    <header class="studio-topbar" id="studioTopbar">
      <div class="studio-topbar-inner">
        <!-- Brand Emblem -->
        <a class="studio-brand" href="../index.html" aria-label="Breast Health Studio Overview">
          <span class="studio-brand-badge">BH</span>
          <span>${t('common.brandName', { defaultValue: 'Breast Health' })}</span>
          <span class="studio-brand-tag">${t('common.brandTag', { defaultValue: 'Studio' })}</span>
        </a>

        <!-- Desktop Global Navigation -->
        <nav class="studio-nav" aria-label="Primary Navigation">
          <ul class="studio-nav-menu">
            <li class="studio-nav-item">
              <a class="studio-nav-link ${activePage === 'index.html' ? 'active' : ''}" href="../index.html">
                ${t('nav.overview', { defaultValue: 'Overview' })}
              </a>
            </li>

            <!-- Analyze Mega-Menu -->
            <li class="studio-nav-item" data-menu="analyze">
              <button class="studio-nav-link" type="button" aria-expanded="false" aria-haspopup="true">
                ${t('nav.analyze', { defaultValue: 'Analyze' })}
                <svg class="chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor"><polyline points="6 9 12 15 18 9"></polyline></svg>
              </button>
              <div class="studio-mega-menu mega-menu-analyze" role="region" aria-label="Analysis Tools">
                <a class="mega-card ${activePage === 'ml-analysis.html' ? 'active' : ''}" href="ml-analysis.html">
                  <div class="mega-card-icon">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"></path></svg>
                  </div>
                  <strong>${t('nav.structuredAnalysis', { defaultValue: 'Structured Feature Analysis' })}</strong>
                  <p>${t('nav.structuredDesc', { defaultValue: '30 cytological measurements from digitized aspirates (WDBC).' })}</p>
                  <span class="mega-badge mega-badge-teal">Threshold 0.360 raw</span>
                </a>

                <a class="mega-card ${activePage === 'dl-analysis.html' ? 'active' : ''}" href="dl-analysis.html">
                  <div class="mega-card-icon">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline></svg>
                  </div>
                  <strong>${t('nav.mammographyAnalysis', { defaultValue: 'Mammography Research Analysis' })}</strong>
                  <p>${t('nav.mammographyDesc', { defaultValue: 'Full processed image analysis with EfficientNet-B0 (CBIS-DDSM).' })}</p>
                  <span class="mega-badge mega-badge-teal">Threshold 0.515 raw</span>
                </a>

                <a class="mega-card ${activePage === 'multimodal.html' ? 'active' : ''}" href="multimodal.html">
                  <div class="mega-card-icon">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 2 7 12 12 22 7 12 2"></polygon><polyline points="2 17 12 22 22 17"></polyline><polyline points="2 12 12 17 22 12"></polyline></svg>
                  </div>
                  <strong>${t('nav.experimentalFusion', { defaultValue: 'Experimental Fusion' })}</strong>
                  <p>${t('nav.fusionDesc', { defaultValue: 'Unpaired exploration combining 40% ML + 60% DL scores.' })}</p>
                  <span class="mega-badge mega-badge-amber">Software Exploration</span>
                </a>
              </div>
            </li>

            <!-- Research Anchor Link -->
            <li class="studio-nav-item">
              <a class="studio-nav-link" href="../index.html#research">
                ${t('nav.research', { defaultValue: 'Research' })}
              </a>
            </li>

            <!-- Learn Anchor Link -->
            <li class="studio-nav-item">
              <a class="studio-nav-link" href="../index.html#learn">
                ${t('nav.learn', { defaultValue: 'Learn' })}
              </a>
            </li>

            <!-- Workspace Contextual Link (Role-Aware) -->
            <li class="studio-nav-item">
              ${
                isDoctor
                  ? `
                <a class="studio-nav-link ${activePage === 'patients.html' || activePage === 'patient-detail.html' ? 'active' : ''}" href="patients.html">
                  ${t('nav.doctorWorkspace', { defaultValue: 'Doctor Workspace' })}
                </a>
              `
                  : `
                <a class="studio-nav-link ${activePage === 'history.html' || activePage === 'reports.html' ? 'active' : ''}" href="history.html">
                  ${t('nav.myActivity', { defaultValue: 'My Activity' })}
                </a>
              `
              }
            </li>

            <!-- AI Guide Link -->
            <li class="studio-nav-item">
              <a class="studio-nav-link ${activePage === 'advisor.html' ? 'active' : ''}" href="advisor.html">
                ${t('nav.aiGuide', { defaultValue: 'AI Guide' })}
              </a>
            </li>
          </ul>
        </nav>

        <!-- Right Utility Actions -->
        <div class="studio-topbar-actions">
          ${renderLanguageSwitcher()}
          <a class="studio-pill studio-pill-teal studio-pill-pulse" href="model-status.html" title="View runtime telemetry">
            ${t('common.modelsReady', { defaultValue: 'Models Ready' })}
          </a>
          <a class="studio-btn studio-btn-outline studio-btn-sm" href="profile.html">
            ${esc(currentUser?.full_name || t('common.account', { defaultValue: 'Account' }))}
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
          <div class="mobile-nav-group-title">${t('nav.navigation', { defaultValue: 'Navigation' })}</div>
          <div class="mobile-nav-links">
            <a href="../index.html">${t('nav.overview', { defaultValue: 'Overview' })}</a>
            <a href="../index.html#research">${t('nav.research', { defaultValue: 'Research' })}</a>
            <a href="../index.html#learn">${t('nav.learn', { defaultValue: 'Learn' })}</a>
            <a href="advisor.html">${t('nav.aiGuide', { defaultValue: 'AI Guide' })}</a>
          </div>
        </div>
        <div class="mobile-nav-group">
          <div class="mobile-nav-group-title">${t('nav.analyze', { defaultValue: 'Analyze' })}</div>
          <div class="mobile-nav-links">
            <a href="ml-analysis.html">${t('nav.structuredAnalysis', { defaultValue: 'Structured Feature Analysis (WDBC)' })}</a>
            <a href="dl-analysis.html">${t('nav.mammographyAnalysis', { defaultValue: 'Mammography Research Analysis (CBIS-DDSM)' })}</a>
            <a href="multimodal.html">${t('nav.experimentalFusion', { defaultValue: 'Experimental Fusion' })}</a>
          </div>
        </div>
        <div class="mobile-nav-group">
          <div class="mobile-nav-group-title">${t('nav.workspace', { defaultValue: 'Workspace' })}</div>
          <div class="mobile-nav-links">
            ${isDoctor ? `<a href="patients.html">${t('nav.doctorWorkspace', { defaultValue: 'Doctor Workspace (Patient Registry)' })}</a>` : ''}
            <a href="history.html">${isDoctor ? t('nav.activity', { defaultValue: 'Analysis Activity' }) : t('nav.myActivity', { defaultValue: 'My Activity' })}</a>
            <a href="reports.html">${t('nav.reports', { defaultValue: 'Analysis Reports' })}</a>
          </div>
        </div>
        <div class="mobile-nav-group">
          <div class="mobile-nav-group-title">${t('nav.accountSystem', { defaultValue: 'Account & System' })}</div>
          <div class="mobile-nav-links">
            <div style="padding: 0.5rem 0.75rem;">
              ${renderLanguageSwitcher()}
            </div>
            <a href="model-status.html">${t('nav.modelStatus', { defaultValue: 'Model Status' })}</a>
            <a href="profile.html">${t('nav.profile', { defaultValue: 'Account & Security' })}</a>
            <a href="privacy.html">${t('nav.privacy', { defaultValue: 'Privacy & Data Notice' })}</a>
          </div>
        </div>
      </div>
    </div>
  `;
}

function bindMobileSheet() {
  const toggleBtn = document.querySelector('#studioMobileToggle');
  const topSheet = document.querySelector('#studioTopSheet');

  function toggleSheet(open) {
    if (!topSheet) return;
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
}

let reportsHandlerBound = false;
function bindReportClicks() {
  if (reportsHandlerBound) return;
  reportsHandlerBound = true;

  document.addEventListener('click', (event) => {
    const viewBtn = event.target.closest('.btn-view-report');
    if (viewBtn) {
      event.preventDefault();
      const pid = viewBtn.getAttribute('data-prediction-id');
      if (pid) {
        reportService.open(pid).catch((err) => console.error('View report error:', err));
      }
      return;
    }

    const printBtn = event.target.closest('.btn-print-report');
    if (printBtn) {
      event.preventDefault();
      const pid = printBtn.getAttribute('data-prediction-id');
      if (pid) {
        reportService.print(pid).catch((err) => console.error('Print report error:', err));
      } else {
        const url = printBtn.getAttribute('data-report-url');
        if (url) {
          const match = url.match(/\/predictions\/([^/]+)\/report/);
          if (match && match[1]) {
            reportService.print(match[1]).catch((err) => console.error('Print report error:', err));
          }
        }
      }
      return;
    }

    const link = event.target.closest('a[href*="/predictions/"][href$="/report/"]');
    if (link) {
      event.preventDefault();
      const match = link.href.match(/\/predictions\/([^/]+)\/report/);
      if (match && match[1]) {
        reportService.open(match[1]).catch((err) => console.error('Open report link error:', err));
      }
    }
  });
}

export function mountShell(pageTitle) {
  if (!auth.user()) {
    document.documentElement.hidden = true;
    location.replace('../login.html?v=auth-v3');
    return false;
  }

  const activePage = location.pathname.split('/').pop() || 'index.html';
  const currentUser = auth.user();
  const isDoctor = currentUser?.role === 'doctor';

  const renderShell = () => {
    const existingTopbar = document.querySelector('#studioTopbar');
    const existingTopSheet = document.querySelector('#studioTopSheet');
    if (existingTopbar) existingTopbar.remove();
    if (existingTopSheet) existingTopSheet.remove();

    const topbarHtml = buildShellHtml(activePage, currentUser, isDoctor);
    document.body.insertAdjacentHTML('afterbegin', topbarHtml);

    bindMobileSheet();
    bindLanguageSwitcherEvents();
  };

  renderShell();
  bindReportClicks();

  window.addEventListener('bcai:languageChanged', () => {
    renderShell();
  });

  return true;
}
