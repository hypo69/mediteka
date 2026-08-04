# Get Foundryutils

**Файл:** `scripts/Get-FoundryUtils.ps1`  
**Тип:** `.ps1`

---

-*- coding: utf-8 -*-
=============================================================================
Process Name: Foundry Utility Functions
=============================================================================
Description:
Reusable Foundry helper functions extracted from start.ps1.
Dot-source this file to get utility functions WITHOUT launching the server.

Functions:
Test-FoundryCli   — check if 'foundry' CLI is in PATH
Get-FoundryPort   — detect active Foundry inference port
Get-FoundryUrl    — return full base URL (http://127.0.0.1:PORT/v1/)

Examples:
. .\scripts\foundry-utils.ps1
Get-FoundryPort
Get-FoundryUrl

File: scripts/Get-FoundryUtils.ps1
Project: AI Assistant (ai_assist)
Version: 0.8.0
Changes in 0.8.0:
- Extracted from start.ps1 to allow dot-sourcing without side effects
Author: hypo69
Copyright: © 2026 hypo69
=============================================================================

### `Test-FoundryCli`

### `Get-FoundryPort`

### `Get-FoundryUrl`


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
