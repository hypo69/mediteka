# Build Exes

**Файл:** `scripts/Build-Exes.ps1`  
**Тип:** `.ps1`

---

-*- coding: utf-8 -*-
=============================================================================
Process Name: EXE Wrapper Generator
=============================================================================
Description:
Compiles tiny C# wrapper programs into .exe files that launch PowerShell
scripts when double-clicked. Uses the built-in Windows C# compiler (csc.exe)
so no external tools are required.
Produces install.exe (wraps install.ps1) and launcher.exe (wraps launcher.ps1).

Examples:
powershell -ExecutionPolicy Bypass -File .\build_exes.ps1

File: scripts/build_exes.ps1
Project: Ai Assistant (Docker)
Version: 0.4.1
Author: hypo69
Copyright: © 2026 hypo69
=============================================================================

### `Build-Wrapper`


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
