# stop

> FastAPI Foundry Stop

## Description

Stops all FastAPI Foundry processes launched in silent mode
(via autostart.ps1 / Task Scheduler).
Stops in order:
1. FastAPI server  — via %TEMP%\fastapi-foundry.pid
2. llama.cpp       — via port from config.json (llama_cpp.port)
3. MkDocs          — via port from config.json (docs_server.port)
Foundry Local is intentionally NOT stopped — it is a system service.
Examples:
powershell -ExecutionPolicy Bypass -File .\stop.ps1
powershell -ExecutionPolicy Bypass -File .\stop.ps1 -StopFoundry
File: stop.ps1
Project: Ai Assistant (Docker)
Version: 0.6.1
Author: hypo69
Copyright: © 2026 hypo69
=============================================================================

## Examples

```powershell
powershell -ExecutionPolicy Bypass -File .\stop.ps1
powershell -ExecutionPolicy Bypass -File .\stop.ps1 -StopFoundry
File: stop.ps1
Project: Ai Assistant (Docker)
Version: 0.6.1
Author: hypo69
Copyright: © 2026 hypo69
=============================================================================
```

## Source

`stop.ps1`

