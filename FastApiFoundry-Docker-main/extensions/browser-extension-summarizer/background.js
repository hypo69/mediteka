// background.js
// Service worker расширения. Отвечает за:
//   - создание контекстного меню
//   - обработку кликов по меню
//   - оркестрацию задач суммаризации (создание job, обновление статусов)
//   - делегирование запросов к API соответствующим коннекторам

import { logger }        from './logger.js';
import { UIManager }     from './ui-manager.js';
import { summarizePage, mergeSummaries } from './summarizer.js';
import { FACTCHECK } from './prompts/factcheck.js';
import { sendRequest as geminiRequest }    from './connectors/gemini.js';
import { sendRequest as openrouterRequest } from './connectors/openrouter.js';
import { sendRequest as openaiRequest }     from './connectors/openai-compat.js';

// ── Контекстное меню ─────────────────────────────────────────────────────────

chrome.runtime.onInstalled.addListener(() => {
    // removeAll перед созданием — защита от дублирования пунктов меню
    // при повторной установке или обновлении расширения
    chrome.contextMenus.removeAll(() => {
        // contexts: ['page', 'frame'] — 'frame' нужен чтобы меню появлялось
        // внутри <iframe> (например редактор кода на GitHub, встроенные виджеты).
        // Без 'frame' Chrome показывает меню расширения только на основной странице.
        chrome.contextMenus.create({ id: 'summarize-parent',    title: 'AI Assist',      contexts: ['page', 'frame'] });
        chrome.contextMenus.create({ id: 'summarize-this-page', title: 'This Tab',        contexts: ['page', 'frame'], parentId: 'summarize-parent' });
        chrome.contextMenus.create({ id: 'summarize-all-tabs',  title: 'All Open Tabs',   contexts: ['page', 'frame'], parentId: 'summarize-parent' });
        chrome.contextMenus.create({ id: 'check-this-fact',     title: 'Check This Fact', contexts: ['selection', 'frame'] });
        logger.info('Context menu created');
    });
});

// ── Защита от двойных кликов ─────────────────────────────────────────────────
// Service worker может получить несколько событий подряд если пользователь
// кликает быстро. Флаг processing блокирует повторный запуск на 300мс.

const ClickGuard = { processing: false };

chrome.contextMenus.onClicked.addListener(async (info, tab) => {
    if (ClickGuard.processing) return;
    ClickGuard.processing = true;
    try {
        if (info.menuItemId === 'summarize-this-page') await handleSummarizePage(tab);
        else if (info.menuItemId === 'summarize-all-tabs') await handleSummarizeAllTabs(tab);
        else if (info.menuItemId === 'check-this-fact')   await handleCheckFact(info, tab);
    } catch (ex) {
        logger.error('Menu click error', { error: ex.message, stack: ex.stack });
    } finally {
        setTimeout(() => { ClickGuard.processing = false; }, 300);
    }
});

// ── Storage helpers ──────────────────────────────────────────────────────────

/**
 * Чтение активных настроек провайдера из storage.
 * ai_assist — не требует API ключа, customUrl указывает на localhost:9696.
 *
 * @returns {Promise<{provider, model, apiKey, customUrl, lang}>}
 */
async function getSettings() {
    const data = await chrome.storage.sync.get([
        'activeProvider', 'activeModel', 'activeKeyIndex',
        'providerKeys', 'summaryLang', 'summaryProvider', 'summaryModel'
    ]);
    const {
        activeProvider, activeModel,
        activeKeyIndex = {}, providerKeys = {},
        summaryLang = 'auto',
        summaryProvider, summaryModel
    } = data;

    const provider = summaryProvider || activeProvider;
    const model    = summaryModel    || activeModel;

    if (!provider) {
        logger.warn('No provider configured. Open the extension popup.');
    }
    if (!model) {
        logger.warn('No model selected. Open the extension popup.');
    }

    const keys   = providerKeys[provider] || [];
    const keyArr = Array.isArray(keys) ? keys : (keys ? [keys] : []);
    const keyIdx = summaryProvider ? 0 : (activeKeyIndex[provider] ?? 0);
    const apiKey = keyArr[keyIdx] || '';

    // ai_assist работает локально — ключ не нужен
    if (!apiKey && provider !== 'custom' && provider !== 'ai_assist') {
        logger.warn('API key is not set. Open the extension popup.');
    }

    const customUrl = providerKeys['custom_url'] || 'http://localhost:9696';
    return { provider, model, apiKey, customUrl, lang: summaryLang };
}

