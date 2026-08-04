# McpWPCLIServer.ps1

**Файл:** `mcp/src/servers/McpWPCLIServer.ps1`  
**Протокол:** MCP STDIO (JSON-RPC 2.0)  
**Версия:** 1.2.5  
**Требования:** PowerShell 7.0+, WP-CLI

## Назначение

Выполняет команды WP-CLI на установке WordPress через MCP протокол. Всегда возвращает структурированный JSON-вывод (`--format=json`).

## Инструменты

| Инструмент | Описание |
|---|---|
| `run-wp-cli` | Выполнить WP-CLI команду |
| `check-wp-cli` | Проверить доступность WP-CLI |

### run-wp-cli

| Параметр | Тип | Обязательный | Описание |
|---|---|---|---|
| `commandArguments` | string | ✅ | Аргументы WP-CLI, например `post list` |
| `workingDirectory` | string | — | Путь к директории WordPress |

### Примеры команд

```
post list
post create --post_title="Hello" --post_status=draft
user list
option get siteurl
plugin list
```

## Конфигурация

Файл: `mcp/src/config/Config-McpWPCLI.json`

```json
{
  "ServerConfig": {
    "Name": "WordPress CLI MCP Server",
    "WordPress": {
      "DefaultPath": "",
      "AutoDetectPath": true,
      "ForceJsonOutput": true
    }
  }
}
```

## Запуск

```powershell
pwsh -NoProfile -File mcp/src/servers/McpWPCLIServer.ps1
```
