# Операционные скрипты

Все скрипты находятся в `scripts/` и запускаются из корня проекта.

## Список скриптов

| Скрипт | Назначение |
|---|---|
| `create_requirements.ps1` | Обновление `requirements.txt` (режимы: pipreqs, freeze) |
| `restart-mkdocs.ps1` | Перезапуск сервера документации MkDocs |
| `llama-start.ps1` | Запуск `llama-server.exe` с выбранной GGUF моделью |
| `load-model.ps1` | Загрузка модели в Foundry через CLI |
| `unload-model.ps1` | Выгрузка модели из Foundry |
| `list-models.ps1` | Список доступных и загруженных моделей Foundry |
| `download-model.ps1` | Скачивание модели через Foundry CLI |
| `hf-download-model.ps1` | Скачивание модели с HuggingFace Hub |
| `hf-models.ps1` | Поиск и просмотр моделей на HuggingFace |
| `service-status.ps1` | Проверка статуса Foundry и FastAPI |
| `Monitor-DiskSpace.ps1` | Проверка места на диске с авто-очисткой |
| `Clear-TempFiles.ps1` | Удаление кэшей, временных файлов и мусора |
| `Archive-RagIndices.ps1` | Архивирование папок индексов RAG в ZIP |
| `Restore-RagIndex.ps1` | Восстановление индекса RAG из архива |
| `Update-Project.ps1` | Проверка обновлений из GitHub и переключение на новый тег |
| `generate-ps-docs.ps1` | Генерация Markdown-документации из PowerShell comment-based help |
| `build_exes.ps1` | Сборка `install.exe` и `launcher.exe` |

---

## create_requirements.ps1

Обновляет `requirements.txt` одним из трёх способов.

```powershell
# Рекомендуемый: только реально используемые пакеты
powershell -ExecutionPolicy Bypass -File .\scripts\create_requirements.ps1 -Mode pipreqs

# Полный снимок venv
powershell -ExecutionPolicy Bypass -File .\scripts\create_requirements.ps1 -Mode freeze
```

### Режимы

| Режим | Описание |
|---|---|
| `pipreqs` | Анализирует `import` в `src/` и генерирует минимальный файл. Автоустанавливает `pipreqs` если нет. |
| `freeze` | `pip freeze` — полный снимок всего venv с зафиксированными версиями. |

### Параметры

| Параметр | По умолчанию | Описание |
|---|---|---|
| `-Mode` | `pipreqs` | Режим работы |
| `-ProjectPath` | корень проекта | Путь к проекту |
| `-VenvPath` | `<корень>\venv` | Путь к venv |

!!! tip "Рекомендуемый workflow"
    После установки нового пакета используйте `freeze`, чтобы зафиксировать точные версии:
    ```powershell
    venv\Scripts\pip.exe install some-package
    powershell -ExecutionPolicy Bypass -File .\scripts\create_requirements.ps1 -Mode freeze
    git add requirements.txt && git commit -m "deps: add some-package"
    ```

---

## restart-mkdocs.ps1

Останавливает текущий процесс MkDocs и запускает новый.

Порт читается из `config.json → docs_server.port` (по умолчанию `9697`).

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\restart-mkdocs.ps1
```

**Что делает:**

1. Читает порт из `config.json`
2. Находит процесс на этом порту через `Get-NetTCPConnection` и убивает его
3. Ждёт 800 мс (освобождение порта)
4. Запускает `mkdocs serve` в новом окне через `venv\Scripts\python.exe`

---

## llama-start.ps1

Запускает `llama-server.exe` из `bin/` с моделью, указанной в `.env`.

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\llama-start.ps1
```

Переменные `.env`:

```env
LLAMA_MODEL_PATH=D:\models\qwen2.5-0.5b-q4_k_m.gguf
LLAMA_SERVER_PATH=.\bin\llama-b8802-bin-win-cpu-x64\llama-server.exe
```

---

## load-model.ps1 / unload-model.ps1

Загрузка и выгрузка модели в Microsoft Foundry Local через CLI.

```powershell
.\scripts\load-model.ps1 -ModelId "qwen3-0.6b-generic-cpu:4:4"
.\scripts\unload-model.ps1 -ModelId "qwen3-0.6b-generic-cpu:4:4"
```

---

## hf-download-model.ps1

Скачивание GGUF модели с HuggingFace Hub.

```powershell
.\scripts\hf-download-model.ps1 -Repo "bartowski/gemma-7b-it-GGUF" -LocalDir "D:\models"
```

Требует `HF_TOKEN` в `.env` для закрытых моделей (Gemma, Llama).

---

## service-status.ps1

Проверяет статус Foundry и FastAPI, выводит порты и состояние процессов.

```powershell
.\scripts\service-status.ps1
```

---

## Monitor-DiskSpace.ps1

Проверяет свободное место на диске перед запуском системы. Автоматически вызывается в `start.ps1` (Этап -1).

