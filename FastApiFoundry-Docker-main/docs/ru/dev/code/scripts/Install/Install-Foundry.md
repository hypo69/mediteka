# Install Foundry

**Файл:** `scripts/Install/Install-Foundry.ps1`  
**Тип:** `.ps1`

---

-*- coding: utf-8 -*-
=============================================================================
Process Name: Установщик Microsoft Foundry Local
=============================================================================
Description:
Устанавливает Microsoft Foundry Local CLI через winget.
После установки запускает сервис и предлагает скачать модель.

Examples:
powershell -ExecutionPolicy Bypass -File .\scripts\Install\Install-Foundry.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\Install\Install-Foundry.ps1 -Model "qwen3-0.6b-generic-cpu:4"

File: scripts\Install\Install-Foundry.ps1
Project: AI Assistant (ai_assist)
Version: 0.7.1
Changes in 0.7.1:
- Обновлён заголовок и проект
- Комментарии переведены на русский
Author: hypo69
Copyright: © 2024 - 2026 hypo69
License: MIT
=============================================================================

### `Test-WingetAvailable`

### `Ensure-Winget`


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
