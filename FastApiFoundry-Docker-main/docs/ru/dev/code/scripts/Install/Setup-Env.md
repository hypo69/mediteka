# Setup Env

**Файл:** `scripts/Install/Setup-Env.ps1`  
**Тип:** `.ps1`

---

-*- coding: utf-8 -*-
=============================================================================
Process Name: Настройка переменных окружения
=============================================================================
Description:
Интерактивный мастер создания или перезаписи файла .env.
Копирует .env.example как шаблон, затем запрашивает GitHub-данные,
API-ключи, URL Foundry и название окружения.
Опционально генерирует криптографически стойкие ключи автоматически.
Запускает check_env.py в конце для валидации конфигурации.

Examples:
powershell -ExecutionPolicy Bypass -File .\scripts\Install\Setup-Env.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\Install\Setup-Env.ps1 -Force
powershell -ExecutionPolicy Bypass -File .\scripts\Install\Setup-Env.ps1 -GenerateKeys

File: scripts\Install\Setup-Env.ps1
Project: AI Assistant (ai_assist)
Version: 0.7.1
Changes in 0.7.1:
- Обновлён заголовок и проект
- Комментарии переведены на русский
Author: hypo69
Copyright: © 2024 - 2026 hypo69
License: MIT
=============================================================================

### `Generate-SecureKey`


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
