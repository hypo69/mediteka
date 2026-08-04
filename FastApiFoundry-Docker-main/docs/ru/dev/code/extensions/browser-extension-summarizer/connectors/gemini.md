# Gemini

**Файл:** `extensions/browser-extension-summarizer/connectors/gemini.js`  
**Тип:** `.js`

---

### `sendRequest`

Запрос к Gemini generateContent API.
 *
 * ПОЧЕМУ КЛЮЧ В QUERY-ПАРАМЕТРЕ:
 *   Gemini API требует ?key=, а не Authorization: Bearer.
 *   Все остальные провайдеры используют Bearer — это особенность только Google.
 *
 * КОНВЕРТАЦИЯ РОЛЕЙ:
 *   OpenAI использует роли user/assistant, Gemini — user/model.
 *   Конвертируем при формировании запроса.
 *
 *

| Параметр | Тип | Описание |
|---|---|---|
| `apiKey` | `string` | * @param {string} model  — короткий id без префикса "models/", например "gemini-2.0-flash" |


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
