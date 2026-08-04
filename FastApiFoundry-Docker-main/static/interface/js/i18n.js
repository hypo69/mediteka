/**
 * i18n.js â€” Internationalization module
 *
 * Uses i18next (loaded via CDN in _head.html).
 *
 * HTML attribute conventions:
 *   data-i18n="key"             â€” sets element innerHTML
 *   data-i18n-placeholder="key" â€” sets input/textarea placeholder
 *   data-i18n-title="key"       â€” sets title attribute
 *
 * RTL languages (he) flip document direction automatically.
 * Selected language is saved to config.json via PATCH /api/v1/config.
 * On load: reads language from config.json, falls back to browser lang, then 'en'.
 */

const RTL_LANGS = new Set(['he', 'ar', 'fa']);
const SUPPORTED  = ['en', 'ru', 'he'];

// â”€â”€ Init â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

/**
 * Initialize i18next and apply translations to the DOM.
 * Called once from app.js after DOMContentLoaded.
 * @param {string} lang - language code from config.json (may be empty)
 */
export async function initI18n(lang) {
    // If lang is explicitly set in config â€” use it.
    // If empty/null â€” detect from browser, fall back to 'en'.
    const resolved = SUPPORTED.includes(lang) ? lang : detectLang();

    // Always load English as fallback bundle
    const [mainRes, enRes] = await Promise.all([
        loadLocale(resolved),
        resolved !== 'en' ? loadLocale('en') : Promise.resolve(null),
    ]);

    await i18next.init({
        lng:         resolved,
        fallbackLng: 'en',
        resources:   { [resolved]: { translation: mainRes } },
        interpolation: { escapeValue: false },
    });

    if (enRes) {
        i18next.addResourceBundle('en', 'translation', enRes, true, true);
    }

    applyTranslations();
    applyDirection(resolved);
    syncSelectors(resolved);
}

// â”€â”€ Language switching â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

/**
 * Switch language, re-apply all translations, save to config.json.
 * Exposed on window.switchLang so navbar/settings onchange can call it.
 * @param {string} lang
 */
export async function switchLang(lang) {
    if (!SUPPORTED.includes(lang)) return;

    // Lazy-load locale bundle if not yet loaded
    if (!i18next.hasResourceBundle(lang, 'translation')) {
        const res = await loadLocale(lang);
        i18next.addResourceBundle(lang, 'translation', res, true, true);
    }

    await i18next.changeLanguage(lang);
    applyTranslations();
    applyDirection(lang);
    syncSelectors(lang);

    // Persist to config.json
    fetch(`${window.API_BASE}/config`, {
        method:  'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ 'app.language': lang }),
    }).catch(() => {});
}

// â”€â”€ DOM translation â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

/**
 * Walk the DOM and update all elements with data-i18n* attributes.
 * Safe to call multiple times â€” idempotent.
 */
export function applyTranslations() {
    // Text / HTML content
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const val = i18next.t(el.getAttribute('data-i18n'));
        if (val) el.innerHTML = val;
    });

    // Input / textarea placeholder
    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
        const val = i18next.t(el.getAttribute('data-i18n-placeholder'));
        if (val) el.placeholder = val;
    });

    // Tooltip / title attribute
    document.querySelectorAll('[data-i18n-title]').forEach(el => {
        const val = i18next.t(el.getAttribute('data-i18n-title'));
        if (val) el.title = val;
    });
}

// â”€â”€ Helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

async function loadLocale(lang) {
    try {
        const r = await fetch(`/static/interface/locales/${lang}.json`);
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return await r.json();
    } catch (e) {
        console.error(`[i18n] Failed to load locale: ${lang}`, e);
        return {};
    }
}

function detectLang() {
    const browser = (navigator.language || 'en').split('-')[0];
    return SUPPORTED.includes(browser) ? browser : 'en';
}

function applyDirection(lang) {
    const dir = RTL_LANGS.has(lang) ? 'rtl' : 'ltr';
    document.documentElement.setAttribute('dir', dir);
    document.documentElement.setAttribute('lang', lang);
}

/**
 * Sync all language selector elements to the current language.
 * Handles both navbar (#lang-selector) and settings (#lang-selector-settings).
 */
function syncSelectors(lang) {
    document.querySelectorAll('#lang-selector, #lang-selector-settings').forEach(sel => {
        sel.value = lang;
    });
}

