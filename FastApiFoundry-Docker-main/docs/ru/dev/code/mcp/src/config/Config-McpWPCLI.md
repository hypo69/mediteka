# Config Mcpwpcli

**Файл:** `mcp/src/config/Config-McpWPCLI.json`  
**Тип:** `.json`

---

| Ключ | Тип | Значение |
|---|---|---|
| `ServerConfig` | `dict` | объект: `Name`, `Version`, `Description`, `MaxExecutionTime`, `LogLevel` |

**Полная структура:**

```json
{
  "ServerConfig": {
    "Name": "WordPress CLI MCP Server",
    "Version": "1.2.1",
    "Description": "Выполняет команды WP-CLI через MCP протокол",
    "MaxExecutionTime": 300,
    "LogLevel": "INFO",
    "Security": {
      "EnableScriptValidation": false,
      "MaxOutputSize": 10000
    },
    "Logging": {
      "LogFile": "mcp-wordpress-server.log",
      "DetailedLogging": false
    },
    "WordPress": {
      "DefaultPath": "",
      "AutoDetectPath": true,
      "ForceJsonOutput": true
    }
  }
}
```

---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
