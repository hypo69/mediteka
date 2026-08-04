# Settings

**Файл:** `mcp/settings.json`  
**Тип:** `.json`

---

| Ключ | Тип | Значение |
|---|---|---|
| `mcpServers` | `dict` | объект: `powershell-stdio`, `powershell-https`, `wordpress-cli`, `local-models`, `huggingface` |
| `disabledServers` | `dict` | объект: `_note`, `powershell-huggingface-ps` |

**Полная структура:**

```json
{
  "mcpServers": {
    "powershell-stdio": {
      "command": "pwsh",
      "args": [
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        "./mcp/src/servers/McpSTDIOServer.ps1"
      ],
      "envFile": "./.env",
      "description": "PowerShell STDIO сервер — выполнение команд на локальной машине"
    },
    "powershell-https": {
      "command": "pwsh",
      "args": [
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        "./mcp/src/servers/McpHttpsServer.ps1",
        "-Port",
        "8090",
        "-ServerHost",
        "localhost",
        "-ConfigFile",
        "./mcp/src/config/Config-McpHTTPS.json"
      ],
      "envFile": "./.env",
      "description": "PowerShell HTTPS REST API сервер на порту 8090"
    },
    "wordpress-cli": {
      "command": "pwsh",
      "args": [
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        "./mcp/src/servers/McpWPCLIServer.ps1",
        "-ConfigFile",
        "./mcp/src/config/Config-McpWPCLI.json"
      ],
      "envFile": "./.env",
      "description": "WordPress CLI сервер для управления WP сайтами"
    },
    "local-models": {
      "command": "python",
      "args": [
        "./mcp/src/servers/local_models_mcp.py"
      ],
      "env": {
        "FASTAPI_BASE_URL": "http://localhost:9696"
      },
      "description": "Локальные AI модели через FastAPI Foundry (Foundry, llama.cpp, Ollama, HuggingFace)"
    },
    "huggingface": {
      "command": "python",
      "args": [
        "./mcp/src/servers/huggingface_mcp.py"
      ],
      "env": {
        "HF_TOKEN": "${HF_TOKEN}"
      },
      "description": "HuggingFace Inference API для генерации текста"
    },
    "docs-deploy": {
      "command": "python",
      "args": [
        "./mcp/src/servers/docs_deploy_mcp.py"
      ],
      "env": {
        "FTP_HOST": "${FTP_HOST}",
        "FTP_USER": "${FTP_USER}",
        "FTP_PASSWORD": "${FTP_PASSWORD}",
        "FTP_PORT": "${FTP_PORT}",
        "FTP_DOCS_RU": "${FTP_DOCS_RU}",
        "FTP_DOCS_EN": "${FTP_DOCS_EN}"
      },
      "description": "Deploy MkDocs documentation (site/ru, site/en) to FTP server"
    },
    "windows-os": {
      "command": "python",
      "args": [
        "./mcp/src/servers/windows_os_mcp.py"
      ],
      "description": "Windows OS диагностика: процессы, службы, диск, сеть, автозагрузка"
    },
    "ftp": {
      "command": "python",
      "args": [
        "./mcp/src/servers/ftp_mcp.py"
      ],
      "env": {
        "FTP_HOST": "${FTP_HOST}",
        "FTP_USER": "${FTP_USER}",
        "FTP_PASSWORD": "${FTP_PASSWORD}",
        "FTP_PORT": "${FTP_PORT}"
      },
      "description": "FTP операции: список файлов, загрузка, скачивание, удаление, переименование"
    },
    "github": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-github"
      ],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "$
```

---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
