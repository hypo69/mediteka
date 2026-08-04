# Index

**Файл:** `extensions/browser-extension-summarizer/prompts/index.js`  
**Тип:** `.js`

---

### `getPrompts`

Получение промптов для заданного языка.
 * При lang='auto' или неизвестном языке возвращает английский промпт
 * с инструкцией отвечать на языке контента.
 *
 * ПОЧЕМУ FALLBACK НА en, А НЕ НА ОТДЕЛЬНЫЙ 'auto'-ПРОМПТ:
 *   Английский промпт с фразой "in the same language as the content" уже
 *   корректно обрабатывает авто-режим — модели понимают эту инструкцию.
 *
 *

| Параметр | Тип | Описание |
|---|---|---|
| `lang` | `string` | * @returns {{ PAGE: string, MERGE: string }} |


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
