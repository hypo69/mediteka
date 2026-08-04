# Ui

**Файл:** `js/ui.js`  
**Тип:** `.js`

---

### `showAlert`

ui.js — Вспомогательные функции интерфейса
 *
 * Содержит:
 *  - showAlert()          — всплывающие уведомления
 *  - updateChatModelBadge() — бейдж активной модели в шапке чата
 *  - updateModelStatus()  — заглушка для статуса модели
 *  - hideProgress()       — скрытие прогресс-бара загрузки
 *  - clearFoundryLogs()   — очистка лога Foundry
 *  - addLog()             — добавление записи в системный лог
 *  - refreshLogs()        — обновление логов с сервера
 *  - filterLogs()         — фильтрация логов по уровню

| Параметр | Тип | Описание |
|---|---|---|
| `message` | `string` | Текст уведомления |
| `type` | `'info'|'success'|'warning'|'danger'` | */ |

### `updateChatModelBadge`

Updates the chat stats badge: model name, response time, token count.
 *

| Параметр | Тип | Описание |
|---|---|---|
| `modelId` | `string` | * @param {{totalTokens?: number, elapsedMs?: number}} [stats] |

### `updateModelStatus`

Заглушка — статус модели выводится только в консоль

### `hideProgress`

Скрывает блок прогресс-бара загрузки модели

### `clearFoundryLogs`

Очищает блок логов Foundry на вкладке Foundry

### `_detectLevel`

| Параметр | Тип | Описание |
|---|---|---|
| `line` | `string` | * @returns {string} |

### `_renderLine`

Render a single log line as a colored <div>.
 * Highlights search term if provided.
 *

| Параметр | Тип | Описание |
|---|---|---|
| `line` | `string` | * @param {string} search |

### `refreshLogs`

Fetch logs from API and render into #log-output.
 *

| Параметр | Тип | Описание |
|---|---|---|
| `append` | `boolean` | If true, prepend older lines (pagination). |

### `_loadMore`

Load older lines (pagination).

### `_toggleAutoRefresh`

Toggle auto-refresh every 5 s.

### `_toggleWrap`

Toggle word-wrap on log output.

### `_downloadLog`

Download current log file from server.

### `_clearLog`

Clear current log file via API.

### `_loadFileList`

Populate file selector from /logs/files.

### `_loadLogSettings`

Load log retention settings into the toolbar.

### `_saveLogSettings`

Save log retention settings.

### `initLogViewer`

Initialize log viewer — attach all event listeners.
 * Called once when the Logs tab becomes active.

### `filterLogs`

### `startFlashingTitle`

| Параметр | Тип | Описание |
|---|---|---|
| `message` | `string` | Текст для мигания. |

### `stopFlashingTitle`

Останавливает мигание заголовка вкладки и возвращает исходный текст.

### `handleHitlTimeout`

Автоматически закрывает модальное окно HITL при получении таймаута от сервера.
 *

| Параметр | Тип | Описание |
|---|---|---|
| `permissionId` | `string` | ID запроса. |

### `playHitlNotification`

Воспроизводит звуковое уведомление для нового запроса HITL.

### `downloadLogs`

### `clearLogFile`

### `addLog`


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
