# Create Requirements

**Файл:** `scripts/Create-Requirements.ps1`  
**Тип:** `.ps1`

---

-*- coding: utf-8 -*-
=============================================================================
Process Name: Create requirements.txt
=============================================================================
Description:
Generates requirements.txt using one of two strategies:
freeze   — full pip freeze snapshot of the active venv
pipreqs  — only packages actually imported in source code (auto-installs pipreqs)

Examples:
.\create_requirements.ps1 -Mode pipreqs
.\create_requirements.ps1 -Mode freeze -ProjectPath . -VenvPath venv

File: scripts/create_requirements.ps1
Project: Ai Assistant (Docker)
Version: 0.6.1
Author: hypo69
Copyright: © 2026 hypo69
=============================================================================

### `Write-Log`

### `Test-CommandExists`

### `Invoke-ActivateVenv`

### `Invoke-Freeze`

### `Invoke-Pipreqs`


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