**Логика работы:**
1. Если свободного места меньше порога (по умолчанию 5 ГБ), запускает `Clear-TempFiles.ps1`.
2. Передает значение `-RetentionDays` в скрипт очистки для управления жизненным циклом RAG-индексов.
3. Если после очистки места все еще недостаточно, отправляет уведомление в Telegram администратору.

---

## Clear-TempFiles.ps1

Удаляет безопасные для удаления временные данные: папки `__pycache__`, содержимое `temp`/`tmp` (исключая `venv`), файлы `*.tmp`, `*.bak` и старые логи. Поддерживает настройку срока хранения индексов.
**Особенности:**
- **Очистка RAG:** Автоматически находит индексы в `~/.aiassistant/rag/`, не изменявшиеся заданное количество дней (параметр `-RetentionDays`, по умолчанию 60).
- **Безопасность:** Перед удалением индекса вызывается `Archive-RagIndices.ps1` для создания резервной копии.

---

## Archive-RagIndices.ps1

Служебный скрипт для упаковки содержимого папки индекса RAG в ZIP-архив. Архивы сохраняются в директорию `archive/rag_indices/` в корне проекта с меткой времени.

---

## Restore-RagIndex.ps1

Позволяет восстановить ранее архивированный индекс RAG. Распаковывает содержимое ZIP-файла обратно в директорию профилей `~/.aiassistant/rag/`. Полезен для возврата к работе с редко используемыми базами знаний, которые были автоматически архивированы системой очистки места.

---

## Update-Project.ps1

Проверяет GitHub на наличие нового релиза и предлагает обновиться. Автоматически запускается из `start.ps1`.

```powershell
# Интерактивный режим
powershell -ExecutionPolicy Bypass -File .\scripts\Update-Project.ps1

# Без подтверждения (авто-принятие)
powershell -ExecutionPolicy Bypass -File .\scripts\Update-Project.ps1 -Silent

# Принудительное обновление даже если версия актуальна
powershell -ExecutionPolicy Bypass -File .\scripts\Update-Project.ps1 -Force
```

**Что делает:**

1. Читает текущую версию из файла `VERSION` или `git describe --tags`
2. Делает `git fetch --tags` и находит последний тег на remote
3. Если есть обновление — предлагает переключиться (`git checkout <tag>`)
4. Запускает `install.ps1` для обновления зависимостей

| Параметр | Описание |
|---|---|
| `-Silent` | Авто-принятие обновления без вопроса |
| `-Force` | Обновить даже если версия уже актуальна |

!!! note
    Требует `git` в `PATH`. Если проект запущен не из git-репозитория, проверка пропускается автоматически.

---

## generate-ps-docs.ps1

Генерирует Markdown-документацию из PowerShell comment-based help (блоки `<# .SYNOPSIS .DESCRIPTION #>`). Используется в GitHub Actions workflow `deploy-docs.yml`.

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\generate-ps-docs.ps1
```

**Что делает:**

1. Сканирует `mcp-powershell-servers/src/servers/` и `scripts/` на все `.ps1` файлы
2. Извлекает `.SYNOPSIS`, `.DESCRIPTION`, `.NOTES` из comment-based help
3. Генерирует `docs/ru/dev/powershell/<name>.md` для каждого скрипта
4. Создаёт `docs/ru/dev/powershell/index.md` со ссылками на все страницы

!!! note
    Чтобы скрипт попал в документацию, добавьте в него блок `<# .SYNOPSIS ... #>`.

---

## build_exes.ps1

Собирает `install.exe` и `launcher.exe` — обёртки над PowerShell скриптами для запуска двойным кликом. Использует встроенный компилятор `csc.exe` (.NET Framework 4), внешние инструменты не нужны.

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build_exes.ps1
```

**Что делает:**

1. Находит `csc.exe` в `C:\Windows\Microsoft.NET\Framework64\v4.0.30319\`
2. Генерирует C# обёртку, которая находит `.ps1` рядом с `.exe` и запускает его через `powershell.exe -ExecutionPolicy Bypass`
3. Компилирует `install.exe` (обёртка `install.ps1`) и `launcher.exe` (обёртка `launcher.ps1`)
4. Кладёт файлы в корень проекта

!!! warning
    Требует .NET Framework 4 (есть на любом Windows 7+). Не требует Visual Studio или MSBuild.

---

## Разбор кода install/

Все скрипты в `install/` следуют единому стандарту оформления.

### Структура каждого скрипта

```
install/<script>.ps1
  ├─ Заголовок файла (hypo69 header)
  ├─ param() — параметры
  ├─ $ErrorActionPreference = 'Stop'
  ├─ Константы ($UPPER_SNAKE_CASE)
  ├─ Функции (Verb-Noun + docstring)
  └─ # --- main --- (точка входа)
