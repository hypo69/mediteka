# Install-Autostart.ps1

Регистрирует задание в Windows Task Scheduler для автозапуска AI Assistant при входе пользователя.

**Файл:** `install\Install-Autostart.ps1`  
**Запуск:** `powershell -ExecutionPolicy Bypass -File .\install\Install-Autostart.ps1`

!!! danger "Требуются права администратора"
    Скрипт должен быть запущен от имени администратора.

---

## Назначение

Создаёт задание `FastApiFoundry-Autostart` в планировщике Windows:
- Триггер: вход пользователя (`AtLogOn`)
- Действие: запуск `autostart.ps1` в скрытом окне
- Настройки: 3 попытки перезапуска с интервалом 1 минута, без ограничения времени выполнения

---

## Параметры

| Параметр | Тип | Описание |
|---|---|---|
| `-Uninstall` | switch | Удалить задание из планировщика |

---

## Примеры

```powershell
# Установить автозапуск
powershell -ExecutionPolicy Bypass -File .\install\Install-Autostart.ps1

# Удалить автозапуск
powershell -ExecutionPolicy Bypass -File .\install\Install-Autostart.ps1 -Uninstall
```

---

## Структура задания

```
Имя задания:  FastApiFoundry-Autostart
Триггер:      При входе пользователя
Действие:     powershell.exe -NonInteractive -NoProfile
              -ExecutionPolicy Bypass -WindowStyle Hidden
              -File "...\autostart.ps1"
Уровень:      Highest (повышенные права)
Перезапуск:   3 раза × 1 минута
```

---

## Связанные файлы

- [`autostart.ps1`](../../powershell/autostart.md) — скрипт автозапуска
- [`start.ps1`](../../powershell/start.md) — интерактивный запуск
