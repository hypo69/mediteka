# Update Project

**Файл:** `scripts/Update-Project.ps1`  
**Тип:** `.ps1`

---

-*- coding: utf-8 -*-
=============================================================================
Process Name: FastAPI Foundry - Update Checker
=============================================================================
Description:
Checks GitHub for a newer release tag and offers to update.
Compares the current local tag (VERSION file or git describe) against
the latest tag on the remote. If a newer tag exists, pulls it and
re-runs install.ps1 to refresh dependencies.

Examples:
powershell -ExecutionPolicy Bypass -File .\scripts\Update-Project.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\Update-Project.ps1 -Silent
powershell -ExecutionPolicy Bypass -File .\scripts\Update-Project.ps1 -Force

File: scripts/Update-Project.ps1
Project: Ai Assistant (Docker)
Version: 0.6.0
Author: hypo69
Copyright: © 2026 hypo69
=============================================================================

### `Get-LocalVersion`

### `Get-RemoteLatestTag`

### `Compare-Versions`

### `Invoke-Update`


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
