# Sdk

**Файл:** `static/interface/js/sdk.js`  
**Тип:** `.js`

---

### `loadExamples`

sdk.js — Примеры SDK
 *
 * Содержит:
 *  - loadExamples()           — загрузка списка примеров
 *  - loadSelectedExample()    — загрузка кода выбранного примера
 *  - runExample()             — выполнение примера через API
 *  - copyExampleToClipboard() — копирование кода в буфер

### `loadSelectedExample`

Загружает код выбранного примера в textarea #example-code.

### `runExample`

Выполняет выбранный пример через POST /examples/{id}/run.
 * Результат отображается в #example-output.

### `copyExampleToClipboard`

Копирует код примера в буфер обмена


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
