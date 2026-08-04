# Windows Sandbox — запуск проекта в изолированной среде

Файлы для работы с Windows Sandbox перенесены в директорию `microsoft_sandbox_operations/`.
Pipeline состоит из трёх компонентов: лончер, маппер и `.wsb`-конфигурация.

---

## Требования

| Требование | Минимум |
|---|---|
| Windows | 10 Pro / Enterprise / Education (build 18305+) или Windows 11 |
| PowerShell | 5.1+ |
| Права | Администратор |
| BIOS | Виртуализация включена (Intel VT-x / AMD-V) |

> 💡 **Проверить виртуализацию:** Диспетчер задач → вкладка **Производительность** → раздел **ЦП** → строка **Виртуализация: включено**

> ⚙️ **Включить Windows Sandbox:** `Win+R` → `appwiz.cpl` → **Включение или отключение компонентов Windows** → отметить **Windows Sandbox**

> 📖 **Подробная инструкция:** [remontka.pro/sandbox-windows/#enable](https://remontka.pro/sandbox-windows/#enable)

---

## Использование

```powershell
powershell -ExecutionPolicy Bypass -File .\microsoft_sandbox_operations\sandbox-launcher.ps1
```

### Параметры `sandbox-launcher.ps1`

| Параметр | Тип | По умолчанию | Описание |
|---|---|---|---|
| `-DelayMs` | int | `2000` | Задержка (мс) между синхронизацией и запуском Sandbox |

---

## Структура директории

```
microsoft_sandbox_operations/
├── sandbox-launcher.ps1   # Точка входа — оркестрирует pipeline
├── sandbox-mapper.ps1     # Синхронизация проекта через robocopy
├── sandbox.wsb            # Конфигурация Sandbox (маппинг, сеть)
└── sandbox-silent.wsb     # Конфигурация для silent-режима
```

---

## Логика работы

```
sandbox-launcher.ps1
    │
    ├─ [1] sandbox-mapper.ps1 (если файл существует)
    │       robocopy $Source → $Target /MIR
    │       исключает: venv, .git, __pycache__, node_modules, *.log
    │       └─ код завершения ≥ 8 → pipeline прерывается
    │
    ├─ [2] Start-Sleep -Milliseconds $DelayMs
    │       ожидание сброса файловой системы
    │
    └─ [3] Start-Process sandbox.wsb
            Windows Sandbox монтирует staging-директорию как read-only
```

---

## Функции

### `sandbox-launcher.ps1` — `Invoke-SandboxScript`

Запускает дочерний скрипт в изолированном процессе PowerShell.

| Параметр | Тип | Описание |
|---|---|---|
| `-Path` | string | Полный путь к скрипту |

**Возвращает:** `bool` — `$true` при успешном завершении

---

### `sandbox-launcher.ps1` — `Invoke-SandboxPipeline`

Оркестрирует полный pipeline: маппер → задержка → запуск.

**Возвращает:** `bool` — `$true` если Sandbox запущен успешно

---

### `sandbox-mapper.ps1` — `Sync-Project`

Зеркалирует исходную директорию в staging через `robocopy /MIR`.

| Параметр | Тип | Описание |
|---|---|---|
| `-Source` | string | Путь к проекту на хосте |
| `-Target` | string | Staging-директория для монтирования |

**Возвращает:** `bool` — `$true` если `robocopy` завершился с кодом ≤ 3

---

## Конфигурация sandbox.wsb

```xml
<Configuration>
  <MappedFolders>
    <MappedFolder>
      <HostFolder>D:\sandbox_mount</HostFolder>
      <SandboxFolder>C:\Users\WDAGUtilityAccount\Desktop\src</SandboxFolder>
      <ReadOnly>true</ReadOnly>
    </MappedFolder>
  </MappedFolders>
  <Networking>Enable</Networking>
</Configuration>
```

Измените `HostFolder` на путь к staging-директории (параметр `-Target` в `sandbox-mapper.ps1`).

---

## Устранение неполадок

| Симптом | Причина | Решение |
|---|---|---|
| `Sandbox script not found` | Неверный рабочий каталог | Запускать `sandbox-launcher.ps1` напрямую по полному пути |
| `Sandbox sync failed` | `robocopy` код ≥ 8 | Проверить права на запись в `-Target` директорию |
| Sandbox не появляется в списке компонентов | Windows Home edition | Нужна Pro / Enterprise / Education |
| Sandbox не открывается | `.wsb` не ассоциирован | Установить Windows Sandbox через «Компоненты Windows» |
| После включения компонентов требуется перезагрузка | Нормальное поведение | Перезапустить ПК, затем повторить скрипт |

> 📖 Подробная инструкция по установке и включению Sandbox:  
> **[https://remontka.pro/sandbox-windows/#enable](https://remontka.pro/sandbox-windows/#enable)**
