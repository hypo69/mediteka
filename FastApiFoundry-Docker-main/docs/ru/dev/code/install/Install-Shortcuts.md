# Install-Shortcuts.ps1

Создаёт ярлыки AI Assistant на рабочем столе Windows.

**Файл:** `install\Install-Shortcuts.ps1`  
**Запуск:** `powershell -ExecutionPolicy Bypass -File .\install\Install-Shortcuts.ps1`

---

## Назначение

Создаёт три ярлыка на рабочем столе:

| Ярлык | Скрипт | Окно | Описание |
|---|---|---|---|
| `AI Assistant.lnk` | `start.ps1` | Обычное | Запуск с консолью |
| `AI Assistant (Silent).lnk` | `autostart.ps1` | Скрытое | Тихий запуск |
| `AI Assistant Docs.lnk` | URL | — | Открывает документацию в браузере |

Перед созданием ярлыков автоматически строит `icon.ico` из PNG-файлов через `Make-Ico.ps1`.

---

## Параметры

| Параметр | Тип | Описание |
|---|---|---|
| `-Silent` | switch | Тихий режим (без вывода) |

---

## Примеры

```powershell
powershell -ExecutionPolicy Bypass -File .\install\Install-Shortcuts.ps1
```

---

## Функции

### Ensure-Icon
Строит `icon.ico` из `assets\icons\` через `Make-Ico.ps1` если файл не существует.

### New-AppShortcut
Создаёт `.lnk`-ярлык через `WScript.Shell` с заданными параметрами.

**Параметры:**

| Параметр | Тип | Описание |
|---|---|---|
| `$Name` | string | Имя ярлыка без `.lnk` |
| `$Arguments` | string | Аргументы для `powershell.exe` |
| `$WindowStyle` | int | 1 = обычное, 7 = скрытое |
| `$Description` | string | Подсказка при наведении |

---

## Связанные файлы

- [`install\Make-Ico.ps1`](Make-Ico.md) — конвертер PNG → ICO
- [`start.ps1`](../../powershell/start.md) — запуск с консолью
- [`autostart.ps1`](../../powershell/autostart.md) — тихий запуск

