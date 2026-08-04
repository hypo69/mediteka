# Openai Compat

**Файл:** `extensions/browser-extension-summarizer/connectors/openai-compat.js`  
**Тип:** `.js`

---

### `buildHeaders`

Формирование заголовков запроса.
 *
 * ПОЧЕМУ ОТДЕЛЬНАЯ ФУНКЦИЯ:
 *   Anthropic использует x-api-key вместо Authorization и требует
 *   обязательный заголовок anthropic-version. Остальные — стандартный Bearer.

### `buildBody`

Формирование тела запроса.
 *
 * ПОЧЕМУ ОТДЕЛЬНАЯ ФУНКЦИЯ:
 *   Anthropic требует обязательный max_tokens.
 *   NVIDIA требует stream: false явно (иначе стримит).
 *   Остальные — минимальный { model, messages }.

### `extractText`

Извлечение текста ответа.
 *
 * ПОЧЕМУ ОТДЕЛЬНАЯ ФУНКЦИЯ:
 *   Anthropic возвращает { content: [{ type:'text', text:'...' }] },
 *   все остальные — { choices: [{ message: { content:'...' } }] }.

### `sendRequest`

Запрос к OpenAI-совместимому провайдеру.
 *
 *

| Параметр | Тип | Описание |
|---|---|---|
| `provider` | `string` | * @param {string} apiKey |
| `model` | `string` | * @param {Array<{role: string, content: string}>} messages |


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
