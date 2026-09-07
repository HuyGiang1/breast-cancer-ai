/**
 * Breast Health Intelligence Studio — Landing Experience Controller
 * Handles top navigation, mega-menus, mobile top-sheet, and interactive prototype preview.
 */

document.addEventListener('DOMContentLoaded', () => {
  initNavigation();
  initInteractivePreview();
  initLazyVideo();
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
 * Lazy Video Player Controller (Beat 09)
 * Avoids loading third-party iframes on initial load.
 * Instantiates privacy-enhanced YouTube embed upon explicit user activation.
 */
function initLazyVideo() {
  const videoContainer = document.getElementById('videoContainer');
  if (!videoContainer) return;

  videoContainer.addEventListener('click', () => {
    videoContainer.style.cursor = 'default';
    videoContainer.innerHTML = `
      <iframe
        src="https://www.youtube-nocookie.com/embed/50CdcLJsIEI?autoplay=1&rel=0"
        title="American Cancer Society Breast Cancer Screening Guideline Overview"
        width="100%"
        height="100%"
        style="border: 0; position: absolute; inset: 0; width: 100%; height: 100%;"
        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
        referrerpolicy="strict-origin-when-cross-origin"
        allowfullscreen>
      </iframe>
    `;
  }, { once: true });
}
