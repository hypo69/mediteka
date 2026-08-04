// connectors/openrouter.js
// Транспортный коннектор для OpenRouter.
//
// ОТВЕТСТВЕННОСТЬ: только HTTP-взаимодействие с OpenRouter API.
//
// ПОЧЕМУ ОТДЕЛЬНЫЙ ФАЙЛ:
//   OpenRouter поддерживает поле reasoning: { enabled: true } — нестандартное
//   расширение для моделей с цепочкой рассуждений (DeepSeek-R1, o1 и др.).
//   Добавлять эту специфику в openai-compat.js нарушило бы его универсальность.

/**
 * Запрос к OpenRouter chat/completions.
 *
 * ПОЧЕМУ reasoning ВКЛЮЧЁН ПО УМОЛЧАНИЮ:
 *   OpenRouter игнорирует поле reasoning для моделей без его поддержки —
 *   включать всегда безопасно, для reasoning-моделей даёт лучший результат.
 *
 * @param {Array<{role: string, content: string}>} messages
 * @param {string} apiKey
 * @param {string} model
 * @returns {Promise<string>}
 */
export async function sendRequest(messages, apiKey, model) {
    const response = await fetch('https://openrouter.ai/api/v1/chat/completions', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${apiKey}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            model,
            messages,
            reasoning: { enabled: true }
        })
    });

    const data = await response.json();
    if (!data.choices?.[0]) throw new Error(data.error?.message || 'No response from OpenRouter');
    return data.choices[0].message.content;
}
