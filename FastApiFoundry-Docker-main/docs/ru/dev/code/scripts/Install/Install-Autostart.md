# Install Autostart

**Файл:** `scripts/Install/Install-Autostart.ps1`  
**Тип:** `.ps1`

---

-*- coding: utf-8 -*-
=============================================================================
Process Name: Регистрация автозапуска в Планировщике заданий Windows
=============================================================================
Description:
Создаёт задание в Windows Task Scheduler, которое запускает autostart.ps1
при входе пользователя (скрытое окно, вывод в лог).
Требует запуска от имени администратора.

Examples:
powershell -ExecutionPolicy Bypass -File .\scripts\Install\Install-Autostart.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\Install\Install-Autostart.ps1 -Uninstall

File: scripts\Install\Install-Autostart.ps1
Project: AI Assistant (ai_assist)
Version: 0.7.1
Changes in 0.7.1:
- Обновлён заголовок и проект
- Комментарии переведены на русский
Author: hypo69
Copyright: © 2024 - 2026 hypo69
License: MIT
=============================================================================


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
