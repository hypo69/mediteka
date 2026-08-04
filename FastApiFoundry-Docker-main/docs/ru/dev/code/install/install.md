# install.ps1

Главный установщик AI Assistant. Точка входа для первоначальной настройки проекта.

**Файл:** `install.ps1`  
**Запуск:** `powershell -ExecutionPolicy Bypass -File .\install.ps1`

---

## Назначение

Последовательно выполняет все шаги установки:

1. Проверка предварительных требований (место на диске, права записи)
2. Поиск Python 3.11+ или распаковка из `bin\Python-3.11.9.zip`
3. Создание виртуального окружения `venv\`
4. Установка зависимостей из `requirements.txt`
5. Интерактивная установка опциональных пакетов (QA, Google, MkDocs, MCP)
6. Установка Chromium for Testing (опционально)
7. Установка RAG-зависимостей (`torch`, `sentence-transformers`, `faiss`) через `scripts/Install/install_rag_deps.py` (автоматический выбор CPU/GPU).
8. Установка Tesseract OCR
9. Создание `.env` из `.env.example`
10. Создание `config.json` из `config.json.example`
11. Создание директории `logs/`
12. **Инициализация баз данных** (`install\Init-Databases.py`)
13. Распаковка llama.cpp из `bin\llama-*.zip`
14. Установка Microsoft Foundry Local (через winget)
15. Проверка и установка LM Studio через `install\Install-LMStudio.ps1`
16. Загрузка моделей по умолчанию (при первой установке)
17. Создание ярлыков на рабочем столе
18. Финальный аудит безопасности (`pip-audit`)

---

## Параметры

| Параметр | Тип | Описание |
|---|---|---|
| `-Force` | switch | Пересоздать venv без запроса |
| `-SkipRag` | switch | Пропустить установку RAG-зависимостей |
| `-SkipTesseract` | switch | Пропустить установку Tesseract OCR |
| `-SkipLMStudio` | switch | Пропустить проверку и установку LM Studio |
| `-NoGui` | switch | Пропустить GUI-установщик |
| `-Mode` | string | Режим: `prod` \| `qa` \| `debug` \| `qa+debug` |

---

## Примеры

```powershell
# Стандартная установка
powershell -ExecutionPolicy Bypass -File .\install.ps1

# Принудительное пересоздание venv
powershell -ExecutionPolicy Bypass -File .\install.ps1 -Force

# Без RAG и Tesseract (быстрая установка)
powershell -ExecutionPolicy Bypass -File .\install.ps1 -SkipRag -SkipTesseract

# Без LM Studio
powershell -ExecutionPolicy Bypass -File .\install.ps1 -SkipLMStudio

# Режим отладки
powershell -ExecutionPolicy Bypass -File .\install.ps1 -Mode debug
```

---

## Влияние параметра -Mode

Параметр `-Mode` определяет конфигурацию среды и влияет на шаг `Step-Backends.ps1`:

*   **`prod` (по умолчанию):** Стандартная установка для пользователя. Оптимизированные веса моделей, отключены инструменты разработки.
*   **`debug`:** Устанавливает дополнительные утилиты для отладки, включает расширенное логирование в `config.json` и настраивает локальные пути для удобной правки кода.
*   **`qa`:** Режим для тестировщиков. Автоматически устанавливает зависимости из `requirements-qa.txt` (Ruff, Mypy, Pytest) и настраивает окружение для запуска автоматических тестов.
*   **`qa+debug`:** Комбинированный режим для разработчиков, работающих над качеством кода.

Значение режима сохраняется в файл `MODE` в корне проекта, чтобы последующие запуски `start.ps1` знали, в каком окружении работает система.

---

## Контроль качества (QA)
Запуск полного цикла проверок (линтеры, типы, Python-тесты и PowerShell Pester-тесты) осуществляется через:
`powershell scripts/Invoke-Qa.ps1`

---

## Вспомогательные функции

### Test-PreFlightRequirements

Проверяет наличие свободного места (≥ 5 ГБ) и права записи во все директории из `config.json → directories`.

### Resolve-Mode

Нормализует строку режима к одному из канонических значений: `prod | qa | debug | qa+debug`.

### Get-ModeFromFile

Читает активный режим из файла `MODE` в корне проекта.

### Stop-VenvProcesses

Останавливает процессы, удерживающие блокировки на файлах venv (порты 9696, 9697).

### Ensure-LMStudioConfig

Гарантирует наличие секции `lmstudio` в `config.json`:
`base_url`, `api_key`, `default_model`, `request_timeout_sec`.

Установка самого приложения LM Studio намеренно вынесена в
`install\Install-LMStudio.ps1`; главный установщик только вызывает этот
специализированный скрипт внутри `try/catch`. Ошибка LM Studio не валит весь
`install.ps1`: она записывается в `logs\aiassistant-install.log`, после чего
установка остальных компонентов продолжается.

### Write-InstallLog

Пишет события установки в `logs\aiassistant-install.log`. Имя файла начинается
с `aiassistant-`, поэтому существующий Logs API (`/api/v1/logs/files`) и вкладка
**Logs** в static UI показывают его без отдельной доработки интерфейса.

---

## Связанные файлы

- `install\Init-Databases.py` — инициализация SQLite баз данных
- [`install\Install-Foundry.ps1`](Install-Foundry.md) — установка Foundry Local
- [`install\Install-LMStudio.ps1`](Install-LMStudio.md) — установка LM Studio
- [`install\Install-Tesseract.ps1`](Install-Tesseract.md) — установка Tesseract OCR
- [`install\Install-Shortcuts.ps1`](Install-Shortcuts.md) — ярлыки на рабочем столе
