# McpHttpsServer.ps1

**Файл:** `mcp/src/servers/McpHttpsServer.ps1`  
**Протокол:** HTTP (System.Net.HttpListener)  
**Порт по умолчанию:** 8090  
**Версия:** 1.1.2  
**Требования:** PowerShell 7.0+

## Назначение

HTTP-версия MCP сервера для выполнения PowerShell скриптов. Принимает POST-запросы с JSON-RPC телом, возвращает JSON-ответы. Подходит для интеграций, где STDIO недоступен.

## Инструменты

| Инструмент | Описание |
|---|---|
| `run-script` | Выполнить PowerShell скрипт с параметрами |

Параметры инструмента идентичны [McpSTDIOServer](mcp-stdio.md).

## Запуск

```powershell
pwsh -NoProfile -File mcp/src/servers/McpHttpsServer.ps1 -Port 8090 -ServerHost localhost
```

## Конфигурация

Файл: `mcp/src/config/Config-McpHTTPS.json`

```json
{
  "Http": {
    "Port": 8090,
    "Host": "localhost",
    "MaxConcurrentRequests": 10
  },
  "MaxExecutionTime": 300
}
```

## Пример запроса

```bash
curl -X POST http://localhost:8090/ \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"run-script","arguments":{"script":"Get-Date"}}}'
```
