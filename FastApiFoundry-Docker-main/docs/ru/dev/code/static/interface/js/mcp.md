# Mcp

**Файл:** `static/interface/js/mcp.js`  
**Тип:** `.js`

---

### `mcpLoadServers`

mcp.js — Управление MCP PowerShell серверами
 *
 * Содержит:
 *  - mcpLoadServers()         — загрузка списка серверов
 *  - mcpStart(name)           — запуск сервера
 *  - mcpStop(name)            — остановка сервера
 *  - startAllMCPServers()     — запуск всех серверов
 *  - stopAllMCPServers()      — остановка всех серверов
 *  - refreshMCPServers()      — алиас mcpLoadServers
 *  - mcpOpenSettingsEditor()  — открыть редактор settings.json
 *  - mcpSaveSettings()        — сохранить settings.json
 *  - mcpCloseSettingsEditor() — закрыть редактор

### `mcpStart`

Алиас для кнопки Refresh

| Параметр | Тип | Описание |
|---|---|---|
| `name` | `string` | */ |

### `mcpStop`

Останавливает MCP сервер по имени.
 *

| Параметр | Тип | Описание |
|---|---|---|
| `name` | `string` | */ |

### `startAllMCPServers`

Запускает все серверы последовательно

### `stopAllMCPServers`

Останавливает все серверы последовательно

### `mcpOpenSettingsEditor`

Открывает редактор settings.json MCP серверов.
 * Загружает текущие настройки в textarea #mcp-settings-editor.

### `mcpSaveSettings`

Сохраняет отредактированный settings.json.
 * Валидирует JSON перед отправкой.

### `mcpCloseSettingsEditor`

Скрывает редактор settings.json


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
