/**
 * Breast Health Intelligence Studio — Landing & Canonical Overview Controller
 *
 * Phase 4R Batch A:
 * - Session-aware Overview (guest vs authenticated user vs doctor)
 * - Authenticated Quick Start bar
 * - Canonical navigation with smooth anchor scrolling (#research, #learn)
 * - Interactive telemetry preview (Study A WDBC vs Study B CBIS-DDSM)
 * - Lazy-loading clinical video player
 */

import { auth } from '../core/auth.js';
import { t, renderLanguageSwitcher, bindLanguageSwitcherEvents, applyDomTranslations } from '../core/i18n.js';

document.addEventListener('DOMContentLoaded', () => {
  initLanguageSwitchers();
  initNavigation();
  initAuthSession();
  initInteractivePreview();
  initLazyVideos();
  initSmoothAnchors();
});

window.addEventListener('bcai:languageChanged', () => {
  initLanguageSwitchers();
  initAuthSession();
});

function initLanguageSwitchers() {
  const topSlot = document.getElementById('topbarLangSlot');
  const mobSlot = document.getElementById('mobileLangSlot');
  if (topSlot) {
    topSlot.innerHTML = renderLanguageSwitcher();
    bindLanguageSwitcherEvents(topSlot);
  }
  if (mobSlot) {
    mobSlot.innerHTML = renderLanguageSwitcher();
    bindLanguageSwitcherEvents(mobSlot);
  }
  applyDomTranslations(document.body);
}

/**
 * Top Navigation & Mobile Top-Sheet Controller
 */
function initNavigation() {
  const mobileToggle = document.getElementById('mobileToggle');
  const topSheet = document.getElementById('mobileTopSheet');
  const topSheetClose = document.getElementById('topSheetClose');

  if (!mobileToggle || !topSheet) return;

  const openSheet = () => {
    topSheet.classList.add('is-open');
    mobileToggle.setAttribute('aria-expanded', 'true');
    mobileToggle.setAttribute('aria-label', 'Close navigation menu');
    document.body.style.overflow = 'hidden';
    const firstFocusable = topSheet.querySelector('a, button');
    firstFocusable?.focus();
  };

  const closeSheet = () => {
    topSheet.classList.remove('is-open');
    mobileToggle.setAttribute('aria-expanded', 'false');
    mobileToggle.setAttribute('aria-label', 'Open navigation menu');
    document.body.style.overflow = '';
  };

  mobileToggle.addEventListener('click', () => {
    const isOpen = topSheet.classList.contains('is-open');
    if (isOpen) {
      closeSheet();
    } else {
      openSheet();
    }
  });

  if (topSheetClose) {
    topSheetClose.addEventListener('click', () => {
      closeSheet();
      mobileToggle.focus();
    });
  }

  // Close sheet on backdrop click
  topSheet.addEventListener('click', (e) => {
    if (e.target === topSheet) {
      closeSheet();
      mobileToggle.focus();
    }
  });

  // Close on link click inside top sheet
  topSheet.querySelectorAll('a').forEach(link => {
    link.addEventListener('click', () => {
      closeSheet();
    });
  });

  // Escape key closes modal/top-sheet
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && topSheet.classList.contains('is-open')) {
      closeSheet();
      mobileToggle.focus();
    }
  });

  // Mega menu keyboard accessibility
  const navItems = document.querySelectorAll('.studio-nav-item');
  navItems.forEach(item => {
    const trigger = item.querySelector('.studio-nav-link');
    const menu = item.querySelector('.studio-mega-menu, .studio-dropdown');
    if (!trigger || !menu) return;

    trigger.addEventListener('keydown', (e) => {
      if (e.key === 'ArrowDown' || e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        menu.classList.add('is-open');
        const firstLink = menu.querySelector('a');
        firstLink?.focus();
      }
    });

    item.addEventListener('mouseleave', () => {
      menu.classList.remove('is-open');
    });

    menu.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        menu.classList.remove('is-open');
        trigger.focus();
      }
    });
  });
}

