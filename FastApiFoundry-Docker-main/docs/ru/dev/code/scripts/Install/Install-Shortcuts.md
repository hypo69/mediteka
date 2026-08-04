# Install Shortcuts

**Файл:** `scripts/Install/Install-Shortcuts.ps1`  
**Тип:** `.ps1`

---

-*- coding: utf-8 -*-
=============================================================================
Process Name: Создание ярлыков на рабочем столе
=============================================================================
Description:
Создаёт два ярлыка Windows на рабочем столе для запуска AI Assistant:
1. "AI Assistant"          — консольное окно через start.ps1
2. "AI Assistant (Silent)" — скрытое окно через autostart.ps1
Источник иконки: assets\icons\icon128.png (конвертируется автоматически).

Examples:
powershell -ExecutionPolicy Bypass -File .\scripts\Install\Install-Shortcuts.ps1

File: scripts\Install\Install-Shortcuts.ps1
Project: AI Assistant (ai_assist)
Version: 0.7.1
Changes in 0.7.1:
- Обновлён заголовок и проект
- Комментарии переведены на русский
Author: hypo69
Copyright: © 2024 - 2026 hypo69
License: MIT
=============================================================================

### `Ensure-Icon`

### `New-AppShortcut`


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
