// -*- coding: utf-8 -*-
// =============================================================================
// Process Name: Summarizer — суммаризация страниц
// =============================================================================
// Description:
//   Маршрутизация запросов к нужному коннектору по providerId.
//   ai_assist → FastAPI Foundry /api/v1/ai/chat
//   Все остальные → соответствующие внешние API через коннекторы.
//
// File: summarizer.js
// Project: AI Assistant (ai_assist)
// Version: 0.8.0
// Author: hypo69
// Copyright: © 2026 hypo69
// =============================================================================

import { sendRequest as geminiRequest }    from './connectors/gemini.js';
import { sendRequest as openrouterRequest } from './connectors/openrouter.js';
import { sendRequest as openaiRequest }     from './connectors/openai-compat.js';
import { getPrompts }                       from './prompts/index.js';

const MAX_CHARS = 80_000;

function route(provider, apiKey, model, messages, customUrl) {
    if (provider === 'gemini')     return geminiRequest(messages, apiKey, model);
    if (provider === 'openrouter') return openrouterRequest(messages, apiKey, model);
    // ai_assist и все OpenAI-совместимые (включая custom) — через openai-compat
    return openaiRequest(provider, apiKey, model, messages, customUrl);
}

/**
 * Суммаризация текста одной страницы.
 *
 * @param {string} pageText
 * @param {string} provider
 * @param {string} apiKey
 * @param {string} model
 * @param {string} [customUrl]
 * @param {string} [lang]
 * @returns {Promise<string>}
 */
export async function summarizePage(pageText, provider, apiKey, model, customUrl = '', lang = 'auto') {
    let text = pageText;
    let truncated = false;
    if (text.length > MAX_CHARS) {
        text = text.slice(0, MAX_CHARS);
        truncated = true;
    }
    const { PAGE } = getPrompts(lang);
    const content = PAGE + text + (truncated ? '\n\n[Content was truncated due to length]' : '');
    return route(provider, apiKey, model, [{ role: 'user', content }], customUrl);
}

/**
 * Объединение массива мини-саммари в один финальный текст.
 *
 * @param {Array<{title: string, summary: string}>} summaries
 * @param {string} provider
 * @param {string} apiKey
 * @param {string} model
 * @param {string} [customUrl]
 * @param {string} [lang]
 * @returns {Promise<string>}
 */
export async function mergeSummaries(summaries, provider, apiKey, model, customUrl = '', lang = 'auto') {
    const combined = summaries
        .map((s, i) => `--- Tab ${i + 1}: ${s.title} ---\n${s.summary}`)
        .join('\n\n');
    const { MERGE } = getPrompts(lang);
    return route(provider, apiKey, model, [{ role: 'user', content: MERGE + combined }], customUrl);
}
