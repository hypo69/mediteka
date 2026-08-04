# McpSTDIOServer.ps1

**Файл:** `mcp/src/servers/McpSTDIOServer.ps1`  
**Протокол:** MCP STDIO (JSON-RPC 2.0)  
**Версия:** 1.1.5  
**Требования:** PowerShell 7.0+

## Назначение

Выполняет произвольные PowerShell скрипты через MCP протокол. Используется как STDIO сервер для Claude Desktop и других MCP клиентов.

## Инструменты

| Инструмент | Описание |
|---|---|
| `run-script` | Выполнить PowerShell скрипт с параметрами |

### run-script

| Параметр | Тип | Обязательный | Описание |
|---|---|---|---|
| `script` | string | ✅ | PowerShell код для выполнения |
| `parameters` | object | — | Параметры для скрипта |
| `workingDirectory` | string | — | Рабочая директория |
| `timeoutSeconds` | integer | — | Таймаут (1–3600, по умолчанию 300) |

## Конфигурация

Файл: `mcp/src/config/mcp-powershell-stdio.config.json`

```json
{
  "ServerConfig": {
    "Name": "PowerShell Script Runner",
    "MaxExecutionTime": 300,
    "Security": {
      "BlockDangerousCommands": false,
      "MaxOutputSize": 10000
    }
  }
}
```

## Запуск

```powershell
pwsh -NoProfile -File mcp/src/servers/McpSTDIOServer.ps1
```

## Конфигурация Claude Desktop

```json
{
  "mcpServers": {
    "powershell": {
      "command": "pwsh",
      "args": ["-NoProfile", "-File", "C:/path/to/mcp/src/servers/McpSTDIOServer.ps1"]
    }
  }
}
```
