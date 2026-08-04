# Install Models

**Файл:** `scripts/Install/Install-Models.ps1`  
**Тип:** `.ps1`

---

-*- coding: utf-8 -*-
=============================================================================
Process Name: Загрузка моделей по умолчанию
=============================================================================
Description:
Загружает модели по умолчанию для Foundry Local и HuggingFace.
Для llama.cpp: сканирует ~/.models на наличие .gguf-файлов
и позволяет выбрать модель по умолчанию для записи в config.json.
Запускается автоматически из install.ps1 при первой установке
или вручную в любое время.

Examples:
powershell -ExecutionPolicy Bypass -File .\scripts\Install\Install-Models.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\Install\Install-Models.ps1 -SkipFoundry
powershell -ExecutionPolicy Bypass -File .\scripts\Install\Install-Models.ps1 -SkipHuggingFace
powershell -ExecutionPolicy Bypass -File .\scripts\Install\Install-Models.ps1 -SkipLlama

File: scripts\Install\Install-Models.ps1
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
