# Install Lmstudio

**Файл:** `scripts/Install/Install-LMStudio.ps1`  
**Тип:** `.ps1`

---

-*- coding: utf-8 -*-
=============================================================================
Process Name: Установщик LM Studio
=============================================================================
Description:
Проверяет наличие LM Studio CLI (`lms`) и при согласии пользователя
устанавливает LM Studio официальной командой:
irm https://lmstudio.ai/install.ps1 | iex

Скрипт защищённо проверяет наличие Invoke-RestMethod / irm и
останавливается с объяснением, если PowerShell не поддерживает этот alias.

Examples:
powershell -ExecutionPolicy Bypass -File .\scripts\Install\Install-LMStudio.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\Install\Install-LMStudio.ps1 -SkipIfExists
powershell -ExecutionPolicy Bypass -File .\scripts\Install\Install-LMStudio.ps1 -DiagnosticsOnly

File: scripts\Install\Install-LMStudio.ps1
Project: AI Assistant (ai_assist)
=============================================================================

### `Get-LMStudioCliPath`

### `Assert-InvokeRestMethodAvailable`

### `Invoke-LMStudioOfficialInstall`


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
