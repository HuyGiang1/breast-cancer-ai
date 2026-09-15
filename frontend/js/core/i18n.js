import i18next from '../vendor/i18next.js';
import { resources } from '../i18n/resources.js';

const STORAGE_KEY = 'bcai_language';
const SUPPORTED_LANGS = ['vi', 'en'];
const DEFAULT_LANG = 'vi';

function getStoredLanguage() {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved && SUPPORTED_LANGS.includes(saved)) {
      return saved;
    }
  } catch (e) {
    // LocalStorage might be disabled
  }
  return DEFAULT_LANG;
}

const currentLanguage = getStoredLanguage();

// Initialize i18next synchronously with embedded resources
i18next.init({
  lng: currentLanguage,
  fallbackLng: 'en',
  supportedLngs: SUPPORTED_LANGS,
  resources,
  interpolation: {
    escapeValue: false, // Browser DOM handlers escape where needed
  },
  returnEmptyString: false,
});

// Sync initial HTML document lang attribute
if (typeof document !== 'undefined' && document.documentElement) {
  document.documentElement.lang = currentLanguage;
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      updateDocumentTitle();
      applyDomTranslations(document);
    });
  } else {
    updateDocumentTitle();
    applyDomTranslations(document);
  }
}

export function getLanguage() {
  return i18next.language || DEFAULT_LANG;
}

export async function setLanguage(lang) {
  if (!SUPPORTED_LANGS.includes(lang)) return;
  if (i18next.language === lang) return;

  await i18next.changeLanguage(lang);

  try {
    localStorage.setItem(STORAGE_KEY, lang);
  } catch (e) {}

  if (typeof document !== 'undefined' && document.documentElement) {
    document.documentElement.lang = lang;
    updateDocumentTitle();
  }

  // Translate static DOM nodes on page
  if (typeof document !== 'undefined') {
    applyDomTranslations(document);
  }

  // Dispatch global event for interactive components to re-render
  if (typeof window !== 'undefined') {
    window.dispatchEvent(
      new CustomEvent('bcai:languageChanged', {
        detail: { lang },
      })
    );
  }
}

export function updateDocumentTitle() {
  if (typeof document === 'undefined') return;
  const lang = getLanguage();
  const path = (typeof window !== 'undefined' && window.location ? window.location.pathname.toLowerCase() : '');

  const titles = {
    'ml-analysis': { vi: 'Phân tích ML · Breast Health Studio', en: 'ML Analysis · Breast Health Studio' },
    'dl-analysis': { vi: 'Phân tích Nhũ ảnh · Breast Health Studio', en: 'Mammography DL Analysis · Breast Health Studio' },
    'multimodal': { vi: 'Kết hợp nghiên cứu · Breast Health Studio', en: 'Experimental Fusion · Breast Health Studio' },
    'patient-detail': { vi: 'Chi tiết hồ sơ · Breast Health Studio', en: 'Patient Detail · Breast Health Studio' },
    'patients': { vi: 'Hồ sơ đối tượng · Breast Health Studio', en: 'Doctor Workspace · Breast Health Studio' },
    'history': { vi: 'Lịch sử phân tích · Breast Health Studio', en: 'Activity · Breast Health Studio' },
    'reports': { vi: 'Báo cáo phân tích · Breast Health Studio', en: 'Analysis Reports · Breast Health Studio' },
    'advisor': { vi: 'Hướng dẫn AI · Breast Health Studio', en: 'AI Guide · Breast Health Studio' },
    'model-status': { vi: 'Trạng thái mô hình · Breast Health Studio', en: 'Model Status · Breast Health Studio' },
    'profile': { vi: 'Tài khoản & Bảo mật · Breast Health Studio', en: 'Profile · Breast Health Studio' },
    'login': { vi: 'Đăng nhập · Breast Health Studio', en: 'Sign in · Breast Health Studio' },
    'register': { vi: 'Đăng ký tài khoản · Breast Health Studio', en: 'Create Account · Breast Health Studio' },
    'forgot-password': { vi: 'Quên mật khẩu · Breast Health Studio', en: 'Forgot Password · Breast Health Studio' },
    'reset-password': { vi: 'Đặt lại mật khẩu · Breast Health Studio', en: 'Reset Password · Breast Health Studio' },
  };

  for (const [key, map] of Object.entries(titles)) {
    if (path.includes(key)) {
      document.title = map[lang] || map.en;
      return;
    }
  }

  if (path.endsWith('/') || path.includes('index.html')) {
    document.title = lang === 'vi'
      ? 'Breast Health Studio · Nghiên cứu AI y tế & Giáo dục'
      : 'Breast Health Studio · AI Medical Research & Education';
  }
}

