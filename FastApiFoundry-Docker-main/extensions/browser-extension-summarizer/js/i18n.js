// -*- coding: utf-8 -*-
// =============================================================================
// Process Name: Extension i18n — internationalization module
// =============================================================================
// Description:
//   Mirrors static/js/i18n.js pattern for browser extension context.
//   Loads locale JSON from extension bundle (no CDN, no server API).
//   Persists language choice to chrome.storage.sync.
//
//   HTML attribute conventions (identical to static UI):
//     data-i18n="key"             — sets element innerHTML
//     data-i18n-placeholder="key" — sets input/textarea placeholder
//     data-i18n-title="key"       — sets title attribute
//
//   RTL languages (he) flip document direction automatically.
//
// File: js/i18n.js
// Project: FastApiFoundry (Docker)
// Version: 0.6.0
// Author: hypo69
// Copyright: © 2026 hypo69
// =============================================================================

const RTL_LANGS = new Set(['he', 'ar', 'fa']);
const SUPPORTED  = ['en', 'ru', 'he'];

// In-memory translation bundles: { lang: { ...keys } }
const _bundles = {};

// ── Public API ────────────────────────────────────────────────────────────────

/**
 * Initialize i18n and apply translations to the DOM.
 * Reads saved language from chrome.storage.sync, falls back to browser lang.
 * @returns {Promise<string>} resolved language code
 */
export async function initI18n() {
    const saved = await _loadSavedLang();
    const lang  = SUPPORTED.includes(saved) ? saved : _detectLang();

    await _ensureBundle(lang);
    if (lang !== 'en') await _ensureBundle('en');

    applyTranslations(lang);
    _applyDirection(lang);
    _syncSelectors(lang);

    // Attach change listener to all .lang-select elements present at init time.
    // Uses event delegation on document for selectors added after init.
    document.addEventListener('change', e => {
        if (e.target.classList.contains('lang-select')) {
            switchLang(e.target.value);
        }
    });

    return lang;
}

/**
 * Switch language, re-apply all translations, persist to chrome.storage.sync.
 * @param {string} lang
 */
export async function switchLang(lang) {
    if (!SUPPORTED.includes(lang)) return;
    await _ensureBundle(lang);
    applyTranslations(lang);
    _applyDirection(lang);
    _syncSelectors(lang);
    chrome.storage.sync.set({ uiLang: lang });
}

/**
 * Translate a single key (dot-notation). Falls back to 'en', then key itself.
 * @param {string} key  e.g. "chat.send"
 * @param {string} [lang]
 * @returns {string}
 */
export function t(key, lang) {
    const cur = lang || document.documentElement.getAttribute('lang') || 'en';
    return _get(_bundles[cur], key) || _get(_bundles['en'], key) || key;
}

/**
 * Walk the DOM and update all elements with data-i18n* attributes.
 * Idempotent — safe to call multiple times.
 * @param {string} [lang]
 */
export function applyTranslations(lang) {
    const cur = lang || document.documentElement.getAttribute('lang') || 'en';

    document.querySelectorAll('[data-i18n]').forEach(el => {
        const val = t(el.getAttribute('data-i18n'), cur);
        if (val) el.innerHTML = val;
    });

    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
        const val = t(el.getAttribute('data-i18n-placeholder'), cur);
        if (val) el.placeholder = val;
    });

    document.querySelectorAll('[data-i18n-title]').forEach(el => {
        const val = t(el.getAttribute('data-i18n-title'), cur);
        if (val) el.title = val;
    });
}

// ── Helpers ───────────────────────────────────────────────────────────────────

async function _ensureBundle(lang) {
    if (_bundles[lang]) return;
    try {
        const url = chrome.runtime.getURL(`locales/${lang}.json`);
        const res = await fetch(url);
        _bundles[lang] = res.ok ? await res.json() : {};
    } catch {
        _bundles[lang] = {};
    }
}

async function _loadSavedLang() {
    return new Promise(resolve => {
        chrome.storage.sync.get(['uiLang'], d => resolve(d.uiLang || ''));
    });
}

function _detectLang() {
    const browser = (navigator.language || 'en').split('-')[0];
    return SUPPORTED.includes(browser) ? browser : 'en';
}

function _applyDirection(lang) {
    document.documentElement.setAttribute('dir', RTL_LANGS.has(lang) ? 'rtl' : 'ltr');
    document.documentElement.setAttribute('lang', lang);
}

function _syncSelectors(lang) {
    document.querySelectorAll('.lang-select').forEach(sel => { sel.value = lang; });
}

/** Resolve dot-notation key in a nested object */
function _get(bundle, key) {
    if (!bundle) return '';
    let cur = bundle;
    for (const p of key.split('.')) {
        if (cur == null || typeof cur !== 'object') return '';
        cur = cur[p];
    }
    return typeof cur === 'string' ? cur : '';
}