/**
 * Извлечение очищенного текста из вкладки через scripting.
 * Клонирование DOM чтобы не мутировать живую страницу.
 * Удаление шумовых элементов: скрипты, стили, навигация, реклама.
 *
 * @param {number} tabId
 * @returns {Promise<string>}
 */
async function extractPageText(tabId) {
    let results;
    try {
        results = await chrome.scripting.executeScript({
            target: { tabId },
            func: () => {
                const clone = document.documentElement.cloneNode(true);
                clone.querySelectorAll(
                    'script,style,noscript,svg,iframe,nav,header,footer,' +
                    '[role="navigation"],[role="banner"],[role="complementary"],' +
                    '.ad,.ads,.advertisement,.cookie-notice,.popup'
                ).forEach(el => el.remove());
                return (clone.innerText || clone.textContent || '').replace(/\s{3,}/g, '\n\n').trim();
            }
        });
    } catch (ex) {
        throw new Error(`Cannot access tab ${tabId}: ${ex.message}`);
    }
    return results?.[0]?.result || '';
}

/**
 * Создание объекта задачи в chrome.storage.local с возвратом её id.
 * Задачи хранятся в local (не sync) — они временные, большие, не нужны на других устройствах.
 *
 * @param {'single'|'multi'} mode
 * @param {number} total
 * @returns {Promise<string>} jobId
 */
async function createJob(mode, total) {
    const jobId = `job_${Date.now()}`;
    await chrome.storage.local.set({
        [jobId]: {
            mode,
            status: 'running', // running | merging | done | error
            total,
            done: 0,
            tabs: [],          // [{title, url, summary, status}]
            finalSummary: null,
            error: null,
            createdAt: Date.now()
        }
    });
    return jobId;
}

/**
 * Patch-обновление полей задачи в storage (не перезапись целиком).
 * Чтение актуального состояния перед записью — параллельные вкладки могут
 * обновлять разные поля одновременно.
 *
 * @param {string} jobId
 * @param {object} patch
 */
async function patchJob(jobId, patch) {
    const { [jobId]: job } = await chrome.storage.local.get(jobId);
    await chrome.storage.local.set({ [jobId]: { ...job, ...patch } });
}

// ── Обработчики ──────────────────────────────────────────────────────────────

/**
 * Суммаризация текущей вкладки.
 * Сохранение sourceTabId до открытия summary-вкладки — после её открытия
 * активной становится summary, и tab.id уже не указывает на исходную страницу.
 */
async function handleSummarizePage(tab) {
    const sourceTabId = tab.id;
    const sourceTitle = tab.title;
    const sourceUrl   = tab.url;

    logger.info('Summarize this page', { tabId: sourceTabId, url: sourceUrl });

    const jobId = await createJob('single', 1);
    await UIManager.openSummaryTab(jobId);

    try {
        const { provider, apiKey, model, customUrl, lang } = await getSettings();

        await patchJob(jobId, {
            tabs: [{ title: sourceTitle, url: sourceUrl, status: 'extracting', summary: null }]
        });

        const text = await extractPageText(sourceTabId);
        if (!text) throw new Error('Could not extract text from the page.');

        await patchJob(jobId, {
            tabs: [{ title: sourceTitle, url: sourceUrl, status: 'summarizing', summary: null }]
        });

        const summary = await summarizePage(text, provider, apiKey, model, customUrl, lang);

        await patchJob(jobId, {
            status: 'done', done: 1, finalSummary: summary,
            tabs: [{ title: sourceTitle, url: sourceUrl, status: 'done', summary }]
        });

        logger.info('Single page summary done', { jobId });

    } catch (ex) {
        logger.error('handleSummarizePage error', { error: ex.message, stack: ex.stack });
        await patchJob(jobId, { status: 'error', error: ex.message });
    }
}

/**
 * Суммаризация всех открытых вкладок (иерархически).
 *
 * Шаг 1: параллельная суммаризация каждой вкладки через Promise.allSettled.
 *   allSettled (не all) — ошибка одной вкладки не прерывает остальные.
 *
 * Шаг 2: объединение всех мини-саммари в один финальный запрос.
 *   Одна успешная вкладка — merge не нужен, берём её саммари напрямую.
 */
