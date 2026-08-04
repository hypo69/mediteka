# Invoke Qastart

**Файл:** `tests/Invoke-QaStart.ps1`  
**Тип:** `.ps1`

---

-*- coding: utf-8 -*-
=============================================================================
Process Name: QA - Stop All Services
=============================================================================
Description:
Stops all AI Assistant services to produce a clean state before QA testing.
Run this before qa-install.ps1 or before running the test suite.

Stops in order:
1. FastAPI server  — PID file or port 9696
2. llama.cpp       — port 9780
3. MkDocs          — port 9697
4. Foundry Local   — foundry service stop

Examples:
powershell -ExecutionPolicy Bypass -File .\tests\qa-start.ps1
powershell -ExecutionPolicy Bypass -File .\tests\qa-start.ps1 -KeepFoundry

File: tests\qa-start.ps1
Project: AI Assistant (ai_assist)
Version: 0.7.1
Author: hypo69
Copyright: © 2026 hypo69
=============================================================================

### `Stop-ServiceByPort`

### `Stop-ServiceByPidFile`

### `Get-PortsFromConfig`


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
