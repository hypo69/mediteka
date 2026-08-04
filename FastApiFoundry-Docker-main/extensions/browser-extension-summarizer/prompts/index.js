// prompts/index.js
// Реестр доступных языков суммаризации.
//
// ПОЧЕМУ РЕЕСТР ОТДЕЛЬНО ОТ ПРОМПТОВ:
//   Каждый язык — отдельный файл с промптами (en.js, ru.js и т.д.).
//   Этот файл только описывает метаданные языков и импортирует промпты.
//   Добавить новый язык = создать файл prompts/xx.js и добавить одну строку сюда.
//
// ПОЧЕМУ НЕ ДИНАМИЧЕСКИЙ IMPORT:
//   Service worker (background.js) не поддерживает динамические импорты надёжно
//   в Manifest V3. Статические импорты — единственный безопасный вариант.

import * as en from './en.js';
import * as ru from './ru.js';
import * as de from './de.js';
import * as fr from './fr.js';
import * as es from './es.js';
import * as zh from './zh.js';
import * as ja from './ja.js';

// LANGUAGES — список для UI (селект в настройках).
// label — отображаемое название, value — ключ языка.
export const LANGUAGES = [
    { value: 'auto', label: 'Auto (same as page)' },
    { value: 'en',   label: 'English' },
    { value: 'ru',   label: 'Русский' },
    { value: 'de',   label: 'Deutsch' },
    { value: 'fr',   label: 'Français' },
    { value: 'es',   label: 'Español' },
    { value: 'zh',   label: '中文' },
    { value: 'ja',   label: '日本語' },
];

// Карта промптов по ключу языка.
const PROMPTS = { en, ru, de, fr, es, zh, ja };

/**
 * Получение промптов для заданного языка.
 * При lang='auto' или неизвестном языке возвращает английский промпт
 * с инструкцией отвечать на языке контента.
 *
 * ПОЧЕМУ FALLBACK НА en, А НЕ НА ОТДЕЛЬНЫЙ 'auto'-ПРОМПТ:
 *   Английский промпт с фразой "in the same language as the content" уже
 *   корректно обрабатывает авто-режим — модели понимают эту инструкцию.
 *
 * @param {string} lang
 * @returns {{ PAGE: string, MERGE: string }}
 */
export function getPrompts(lang) {
    if (lang === 'auto' || !PROMPTS[lang]) {
        return {
            PAGE: `You are a concise summarizer. Given the text content of a web page, produce a clear, structured summary in the same language as the content.

Rules:
- Keep the summary under 300 words
- Use bullet points for key facts
- Start with one sentence describing what the page is about
- Omit navigation menus, ads, cookie notices, and boilerplate
- Return valid HTML only (use <p>, <ul>, <li>, <strong> tags). No markdown, no code fences.

Page content:
`,
            MERGE: `You are a concise summarizer. Below are individual summaries of multiple open browser tabs. Produce a single coherent summary in the same language as the majority of the content.

Rules:
- Keep the final summary under 500 words
- Group related topics together
- Use bullet points for key facts
- Return valid HTML only (use <p>, <ul>, <li>, <strong> tags). No markdown, no code fences.

Individual tab summaries:
`
        };
    }
    return PROMPTS[lang];
}
