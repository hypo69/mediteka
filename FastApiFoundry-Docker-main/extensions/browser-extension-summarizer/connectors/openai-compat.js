// connectors/openai-compat.js
// Транспортный коннектор для провайдеров с OpenAI-совместимым API.
//
// ОТВЕТСТВЕННОСТЬ: только HTTP-взаимодействие. Никакой логики промптов.
//
// ПОЧЕМУ ОДИН ФАЙЛ ДЛЯ ВСЕХ:
//   OpenAI, Mistral, Groq, DeepSeek, xAI, NVIDIA, Cohere, Anthropic, Custom —
//   все используют формат POST /chat/completions с { model, messages }.
//   Разница только в base URL, заголовках и мелких деталях тела запроса.
//
// ПОЧЕМУ ИНТЕРФЕЙС ПРИНИМАЕТ messages[], А НЕ prompt:
//   Единый интерфейс со всеми коннекторами — chat.js и summarizer.js
//   не должны знать какой коннектор используется под капотом.
//   Для одиночного промпта достаточно передать [{role:'user', content: prompt}].

export const PROVIDER_URLS = {
    openai:    'https://api.openai.com/v1/chat/completions',
    mistral:   'https://api.mistral.ai/v1/chat/completions',
    groq:      'https://api.groq.com/openai/v1/chat/completions',
    cohere:    'https://api.cohere.com/v2/chat',
    deepseek:  'https://api.deepseek.com/chat/completions',
    xai:       'https://api.x.ai/v1/chat/completions',
    nvidia:    'https://integrate.api.nvidia.com/v1/chat/completions',
    anthropic: 'https://api.anthropic.com/v1/messages', // отличается форматом ответа
};

/**
 * Формирование заголовков запроса.
 *
 * ПОЧЕМУ ОТДЕЛЬНАЯ ФУНКЦИЯ:
 *   Anthropic использует x-api-key вместо Authorization и требует
 *   обязательный заголовок anthropic-version. Остальные — стандартный Bearer.
 */
function buildHeaders(provider, apiKey) {
    // HTTP-заголовки принимают только ISO-8859-1 — убираем всё что выходит за диапазон
    const safeKey = apiKey ? apiKey.replace(/[^\x20-\x7E]/g, '') : '';
    if (provider === 'anthropic') {
        return {
            'x-api-key': safeKey,
            'anthropic-version': '2023-06-01',
            'Content-Type': 'application/json'
        };
    }
    return {
        'Authorization': `Bearer ${safeKey}`,
        'Content-Type': 'application/json'
    };
}

/**
 * Формирование тела запроса.
 *
 * ПОЧЕМУ ОТДЕЛЬНАЯ ФУНКЦИЯ:
 *   Anthropic требует обязательный max_tokens.
 *   NVIDIA требует stream: false явно (иначе стримит).
 *   Остальные — минимальный { model, messages }.
 */
function buildBody(provider, model, messages) {
    if (provider === 'anthropic') {
        return { model, messages, max_tokens: 8192 };
    }
    if (provider === 'nvidia') {
        return { model, messages, temperature: 0.15, top_p: 0.95, max_tokens: 8192, stream: false };
    }
    return { model, messages };
}

/**
 * Извлечение текста ответа.
 *
 * ПОЧЕМУ ОТДЕЛЬНАЯ ФУНКЦИЯ:
 *   Anthropic возвращает { content: [{ type:'text', text:'...' }] },
 *   все остальные — { choices: [{ message: { content:'...' } }] }.
 */
function extractText(provider, data) {
    if (data.error) throw new Error(data.error.message || JSON.stringify(data.error));
    if (data.message && !data.choices && !data.content) throw new Error(data.message); // Cohere error

    if (provider === 'anthropic') {
        const text = data.content?.[0]?.text;
        if (!text) throw new Error('Empty response from Anthropic');
        return text;
    }
    const text = data.choices?.[0]?.message?.content;
    if (!text) throw new Error('Empty response from model');
    return text;
}

/**
 * Запрос к OpenAI-совместимому провайдеру.
 *
 * @param {string} provider
 * @param {string} apiKey
 * @param {string} model
 * @param {Array<{role: string, content: string}>} messages
 * @param {string} [customUrl] — base URL для custom-провайдера (Ollama, vLLM и др.)
 * @returns {Promise<string>}
 */
export async function sendRequest(provider, apiKey, model, messages, customUrl = '') {
    // ai_assist — наш FastAPI Foundry, запрос через /api/v1/ai/chat
    if (provider === 'ai_assist') {
        const base = (customUrl || 'http://localhost:9696').replace(/\/$/, '');
        const res = await fetch(`${base}/api/v1/ai/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ model, messages })
        });
        const data = await res.json();
        if (!data.success) throw new Error(data.error || 'FastAPI error');
        return data.content || data.message || '';
    }

    const url = (provider === 'custom')
        ? (customUrl.replace(/\/$/, '') + '/chat/completions')
        : PROVIDER_URLS[provider];

    if (!url) throw new Error(`Unknown provider: ${provider}`);

    const response = await fetch(url, {
        method: 'POST',
        headers: buildHeaders(provider, apiKey),
        body: JSON.stringify(buildBody(provider, model, messages))
    });

    const data = await response.json();
    return extractText(provider, data);
}
