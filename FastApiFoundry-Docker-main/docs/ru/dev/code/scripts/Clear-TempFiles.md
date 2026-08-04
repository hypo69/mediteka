# Clear Tempfiles

**Файл:** `scripts/Clear-TempFiles.ps1`  
**Тип:** `.ps1`

---

-*- coding: utf-8 -*-
=============================================================================
Название процесса: FastAPI Foundry Smart Launcher (Умный запуск)
=============================================================================
Описание:
Основная точка входа для запуска сервера FastAPI Foundry.
При первом запуске — автоматическая установка зависимостей через install.ps1.
Загрузка переменных .env, обнаружение или запуск службы Foundry AI,
опциональный запуск серверов llama.cpp и MkDocs, финальный запуск FastAPI.

Примеры:
powershell -ExecutionPolicy Bypass -File .\start.ps1
powershell -ExecutionPolicy Bypass -File .\start.ps1 -Config config.json

File: start.ps1
Project: Ai Assistant
Package: FastApiFoundry
Version: 0.7.1
Author: hypo69
Copyright: © 2025 - 2026 hypo69
=============================================================================

### `Write-Log`

### `Load-EnvFile`

Активация виртуального окружения Python.
    Настройка путей для работы с pip и python внутри venv.
#>

# Активация виртуального окружения

$ActivateScript = "$Root\venv\Scripts\Activate

### `Get-LauncherConfig`

### `Test-FoundryCli`

Проверка доступности Foundry CLI.
    Поиск утилиты 'foundry' в системном PATH.

### `Get-FoundryPort`

Поиск TCP-порта службы инференса Foundry.
    Обнаружение активного порта Foundry AI.

Поиск процесса 'Inference

### `Ensure-LlamaBin`

Обеспечение актуальности бинарных файлов llama

### `Start-LlamaServer`

Запуск сервера llama


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
