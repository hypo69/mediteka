# Settings

**Файл:** `servers/wordpress-cli/.gemini/settings.json`  
**Тип:** `.json`

---

| Ключ | Тип | Значение |
|---|---|---|
| `mcpServers` | `dict` | объект: `powershell-stdio`, `wordpress-cli`, `github`, `sequential-thinking`, `pydoll` |
| `disabledServers` | `dict` | объект: `powershell-http` |

**Полная структура:**

```json
{
  "mcpServers": {
    "powershell-stdio": {
      "command": "pwsh",
      "args": [
        "-File",
        "C:/powershell/modules/mcp-powershell-server/src/servers/mcp-powershell-stdio.ps1"
      ],
      "env": {
        "POWERSHELL_EXECUTION_POLICY": "RemoteSigned"
      }
    },
    "wordpress-cli": {
      "command": "pwsh",
      "args": [
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        "C:/powershell/modules/mcp-powershell-server/src/servers/mcp-powershell-wordpress.ps1"
      ],
      "env": {
        "POWERSHELL_EXECUTION_POLICY": "RemoteSigned"
      }
    },
    "github": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-github"
      ],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
      }
    },
    "sequential-thinking": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-sequential-thinking"
      ]
    },
    "pydoll": {
      "command": "python",
      "args": [
        "-m",
        "pydoll_mcp.server"
      ],
      "env": {
        "PYDOLL_LOG_LEVEL": "INFO"
      }
    }
  },
  "disabledServers": {
    "powershell-http": {
      "command": "pwsh",
      "args": [
        "-File",
        "C:/powershell/modules/mcp-powershell-server/src/servers/mcp-powershell-https.ps1"
      ],
      "env": {
        "POWERSHELL_EXECUTION_POLICY": "RemoteSigned"
      }
    }
  }
}
```

---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
