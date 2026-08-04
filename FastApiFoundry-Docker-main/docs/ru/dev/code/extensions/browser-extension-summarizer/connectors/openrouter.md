# Openrouter

**Файл:** `extensions/browser-extension-summarizer/connectors/openrouter.js`  
**Тип:** `.js`

---

### `sendRequest`

Запрос к OpenRouter chat/completions.
 *
 * ПОЧЕМУ reasoning ВКЛЮЧЁН ПО УМОЛЧАНИЮ:
 *   OpenRouter игнорирует поле reasoning для моделей без его поддержки —
 *   включать всегда безопасно, для reasoning-моделей даёт лучший результат.
 *
 *

| Параметр | Тип | Описание |
|---|---|---|
| `apiKey` | `string` | * @param {string} model |


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