async function handleSummarizeAllTabs(originTab) {
    const allTabs = (await chrome.tabs.query({})).filter(
        t => t.url && (t.url.startsWith('http://') || t.url.startsWith('https://'))
    );

    if (!allTabs.length) { logger.warn('No accessible tabs found'); return; }

    logger.info('Summarize all tabs', { count: allTabs.length });

    const jobId = await createJob('multi', allTabs.length);
    await UIManager.openSummaryTab(jobId);

    try {
        const { provider, apiKey, model, customUrl, lang } = await getSettings();

        await patchJob(jobId, {
            tabs: allTabs.map(t => ({ title: t.title || t.url, url: t.url, status: 'pending', summary: null }))
        });

        // Шаг 1: параллельная суммаризация
        const results = await Promise.allSettled(
            allTabs.map(async (t, idx) => {
                const update = async (patch) => {
                    const { [jobId]: job } = await chrome.storage.local.get(jobId);
                    Object.assign(job.tabs[idx], patch);
                    if (patch.status === 'done' || patch.status === 'skipped') job.done += 1;
                    await chrome.storage.local.set({ [jobId]: job });
                };

                await update({ status: 'extracting' });

                let text = '';
                try { text = await extractPageText(t.id); }
                catch (ex) { logger.warn('Cannot extract text', { url: t.url, error: ex.message }); }

                if (!text) {
                    await update({ status: 'skipped', summary: '(no extractable content)' });
                    return { title: t.title || t.url, summary: '(no extractable content)' };
                }

                await update({ status: 'summarizing' });
                const summary = await summarizePage(text, provider, apiKey, model, customUrl, lang);
                await update({ status: 'done', summary });

                return { title: t.title || t.url, summary };
            })
        );

        // Собираем только успешные саммари с реальным контентом
        const successful = results
            .filter(r => r.status === 'fulfilled')
            .map(r => r.value)
            .filter(s => s.summary && s.summary !== '(no extractable content)');

        if (!successful.length) throw new Error('Could not summarize any tab.');

        // Шаг 2: финальное объединение
        await patchJob(jobId, { status: 'merging' });

        const finalSummary = successful.length === 1
            ? successful[0].summary
            : await mergeSummaries(successful, provider, apiKey, model, customUrl, lang);

        await patchJob(jobId, { status: 'done', finalSummary });
        logger.info('All-tabs summary done', { jobId, tabCount: allTabs.length });

    } catch (ex) {
        logger.error('handleSummarizeAllTabs error', { error: ex.message, stack: ex.stack });
        await patchJob(jobId, { status: 'error', error: ex.message });
    }
}

/**
 * Проверка факта для выделенного текста.
 *
 * Результат записывается в chrome.storage.local в виде job.
 * chat.js читает его напрямую из storage через polling
 * и показывает как диалог в чате.
 *
 * @param {chrome.contextMenus.OnClickData} info
 * @param {chrome.tabs.Tab} tab
 */
async function handleCheckFact(info, tab) {
    const selection = info.selectionText?.trim();
    if (!selection) return;

    logger.info('Check this fact', { length: selection.length, url: tab.url });

    const jobId = `job_${Date.now()}`;
    await chrome.storage.local.set({
        [jobId]: {
            mode: 'factcheck',
            status: 'running',
            selection,
            finalSummary: null,
            error: null,
            createdAt: Date.now()
        }
    });

    // Открываем чат с параметром factcheck — chat.js загрузит результат из storage
    // и покажет его как сообщение ассистента. Пользователь может продолжить диалог.
    chrome.tabs.create({ url: chrome.runtime.getURL(`chat.html?factcheck=${jobId}`), active: true });

    try {
        const { provider, apiKey, model, customUrl } = await getSettings();
        const messages = [{ role: 'user', content: FACTCHECK + selection }];

        let result;
        if (provider === 'gemini')          result = await geminiRequest(messages, apiKey, model);
        else if (provider === 'openrouter') result = await openrouterRequest(messages, apiKey, model);
        else                                result = await openaiRequest(provider, apiKey, model, messages, customUrl);

        const { [jobId]: job } = await chrome.storage.local.get(jobId);
        await chrome.storage.local.set({ [jobId]: { ...job, status: 'done', finalSummary: result } });
        logger.info('Fact check done', { jobId });
    } catch (ex) {
        logger.error('handleCheckFact error', { error: ex.message });
        const { [jobId]: job } = await chrome.storage.local.get(jobId);
        await chrome.storage.local.set({ [jobId]: { ...job, status: 'error', error: ex.message } });
    }
}

// ── RAG: сохранение страницы ─────────────────────────────────────────────────

/**
 * Сохраняет текущую страницу в chrome.storage.local как RAG-запись.
 * Текст извлекается тем же способом что и для суммаризации.
 *
 * @param {chrome.tabs.Tab} tab
 */
