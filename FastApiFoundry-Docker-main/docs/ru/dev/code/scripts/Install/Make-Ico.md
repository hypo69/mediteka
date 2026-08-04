# Make Ico

**Файл:** `scripts/Install/Make-Ico.ps1`  
**Тип:** `.ps1`

---

-*- coding: utf-8 -*-
=============================================================================
Process Name: Конвертер PNG в ICO
=============================================================================
Description:
Конвертирует assets/icons/icon16.png + icon48.png + icon128.png
в единый файл icon.ico в корне проекта.
Использует .NET System.Drawing — внешние инструменты не нужны.

Examples:
powershell -ExecutionPolicy Bypass -File .\scripts\Install\Make-Ico.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\Install\Make-Ico.ps1 -ProjectRoot "D:\project"

File: scripts\Install\Make-Ico.ps1
Project: AI Assistant (ai_assist)
Version: 0.7.1
Changes in 0.7.1:
- Обновлён заголовок и проект
- Комментарии переведены на русский
Author: hypo69
Copyright: © 2024 - 2026 hypo69
License: MIT
=============================================================================

### `ConvertTo-Ico`


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