```

### Стандарт docstring для функций

Все публичные функции документируются по единому шаблону.
Порядок секций фиксирован и не меняется:

```powershell
function Verb-Noun {
    <#
    .SYNOPSIS
        Short description — одна строка, суть функции.
    .DESCRIPTION
        Long description — опционально, многострочное пояснение.

        Args:
            $ParamName (type) — описание, ограничения, значение по умолчанию.

        Returns:
            type — что возвращается и при каком условии.

        Exceptions:
            ErrorType — когда выбрасывается.
    .EXAMPLE
        Verb-Noun -Param value
        # ожидаемый результат или побочный эффект
    #>
    param([string]$ParamName)
    ...
}
```

**Правила:**

- `.SYNOPSIS` — обязательна, одна строка без точки в конце
- `Args:` / `Returns:` / `Exceptions:` — внутри `.DESCRIPTION`, опускаются если неприменимы
- `.EXAMPLE` — минимум один на каждую публичную функцию
- Запрещены: `.PARAMETER`, `.OUTPUTS`, `.NOTES`

### Примеры из install/

**install-tesseract.ps1** — три функции с разными сигнатурами:

```powershell
function Test-TesseractInstalled {
    <#
    .SYNOPSIS
        Checks whether tesseract.exe is reachable via PATH or at the default install path.
    .DESCRIPTION
        Returns:
            bool — True if found.
    .EXAMPLE
        Test-TesseractInstalled
        # Returns $true on a machine with Tesseract in PATH
    #>
    if (Get-Command tesseract -ErrorAction SilentlyContinue) { return $true }
    return Test-Path $TESSERACT_EXE
}

function Write-TesseractToConfig {
    <#
    .SYNOPSIS
        Writes or updates text_extractor.tesseract_cmd in config.json.
    .DESCRIPTION
        Args:
            $ExePath (string) — full path to tesseract.exe.
    .EXAMPLE
        Write-TesseractToConfig -ExePath 'C:\Program Files\Tesseract-OCR\tesseract.exe'
        # Updates config.json: text_extractor.tesseract_cmd
    #>
    param([string]$ExePath)
    ...
}

function Install-Tesseract {
    <#
    .SYNOPSIS
        Downloads the Tesseract installer and runs it silently.
    .DESCRIPTION
        Returns:
            bool — True if installation succeeded.
    .EXAMPLE
        $ok = Install-Tesseract
        if ($ok) { Add-TesseractToPath }
    #>
    ...
}
```

**install-shortcuts.ps1** — функция с несколькими параметрами:

```powershell
function New-AppShortcut {
    <#
    .SYNOPSIS
        Creates a .lnk shortcut on the Desktop.
    .DESCRIPTION
        Args:
            $Name (string) — shortcut filename without .lnk.
            $Arguments (string) — PowerShell arguments string.
            $WindowStyle (int) — 1 = normal, 7 = minimized/hidden.
            $Description (string) — tooltip text shown on hover.
    .EXAMPLE
        New-AppShortcut -Name 'AI Assistant' -Arguments "-File start.ps1" -WindowStyle 1 -Description 'Launch'
        # Creates AI Assistant.lnk on the Desktop
    #>
    param (
        [string]$Name,
        [string]$Arguments,
        [int]$WindowStyle,
        [string]$Description
    )
    ...
}
```

**setup-env.ps1** — функция без параметров, только Returns:

```powershell
function Generate-SecureKey {
    <#
    .SYNOPSIS
        Generates a cryptographically secure random string.
    .DESCRIPTION
        Args:
            $Length (int) — number of random bytes. Default: 32.

        Returns:
            string — URL-safe Base64 string with '+', '/' and '=' removed.
    .EXAMPLE
        $key = Generate-SecureKey 32
        # Returns a 40+ character random string
    #>
    param([int]$Length = 32)
    ...
}
```

### Паттерн guard clause

Все скрипты используют ранний выход вместо глубокой вложенности:

```powershell
# install-autostart.ps1
if (-not ([Security.Principal.WindowsPrincipal]...).IsInRole(...Administrator)) {
    Write-Host '❌ Administrator rights required.' -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $Script)) {
    Write-Host "❌ autostart.ps1 not found: $Script" -ForegroundColor Red
    exit 1
}
```

### Вспомогательный Python-скрипт

`_setup_env.py` — минимальный хелпер без классов и функций:

```python
# Создаёт .env из .env.example если файл отсутствует.
# Вызывается из install.ps1 как fallback перед setup-env.ps1.
root = Path(__file__).parent.parent
env = root / ".env"
example = root / ".env.example"

if env.exists():
    print(".env already exists — skipping")
elif example.exists():
    shutil.copy(example, env)
else:
    env.write_text("# FastAPI Foundry\nFOUNDRY_BASE_URL=...\n")
```

### Связи между скриптами

```
install.ps1 (корень)
  ├─ install\install-tesseract.ps1   (если не -SkipTesseract)
  ├─ install\install-foundry.ps1     (если foundry не найден)
  ├─ install\install-models.ps1      (при первой установке)
  ├─ install\install-shortcuts.ps1   (всегда)
  └─ install\_setup_env.py           (если .env отсутствует)

install\install-shortcuts.ps1
  └─ install\make-ico.ps1            (если icon.ico отсутствует)

install\install-autostart.ps1       (запускается отдельно, требует Admin)
install\install-huggingface-cli.ps1 (запускается отдельно)
install\setup-env.ps1               (запускается отдельно)
```