async function handleRagSavePage(tab) {
    // Нельзя извлекать текст из системных страниц и страниц самого расширения
    if (!tab.url || tab.url.startsWith('chrome') || tab.url.startsWith('about') || tab.url.startsWith('chrome-extension')) {
        logger.warn('RAG: cannot access this tab', { url: tab.url });
        return;
    }
    const entry = { id: `rag_${Date.now()}`, url: tab.url, title: tab.title, savedAt: Date.now(), text: '', status: 'pending' };

    // Сохраняем запись сразу — чтобы пользователь видел её в списке
    const { ragEntries = [] } = await chrome.storage.local.get('ragEntries');
    ragEntries.push(entry);
    await chrome.storage.local.set({ ragEntries });

    logger.info('RAG entry created', { id: entry.id, url: entry.url });

    try {
        const text = await extractPageText(tab.id);
        entry.text   = text;
        entry.status = 'ready';
    } catch (ex) {
        logger.error('RAG extractPageText failed', { error: ex.message });
        entry.status = 'error';
        entry.error  = ex.message;
    }

    // Обновляем запись с текстом
    const { ragEntries: updated = [] } = await chrome.storage.local.get('ragEntries');
    const idx = updated.findIndex(e => e.id === entry.id);
    if (idx !== -1) updated[idx] = entry;
    await chrome.storage.local.set({ ragEntries: updated });

    logger.info('RAG entry saved', { id: entry.id, status: entry.status, chars: entry.text.length });
}

// ── Сообщения от summary.html и rag-storage.html ─────────────────────────────
// service worker может быть неактивен — сообщение его разбудит.

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'getJob') {
        chrome.storage.local.get(request.jobId, result => {
            sendResponse({ job: result[request.jobId] || null });
        });
        return true;
    }

    // chat.js сохраняет summary как RAG-запись
    if (request.action === 'saveToRag') {
        const { title, url, text } = request;
        const entry = { id: `rag_${Date.now()}`, url, title, savedAt: Date.now(), text, status: 'ready' };
        chrome.storage.local.get('ragEntries', async ({ ragEntries = [] }) => {
            ragEntries.push(entry);
            await chrome.storage.local.set({ ragEntries });
            sendResponse({ ok: true, id: entry.id });
        });
        return true;
    }

    // rag-storage.js запрашивает список записей
    if (request.action === 'getRagEntries') {
        chrome.storage.local.get('ragEntries', ({ ragEntries = [] }) => {
            sendResponse({ entries: ragEntries });
        });
        return true;
    }

    // rag-storage.js удаляет запись
    if (request.action === 'deleteRagEntry') {
        chrome.storage.local.get('ragEntries', async ({ ragEntries = [] }) => {
            const filtered = ragEntries.filter(e => e.id !== request.id);
            await chrome.storage.local.set({ ragEntries: filtered });
            sendResponse({ ok: true });
        });
        return true;
    }

    // rag-storage.js отправляет записи на FastAPI /api/v1/rag/build
    if (request.action === 'sendToRag') {
        handleSendToRag(request.ids, request.serverUrl)
            .then(result => sendResponse(result))
            .catch(ex  => sendResponse({ ok: false, error: ex.message }));
        return true;
    }
});

/**
 * Отправляет выбранные RAG-записи на сервер FastAPI Foundry.
 * Каждая запись отправляется как текстовый документ через /api/v1/rag/build.
 *
 * @param {string[]} ids       - массив id записей для отправки
 * @param {string}   serverUrl - базовый URL сервера, например http://localhost:9696
 * @returns {Promise<{ok: boolean, sent: number, errors: string[]}>}
 */
async function handleSendToRag(ids, serverUrl) {
    const { ragEntries = [] } = await chrome.storage.local.get('ragEntries');
    const toSend = ragEntries.filter(e => ids.includes(e.id) && e.status === 'ready' && e.text);

    if (!toSend.length) return { ok: false, error: 'No ready entries selected' };

    const errors = [];
    let sent = 0;

    for (const entry of toSend) {
        try {
            const res = await fetch(`${serverUrl}/api/v1/rag/build`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: entry.text, source: entry.url, title: entry.title })
            });
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            sent++;
            logger.info('RAG entry sent', { id: entry.id, url: entry.url });
        } catch (ex) {
            logger.error('RAG send failed', { id: entry.id, error: ex.message });
            errors.push(`${entry.title}: ${ex.message}`);
        }
    }

    return { ok: sent > 0, sent, errors };
}
