# Install-Llama

> Настройка llama.cpp

## Description

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

## Examples

```powershell
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
```

## Source

`scripts/Install/Install-Llama.ps1`

