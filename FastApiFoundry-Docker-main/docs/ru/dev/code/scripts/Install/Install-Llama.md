# Install Llama

**Файл:** `scripts/Install/Install-Llama.ps1`  
**Тип:** `.ps1`

---

-*- coding: utf-8 -*-
=============================================================================
Process Name: Настройка llama.cpp
=============================================================================
Description:
Распаковывает Windows-бинарник llama.cpp из bin\llama-*.zip
(если ещё не распакован), затем записывает путь к директории моделей
в config.json (секции directories.models и llama_cpp.model_path).

Examples:
powershell -ExecutionPolicy Bypass -File .\scripts\Install\Install-Llama.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\Install\Install-Llama.ps1 -ModelsDir "D:\models"

File: scripts\Install\Install-Llama.ps1
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
