/**
 * Breast Health Intelligence Studio — Landing Experience Controller
 * Handles top navigation, mega-menus, mobile top-sheet, and interactive prototype preview.
 */

document.addEventListener('DOMContentLoaded', () => {
  initNavigation();
  initInteractivePreview();
});

/**
 * Top Navigation & Mobile Top-Sheet Controller
 */
function initNavigation() {
  const mobileToggle = document.getElementById('mobileToggle');
  const topSheet = document.getElementById('mobileTopSheet');
  const topSheetClose = document.getElementById('topSheetClose');
  const navLinks = document.querySelectorAll('.studio-top-sheet a, .studio-nav-link');

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

  // Close sheet on backdrop click (click outside content container)
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
  const calibProbValue = document.getElementById('calibProbValue');
  const calibProbFill = document.getElementById('calibProbFill');
  const statusPill = document.getElementById('previewStatusPill');

  if (!sampleA_Btn || !sampleB_Btn) return;

  const sampleData = {
    A: {
      tag: 'Study A · Case #W-1042',
      model: 'Logistic Regression (30 FNA Features)',
      cutoff: 'Raw Cutoff ≥ 0.360',
      modality: 'Fine Needle Aspirate (FNA) Nuclear Morphometry',
      raw: 0.884,
      calib: 0.912,
      decision: 'Malignant Suspicion (Above 0.360 Research Cutoff)',
      badgeClass: 'badge-danger'
    },
    B: {
      tag: 'Study B · Case #DDSM-4109',
      model: 'EfficientNet-B0 (Single View Mammography)',
      cutoff: 'Raw Cutoff ≥ 0.515',
      modality: 'Full-Field Digital Mammography ROI (512×512)',
      raw: 0.284,
      calib: 0.315,
      decision: 'Benign Pattern (Below 0.515 Research Cutoff)',
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

    if (calibProbValue) calibProbValue.textContent = (data.calib * 100).toFixed(1) + '%';
    if (calibProbFill) calibProbFill.style.width = (data.calib * 100).toFixed(1) + '%';

    if (statusPill) {
      statusPill.textContent = data.decision;
      statusPill.className = `studio-badge ${data.badgeClass}`;
    }
  };

  sampleA_Btn.addEventListener('click', () => updateDisplay('A'));
  sampleB_Btn.addEventListener('click', () => updateDisplay('B'));
}
