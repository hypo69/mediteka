# Start Fastapi

**Файл:** `scripts/Start-Engine/Start-FastApi.ps1`  
**Тип:** `.ps1`

---

-*- coding: utf-8 -*-
=============================================================================
Process Name: Start FastAPI Server
=============================================================================
Description:
Stops previous FastAPI instance (by PID file), then starts run.py.
Waits for port to become available and opens browser.

Examples:
powershell -ExecutionPolicy Bypass -File .\scripts\Start-Engine\Start-FastApi.ps1 `
-Root D:\repos\FastApiFoundry-Docker -VenvPath D:\repos\...\venv\Scripts\python.exe

File: scripts/Start-Engine/Start-FastApi.ps1
Project: AI Assistant (ai_assist)
Version: 0.8.0
Author: hypo69
Copyright: © 2026 hypo69
=============================================================================


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
