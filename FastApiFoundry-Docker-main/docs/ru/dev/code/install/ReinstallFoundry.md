# ReinstallFoundry.ps1

Полный сброс и переустановка Microsoft Foundry Local. Используется в CI/QA-пайплайнах.

**Файл:** `install\ReinstallFoundry.ps1`  
**Запуск:** `powershell -ExecutionPolicy Bypass -File .\install\ReinstallFoundry.ps1`

---

## Назначение

Выполняет три шага последовательно:

```
Stop-Foundry → Uninstall-Foundry → Install-Foundry → Wait-Ready
```

**Коды завершения:**

| Код | Значение |
|---|---|
| `0` | Успех — API готов |
| `1` | Ошибка установки |
| `2` | Таймаут — API не ответил за отведённое время |

---

## Параметры

| Параметр | Тип | По умолчанию | Описание |
|---|---|---|---|
| `-TimeoutSec` | int | `60` | Максимальное время ожидания готовности API |
| `-Verbose` | switch | — | Выводить счётчик оставшегося времени |

---

## Примеры

```powershell
# Стандартная переустановка
powershell -ExecutionPolicy Bypass -File .\install\ReinstallFoundry.ps1

# С увеличенным таймаутом
powershell -ExecutionPolicy Bypass -File .\install\ReinstallFoundry.ps1 -TimeoutSec 120

# С подробным выводом
powershell -ExecutionPolicy Bypass -File .\install\ReinstallFoundry.ps1 -TimeoutSec 30 -Verbose
```

---

## Функции

### Stop-Foundry
Принудительно завершает все процессы `Inference.Service.Agent*`. Ждёт 2 секунды для освобождения портов.

### Uninstall-Foundry
Останавливает сервис и удаляет пакет через `winget uninstall Microsoft.FoundryLocal --silent`. Очищает PATH в текущей сессии.

### Install-Foundry
Устанавливает `Microsoft.FoundryLocal` через winget в тихом неинтерактивном режиме. Обновляет PATH. Завершает с кодом `1` при ошибке.

### Wait-Ready
Запускает `foundry service start`, затем опрашивает `GET /v1/models` на портах 50000–60000 до получения ответа `200 OK` или истечения таймаута.

---

## Использование в CI

```yaml
# GitHub Actions
- name: Reinstall Foundry
  shell: pwsh
  run: |
    powershell -ExecutionPolicy Bypass -File .\install\ReinstallFoundry.ps1 -TimeoutSec 120
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
```

