# Mcp Powershell Stdio.Config

**Файл:** `mcp/src/config/mcp-powershell-stdio.config.json`  
**Тип:** `.json`

---

| Ключ | Тип | Значение |
|---|---|---|
| `ServerConfig` | `dict` | объект: `Name`, `Version`, `Description`, `MaxExecutionTime`, `LogLevel` |

**Полная структура:**

```json
{
  "ServerConfig": {
    "Name": "PowerShell Script Runner",
    "Version": "1.1.1",
    "Description": "Выполняет PowerShell скрипты через MCP протокол",
    "MaxExecutionTime": 300,
    "LogLevel": "INFO",
    "Security": {
      "EnableScriptValidation": false,
      "BlockDangerousCommands": false,
      "RestrictedCommands": [
        "Remove-Item.*C:\\\\Windows",
        "Remove-Item.*C:\\\\Program Files",
        "Format-Volume",
        "Stop-Computer",
        "Restart-Computer",
        "Remove-Item.*HKLM:",
        "New-ItemProperty.*HKLM:",
        "Set-ItemProperty.*HKLM:",
        "Remove-ItemProperty.*HKLM:"
      ],
      "AllowedModules": [
        "Microsoft.PowerShell.*",
        "PackageManagement",
        "PowerShellGet",
        "PSReadLine",
        "ThreadJob"
      ],
      "MaxOutputSize": 10000,
      "MaxScriptLength": 50000
    },
    "Logging": {
      "LogFile": "mcp-powershell-server.log",
      "DetailedLogging": false
    },
    "Paths": {
      "AllowedPaths": [
        "C:\\Scripts\\",
        "C:\\Tools\\",
        "C:\\Temp\\"
      ]
    }
  }
}
```

---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