/**
 * Session State & Authenticated Overview Adaptation
 */
function initAuthSession() {
  const user = auth.user();
  const authQuickStart = document.getElementById('authQuickStart');
  const headerAuthActions = document.getElementById('headerAuthActions');
  const topbarWorkspaceSlot = document.getElementById('topbarWorkspaceSlot');
  const mobileWorkspaceSlot = document.getElementById('mobileWorkspaceSlot');
  const mobileAccountSlot = document.getElementById('mobileAccountSlot');
  const heroSecondaryCta = document.getElementById('heroSecondaryCta');
  const quickStartGreeting = document.getElementById('quickStartGreeting');
  const quickStartRoleBadge = document.getElementById('quickStartRoleBadge');
  const quickStartDoctorCard = document.getElementById('quickStartDoctorCard');
  const quickStartSignOutBtn = document.getElementById('quickStartSignOutBtn');

  const esc = value => String(value ?? '').replace(/[&<>"']/g, char => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[char]));

  if (user) {
    // Authenticated User
    const isDoctor = user.role === 'doctor';
    const displayName = user.full_name || user.email.split('@')[0];

    // Show Quick Start section
    if (authQuickStart) {
      authQuickStart.style.display = 'block';
    }
    if (quickStartGreeting) {
      quickStartGreeting.textContent = `${t('common.welcome', 'Welcome')}, ${displayName}`;
    }
    if (quickStartRoleBadge) {
      quickStartRoleBadge.textContent = isDoctor ? `👨‍⚕️ ${t('nav.doctorWorkspace', 'Doctor Workspace')}` : `👤 ${t('nav.myActivity', 'Personal Account')}`;
    }
    if (quickStartDoctorCard) {
      quickStartDoctorCard.style.display = isDoctor ? 'flex' : 'none';
    }

    // Topbar header auth identity
    if (headerAuthActions) {
      headerAuthActions.innerHTML = `
        <span style="font-size: 0.8125rem; font-weight: 600; color: var(--slate-700); margin-right: 0.25rem;">
          ${t('common.welcome', 'Welcome')}, ${esc(displayName)}
        </span>
        <a class="studio-btn studio-btn-outline studio-btn-sm" href="pages/profile.html">${t('common.profile', 'Account')}</a>
        <button class="studio-btn studio-btn-ghost studio-btn-sm" id="topbarSignOutBtn" type="button">${t('common.logout', 'Sign Out')}</button>
      `;
      document.getElementById('topbarSignOutBtn')?.addEventListener('click', () => {
        auth.clear();
        location.reload();
      });
    }

    // Topbar workspace slot
    if (topbarWorkspaceSlot) {
      topbarWorkspaceSlot.innerHTML = isDoctor
        ? `<a class="studio-nav-link" href="pages/patients.html">${t('nav.doctorWorkspace', 'Doctor Workspace')}</a>`
        : `<a class="studio-nav-link" href="pages/history.html">${t('nav.myActivity', 'My Activity')}</a>`;
    }

    // Mobile sheet slots
    if (mobileWorkspaceSlot) {
      mobileWorkspaceSlot.innerHTML = `
        <div class="mobile-nav-group">
          <div class="mobile-nav-group-title">${isDoctor ? t('nav.doctorWorkspace', 'Doctor Workspace') : t('nav.myActivity', 'My Activity')}</div>
          <div class="mobile-nav-links">
            ${isDoctor ? `<a href="pages/patients.html">${t('patients.title', 'Doctor Workspace')} (${t('patients.registryHero', 'Patient Registry')})</a>` : ''}
            <a href="pages/history.html">${isDoctor ? t('history.doctorTitle', 'Analysis Activity') : t('history.title', 'My Activity')}</a>
            <a href="pages/reports.html">${t('reports.title', 'Analysis Reports')}</a>
          </div>
        </div>
      `;
    }

    if (mobileAccountSlot) {
      mobileAccountSlot.innerHTML = `
        <div class="mobile-nav-group">
          <div class="mobile-nav-group-title">${t('common.profile', 'Account')} (${esc(displayName)})</div>
          <div class="mobile-nav-links">
            <a href="pages/profile.html">${t('profile.title', 'Account & Security')}</a>
            <a href="javascript:void(0)" id="mobileSignOutLink" style="color: var(--danger, #ef4444);">${t('common.logout', 'Sign Out')}</a>
          </div>
        </div>
      `;
      document.getElementById('mobileSignOutLink')?.addEventListener('click', () => {
        auth.clear();
        location.reload();
      });
    }

    // Hero secondary CTA
    if (heroSecondaryCta) {
      heroSecondaryCta.textContent = isDoctor ? `${t('nav.doctorWorkspace', 'Doctor Workspace')} →` : `${t('nav.analyze', 'Continue Analysis')} →`;
      heroSecondaryCta.href = isDoctor ? 'pages/patients.html' : 'pages/ml-analysis.html';
    }

    // Quick start sign-out
    if (quickStartSignOutBtn) {
      quickStartSignOutBtn.addEventListener('click', () => {
        auth.clear();
        location.reload();
      });
    }

  } else {
    // Guest (Logged out)
    if (authQuickStart) {
      authQuickStart.style.display = 'none';
    }
    if (topbarWorkspaceSlot) {
      topbarWorkspaceSlot.innerHTML = '';
    }
    if (mobileWorkspaceSlot) {
      mobileWorkspaceSlot.innerHTML = '';
    }
    if (mobileAccountSlot) {
      mobileAccountSlot.innerHTML = `
        <div class="mobile-nav-group">
          <div class="mobile-nav-group-title">${t('common.profile', 'Account')}</div>
          <div class="mobile-nav-links">
            <a href="login.html?v=auth-v3">${t('nav.signIn', 'Sign In')}</a>
            <a href="register.html?v=auth-v3">${t('nav.createAccount', 'Create Account')}</a>
          </div>
        </div>
      `;
    }
  }
}

/**
 * Smooth Anchor Scrolling for #research and #learn Hub
 */
function initSmoothAnchors() {
  document.querySelectorAll('a[href^="#"]').forEach(link => {
    link.addEventListener('click', (e) => {
      const hash = link.getAttribute('href');
      if (hash === '#' || hash === '') return;
      const target = document.querySelector(hash);
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth' });
        history.pushState(null, '', hash);
      }
    });
  });

  // Handle direct URL with hash on page load
  if (location.hash) {
    setTimeout(() => {
      const target = document.querySelector(location.hash);
      if (target) {
        target.scrollIntoView({ behavior: 'smooth' });
      }
    }, 150);
  }
}

/**
 * Interactive Analysis Experience Preview (Beat 04)
 * Allows exploring Study A (WDBC FNA) vs Study B (CBIS-DDSM Mammography) sample profiles.
 */
function initInteractivePreview() {
  const sampleA_Btn = document.getElementById('sampleA_Btn');
  const sampleB_Btn = document.getElementById('sampleB_Btn');
  const previewSampleTag = document.getElementById('previewSampleTag');
  const previewModelTag = document.getElementById('previewModelTag');
  const previewCutoffTag = document.getElementById('previewCutoffTag');
  const previewModalityText = document.getElementById('previewModalityText');
  const rawProbValue = document.getElementById('rawProbValue');
  const rawProbFill = document.getElementById('rawProbFill');
  const rawMarginTag = document.getElementById('rawMarginTag');
  const panelA = document.getElementById('telemetryStudyAPanel');
  const panelB = document.getElementById('telemetryStudyBPanel');
  const calibProbValue = document.getElementById('calibProbValue');
  const calibProbFill = document.getElementById('calibProbFill');
  const calibReliabilityPill = document.getElementById('calibReliabilityPill');
  const statusPill = document.getElementById('previewStatusPill');

  if (!sampleA_Btn || !sampleB_Btn) return;

  const sampleData = {
    A: {
      tag: 'Interactive demonstration sample (WDBC Cytology)',
      model: 'Logistic Regression (30 FNA Features)',
      cutoff: 'Frozen research decision threshold: ≥ 0.360',
      modality: 'Fine Needle Aspirate (FNA) 30 Nuclear Morphometry Features',
      raw: 0.884,
      margin: '+52.4% above cutoff',
      marginClass: 'margin-pill-pos',
      calib: null,
      decision: 'Malignant Prediction (Raw probability 0.884 ≥ 0.360 threshold)',
      badgeClass: 'badge-danger'
    },
    B: {
      tag: 'Interactive demonstration sample (CBIS-DDSM Mammography)',
      model: 'EfficientNet-B0 (Full Processed Image)',
      cutoff: 'Frozen research decision threshold: ≥ 0.515',
      modality: 'CBIS-DDSM Mammography Full Processed Image (224×224×3 RGB input)',
      raw: 0.284,
      margin: '-23.1% below cutoff',
      marginClass: 'margin-pill-neg',
      calib: 0.315,
      reliability: 'Interpretation Reliability: High',
      decision: 'Benign Prediction (Raw probability 0.284 < 0.515 threshold)',
      badgeClass: 'badge-success'
    }
  };

  const updateDisplay = (key) => {
    const data = sampleData[key];
    if (!data) return;

    if (sampleA_Btn && sampleB_Btn) {
      sampleA_Btn.classList.toggle('active', key === 'A');
      sampleB_Btn.classList.toggle('active', key === 'B');
    }

    if (previewSampleTag) previewSampleTag.textContent = data.tag;
    if (previewModelTag) previewModelTag.textContent = data.model;
    if (previewCutoffTag) previewCutoffTag.textContent = data.cutoff;
    if (previewModalityText) previewModalityText.textContent = data.modality;

    if (rawProbValue) rawProbValue.textContent = (data.raw * 100).toFixed(1) + '%';
    if (rawProbFill) rawProbFill.style.width = (data.raw * 100).toFixed(1) + '%';
    if (rawMarginTag) {
      rawMarginTag.textContent = data.margin;
      rawMarginTag.className = `telemetry-margin-pill ${data.marginClass}`;
    }

    if (panelA && panelB) {
      panelA.style.display = key === 'A' ? 'flex' : 'none';
      panelB.style.display = key === 'B' ? 'flex' : 'none';
    }

    if (key === 'B') {
      if (calibProbValue) calibProbValue.textContent = (data.calib * 100).toFixed(1) + '%';
      if (calibProbFill) calibProbFill.style.width = (data.calib * 100).toFixed(1) + '%';
      if (calibReliabilityPill) calibReliabilityPill.textContent = data.reliability;
    }

    if (statusPill) {
      statusPill.textContent = data.decision;
      statusPill.className = `studio-badge ${data.badgeClass}`;
    }
  };

  sampleA_Btn.addEventListener('click', () => updateDisplay('A'));
  sampleB_Btn.addEventListener('click', () => updateDisplay('B'));
}

/**
 * Lazy Video Player Controller
 * Avoids loading third-party iframes on initial page load.
 * Instantiates privacy-enhanced YouTube embed upon user activation.
 */
function initLazyVideos() {
  const stages = document.querySelectorAll('.video-poster-stage[data-videoid]');
  stages.forEach(stage => {
    stage.addEventListener('click', () => {
      const videoId = stage.dataset.videoid;
      const title = stage.dataset.title || 'Educational Video';
      stage.style.cursor = 'default';
      stage.innerHTML = `
        <iframe
          src="https://www.youtube-nocookie.com/embed/${videoId}?autoplay=1&rel=0"
          title="${title.replace(/"/g, '&quot;')}"
          width="100%"
          height="100%"
          style="border: 0; position: absolute; inset: 0; width: 100%; height: 100%;"
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
          referrerpolicy="strict-origin-when-cross-origin"
          allowfullscreen>
        </iframe>
      `;
    }, { once: true });
  });
}
