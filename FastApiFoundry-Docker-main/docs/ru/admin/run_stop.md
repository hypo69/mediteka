# Запуск и остановка

---

## Последовательность запуска

`start.ps1` — тонкий оркестратор. Каждый этап делегирован отдельному скрипту в `scripts/Start-Engine/`:

```
start.ps1
│
├── gui\Start-Tray.ps1                     # [0] Иконка в трее — первый шаг, следит за состоянием сама
├── scripts\Update-Project.ps1             # [1] Проверка обновлений по git-тегам
├── venv + .env                            # [2] Активация окружения, загрузка переменных
│
├── Start-Engine\Start-Foundry.ps1         # [3] Обнаруживает или запускает Microsoft Foundry Local
├── Start-Engine\Start-MkDocs.ps1          # [4] Сервер документации (если docs_server.enabled)
├── Start-Engine\Start-Llama.ps1           # [5] llama-server.exe с GGUF-моделью (если auto_start)
├── Start-Engine\Start-OpenCode.ps1        # [6] OpenCode сервер (если enabled + auto_start)
│
├── Start-Engine\Start-FastApi.ps1         # [7] Запускает run.py, ждёт порт, открывает браузер ⬅ блокирующий
│
finally
└── Start-Engine\Stop-Engine.ps1           # Останавливает все компоненты по PID-файлам
```

Назначение каждого скрипта:

| Файл | Что делает |
|---|---|
| `start.ps1` | Точка входа. Тонкий оркестратор: запускает все этапы по порядку |
| `gui/Start-Tray.ps1` | Запускает `tray.py` в скрытом окне, следит за PID |
| `gui/tray.py` | Иконка в трее: меню Admin / User / Start / Shutdown, опрашивает `/health` каждые 5 с |
| `scripts/Update-Project.ps1` | Проверяет обновления по git-тегам |
| `scripts/Get-FoundryUtils.ps1` | Утилиты: `Test-FoundryCli`, `Get-FoundryPort`, `Get-FoundryUrl` |
| `Start-Engine/Start-Foundry.ps1` | Обнаруживает или запускает Foundry Local, экспортирует `FOUNDRY_BASE_URL` |
| `Start-Engine/Start-MkDocs.ps1` | Запускает сервер документации (`http.server` или `mkdocs serve`) |
| `Start-Engine/Start-Llama.ps1` | Распаковывает бинарник и запускает `llama-server.exe` с GGUF-моделью |
| `Start-Engine/Start-OpenCode.ps1` | Запускает OpenCode сервер (если `enabled` + `auto_start` в `config.json`) |
| `Start-Engine/Start-FastApi.ps1` | Останавливает предыдущий FastAPI, запускает `run.py`, ждёт порт, открывает браузер |
| `Start-Engine/Stop-Engine.ps1` | Останавливает все компоненты по PID-файлам из `%TEMP%` |

!!! info "Иконка в трее"
    Трей запускается **первым** — до Foundry, llama и FastAPI.
    Пока сервер грузится, пункты **Admin** и **Shutdown** неактивны.
    Как только `/api/v1/health` ответил — меню переключается автоматически.

---

## Запуск

```powershell
# Основной способ — запускает всё (venv, Foundry, llama.cpp, FastAPI)
.\start.ps1

# Если Foundry уже запущен — можно напрямую
venv\Scripts\python.exe run.py
```

После запуска: **http://localhost:9696**

Подробный разбор этапов `start.ps1`: [Локальный workflow](../user/local_workflow.md)

---

## Остановка

```powershell
# Остановить FastAPI, llama.cpp, MkDocs
.\stop.ps1

# Остановить всё включая Foundry
.\stop.ps1 -StopFoundry
```

!!! warning "Foundry не останавливается по умолчанию"
    Foundry — системный сервис Microsoft. Его остановка выгрузит модель из памяти.
    Используйте `-StopFoundry` осознанно.

---

## Перезапуск

```powershell
.\start.ps1
```

`start.ps1` сам остановит предыдущий экземпляр FastAPI и запустит новый.

---

## Автозапуск при входе в Windows

```powershell
# Зарегистрировать автозапуск (требует прав администратора)
.\install\install-autostart.ps1

# Удалить автозапуск
.\install\install-autostart.ps1 -Uninstall
```

Система будет запускаться автоматически при входе пользователя в Windows.
Лог автозапуска: `logs/autostart.log`

---

## Порты сервисов

| Сервис | Порт | Управление |
|---|---|---|
| FastAPI | 9696 | `start.ps1` / `stop.ps1` |
| MkDocs (документация) | 9697 | `start.ps1` (если `docs_server.enabled: true`) |
| llama.cpp | 9780 | `start.ps1` (если `llama_cpp.auto_start: true`) |
| Foundry Local | авто | `foundry service start/stop` |
