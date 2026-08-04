# Install-LMStudio.ps1

Специализированный установщик LM Studio для Windows.

**Файл:** `install\Install-LMStudio.ps1`  
**Запуск:** `powershell -ExecutionPolicy Bypass -File .\install\Install-LMStudio.ps1`

---

## Назначение

Скрипт проверяет наличие LM Studio CLI (`lms`) и, если CLI не найден,
спрашивает пользователя, нужно ли установить LM Studio.

При согласии используется официальная команда LM Studio:

```powershell
irm https://lmstudio.ai/install.ps1 | iex
```

`irm` — стандартный alias PowerShell для `Invoke-RestMethod`. Перед запуском
официальной команды скрипт проверяет наличие и `irm`, и `Invoke-RestMethod`.
Если они недоступны, специализированный скрипт останавливает только шаг
LM Studio с объяснением причины и рекомендацией запустить PowerShell 7+ или
Windows PowerShell 5.1+. Главный `install.ps1` ловит эту ошибку, пишет её в
`logs\aiassistant-install.log` и продолжает установку остальных компонентов.

---

## Параметры

| Параметр | Тип | Описание |
|---|---|---|
| `-SkipIfExists` | switch | Завершить без действий, если `lms` уже найден |
| `-DiagnosticsOnly` | switch | Только проверить наличие LM Studio, без установки |
| `-AssumeYes` | switch | Не задавать вопрос и сразу запускать официальный установщик |

---

## Поведение

1. Ищет `lms` через `Get-Command`.
2. Проверяет стандартные пути:
   - `%USERPROFILE%\.lmstudio\bin\lms.exe`
   - `%LOCALAPPDATA%\Programs\LM Studio\...`
   - `%LOCALAPPDATA%\LM Studio\lms.exe`
3. Если LM Studio найден — показывает версию.
4. Если не найден — спрашивает пользователя.
5. Перед установкой проверяет `irm` / `Invoke-RestMethod`.
6. Запускает официальный bootstrap.
7. После установки пытается выполнить `lms bootstrap`.
8. Показывает статус сервера или подсказку `lms server start`.

---

## Связь с install.ps1

Главный `install.ps1` не содержит сетевую установочную логику LM Studio.
Он вызывает этот скрипт внутри `try/catch`:

```powershell
& .\install\Install-LMStudio.ps1
```

Это сохраняет архитектуру установщика: `install.ps1` управляет порядком шагов,
а конкретные install-задачи живут в отдельных `install\Install-*.ps1`.

Ошибки этого шага являются нефатальными для общего install flow: LM Studio
провайдер будет недоступен до ручной установки LM Studio, но FastAPI, Foundry,
llama.cpp, Ollama, HuggingFace и остальные компоненты продолжают настраиваться.

---

## Тесты

Проверки находятся в:

```powershell
tests\unit\InstallLMStudio.Tests.ps1
```

Они валидируют синтаксис, наличие официальной команды, защитную проверку `irm`
и то, что `install.ps1` вызывает специализированный скрипт.