export function t(key, options = {}) {
  return i18next.t(key, options);
}

/**
 * Automatically applies translations to any DOM tree containing data-i18n attributes.
 */
export function applyDomTranslations(root = document) {
  if (!root) return;

  root.querySelectorAll('[data-i18n]').forEach((el) => {
    const key = el.getAttribute('data-i18n');
    if (key) {
      el.textContent = t(key);
    }
  });

  root.querySelectorAll('[data-i18n-html]').forEach((el) => {
    const key = el.getAttribute('data-i18n-html');
    if (key) {
      el.innerHTML = t(key);
    }
  });

  root.querySelectorAll('[data-i18n-placeholder]').forEach((el) => {
    const key = el.getAttribute('data-i18n-placeholder');
    if (key) {
      el.placeholder = t(key);
    }
  });

  root.querySelectorAll('[data-i18n-title]').forEach((el) => {
    const key = el.getAttribute('data-i18n-title');
    if (key) {
      el.title = t(key);
    }
  });

  root.querySelectorAll('[data-i18n-aria-label]').forEach((el) => {
    const key = el.getAttribute('data-i18n-aria-label');
    if (key) {
      el.setAttribute('aria-label', t(key));
    }
  });
}

/**
 * Renders the standardized Global Language Switcher HTML.
 */
export function renderLanguageSwitcher(extraClass = '') {
  const lang = getLanguage();
  const label = lang === 'vi' ? 'Tiếng Việt' : 'English';

  return `
    <div class="studio-lang-switch ${extraClass}" data-component="language-switcher">
      <button
        type="button"
        class="studio-lang-btn studio-lang-trigger"
        aria-expanded="false"
        aria-haspopup="true"
        aria-label="Change language: current ${label}"
      >
        <span class="studio-lang-globe">🌐</span>
        <span class="studio-lang-label">${label}</span>
        <svg class="chevron" viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="6 9 12 15 18 9"></polyline>
        </svg>
      </button>
      <div class="studio-lang-menu" role="menu">
        <button
          type="button"
          class="studio-lang-option ${lang === 'vi' ? 'active' : ''}"
          data-set-lang="vi"
          role="menuitem"
        >
          <span class="flag">🇻🇳</span>
          <span>Tiếng Việt</span>
          ${lang === 'vi' ? '<span class="check">✓</span>' : ''}
        </button>
        <button
          type="button"
          class="studio-lang-option ${lang === 'en' ? 'active' : ''}"
          data-set-lang="en"
          role="menuitem"
        >
          <span class="flag">🇬🇧</span>
          <span>English</span>
          ${lang === 'en' ? '<span class="check">✓</span>' : ''}
        </button>
      </div>
    </div>
  `;
}

/**
 * Attaches event listeners for the Language Switcher in the DOM.
 */
export function bindLanguageSwitcherEvents(root = document) {
  const switchers = root.querySelectorAll('.studio-lang-switch');

  switchers.forEach((switcher) => {
    const trigger = switcher.querySelector('.studio-lang-btn');
    const menu = switcher.querySelector('.studio-lang-menu');

    if (!trigger || !menu) return;

    trigger.onclick = (e) => {
      e.stopPropagation();
      const open = switcher.classList.toggle('is-open');
      menu.classList.toggle('is-open', open);
      trigger.setAttribute('aria-expanded', String(open));
    };

    const options = menu.querySelectorAll('[data-set-lang]');
    options.forEach((opt) => {
      opt.onclick = async (e) => {
        e.stopPropagation();
        const targetLang = opt.getAttribute('data-set-lang');
        switcher.classList.remove('is-open');
        menu.classList.remove('is-open');
        trigger.setAttribute('aria-expanded', 'false');
        await setLanguage(targetLang);
      };
    });
  });

  // Click outside closes menu
  document.addEventListener('click', (e) => {
    document.querySelectorAll('.studio-lang-switch.is-open').forEach((s) => {
      if (!s.contains(e.target)) {
        s.classList.remove('is-open');
        s.querySelector('.studio-lang-menu')?.classList.remove('is-open');
        s.querySelector('.studio-lang-btn')?.setAttribute('aria-expanded', 'false');
      }
    });
  });
}

export { i18next };
export default {
  getLanguage,
  setLanguage,
  t,
  applyDomTranslations,
  renderLanguageSwitcher,
  bindLanguageSwitcherEvents,
};
