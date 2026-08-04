# windows_os_mcp.py

**Файл:** `mcp/src/servers/windows_os_mcp.py`  
**Протокол:** MCP STDIO  
**Версия:** 0.7.1

## Назначение

MCP сервер для диагностики Windows OS. Выполняет PowerShell команды через `pwsh` и возвращает структурированный JSON.

## Инструменты

| Инструмент | Описание |
|---|---|
| `get_processes` | Топ N процессов по CPU или памяти |
| `get_services` | Список служб Windows с фильтром по статусу |
| `get_disk_info` | Использование дискового пространства |
| `get_network_stats` | Активные TCP соединения и сетевые адаптеры |
| `get_system_info` | ОС, CPU, RAM, uptime |
| `kill_process` | Завершить процесс по PID |
| `get_startup_items` | Программы в автозагрузке |

### get_processes

| Параметр | Тип | По умолчанию | Описание |
|---|---|---|---|
| `sort_by` | string | `cpu` | Сортировка: `cpu`, `memory`, `name` |
| `top` | integer | 20 | Количество процессов (1–100) |

### get_services

| Параметр | Тип | По умолчанию | Описание |
|---|---|---|---|
| `filter_status` | string | `all` | Фильтр: `all`, `Running`, `Stopped` |

### kill_process

| Параметр | Тип | Обязательный | Описание |
|---|---|---|---|
| `pid` | integer | ✅ | PID процесса |

## Требования

- PowerShell 7+ (`pwsh`) должен быть доступен в PATH

## Запуск

```powershell
venv\Scripts\python.exe mcp/src/servers/windows_os_mcp.py
```
