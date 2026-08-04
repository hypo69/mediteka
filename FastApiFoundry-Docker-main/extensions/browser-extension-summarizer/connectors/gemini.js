// connectors/gemini.js
// Транспортный коннектор для Google Gemini API.
//
// ОТВЕТСТВЕННОСТЬ: только HTTP-взаимодействие с Gemini API.
// Никакой логики промптов, суммаризации или обрезки текста — это в summarizer.js.
//
// ПОЧЕМУ ОТДЕЛЬНЫЙ ФАЙЛ:
//   Gemini использует принципиально другой формат запроса (contents/parts вместо
//   messages/content) и передаёт ключ в query-параметре ?key= вместо Bearer-заголовка.
//   Унифицировать с openai-compat.js невозможно без усложнения общего коннектора.
//
// ИНТЕРФЕЙС УНИФИЦИРОВАН С ОСТАЛЬНЫМИ КОННЕКТОРАМИ:
//   Все коннекторы принимают messages в формате [{role, content}] —
//   это стандарт OpenAI, который мы используем как общий язык.
//   Gemini-коннектор конвертирует его во внутренний формат contents/parts.

/**
 * Запрос к Gemini generateContent API.
 *
 * ПОЧЕМУ КЛЮЧ В QUERY-ПАРАМЕТРЕ:
 *   Gemini API требует ?key=, а не Authorization: Bearer.
 *   Все остальные провайдеры используют Bearer — это особенность только Google.
 *
 * КОНВЕРТАЦИЯ РОЛЕЙ:
 *   OpenAI использует роли user/assistant, Gemini — user/model.
 *   Конвертируем при формировании запроса.
 *
 * @param {Array<{role: 'user'|'assistant', content: string}>} messages
 * @param {string} apiKey
 * @param {string} model  — короткий id без префикса "models/", например "gemini-2.0-flash"
 * @returns {Promise<string>}
 */
export async function sendRequest(messages, apiKey, model) {
    const url = `https://generativelanguage.googleapis.com/v1/models/${encodeURIComponent(model)}:generateContent?key=${encodeURIComponent(apiKey)}`;

    // Конвертация messages → contents/parts и роли assistant → model
    const contents = messages.map(m => ({
        role: m.role === 'assistant' ? 'model' : 'user',
        parts: [{ text: m.content }]
    }));

    const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ contents })
    });

    const data = await response.json();

    if (data.error) throw new Error(data.error.message || 'Gemini API error');

    // candidates пуст если контент заблокирован safety-фильтрами
    if (!data.candidates?.length) {
        const reason = data.promptFeedback?.blockReason || 'unknown';
        throw new Error(`Response blocked: ${reason}`);
    }

    const text = data.candidates[0]?.content?.parts?.[0]?.text;
    if (!text) throw new Error('Empty response from Gemini');
    return text;
}
