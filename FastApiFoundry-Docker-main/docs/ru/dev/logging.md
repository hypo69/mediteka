# Подсистема логирования — документация разработчика

## Цель

Логирование используется как диагностический контур для администратора. В
файловое хранилище пишутся только предупреждения и ошибки. Обычные успешные
запросы `200 OK` не сохраняются.

## Архитектура

```text
logging.getLogger(__name__).warning/error(...)
               |
               v
        stdlib root logger
               |
        +------+-------------------+
        |                          |
        v                          v
 console StreamHandler       DailyLineRotatingFileHandler
                             %TEMP%/aissistant
```

Ключевой файл: `src/logger/__init__.py`.

`configure_logging()` подключает управляемые handlers к root logger. Поэтому
обычные модульные логгеры вида `logging.getLogger(__name__)` автоматически
попадают в общий поток.

## Файлы

| Файл | Назначение |
|---|---|
| `src/logger/__init__.py` | `DailyLineRotatingFileHandler`, `configure_logging`, `get_log_settings` |
| `src/utils/logging_config.py` | Bootstrap-обертка для запуска |
| `src/api/app.py` | FastAPI middleware: логирует только `4xx`, `5xx`, исключения |
| `src/api/endpoints/logs.py` | REST API для вкладки Logs |
| `src/models/router.py` | Логирование ошибок backend-генерации |
| `src/api/endpoints/chat_endpoints.py` | Логирование исключений session chat |
| `src/api/endpoints/ai_endpoints.py` | Логирование ошибок AI chat, stream и RAG enhancement |
| `static/interface/partials/_tab_logs.html` | UI вкладки Logs |
| `static/interface/js/ui.js` | JS логика просмотрщика и настроек |

## Handler

`DailyLineRotatingFileHandler` пишет файлы по шаблону:

```text
aiassistant-YYYY-MM-DD-NNN.log
```

Ротация происходит в двух случаях:

- сменилась дата
- текущий файл достиг `max_lines_per_file`

Старые файлы удаляются, когда их дата старше `retention_days`.

## Конфигурация

Источник: секция `logging` в `config.json`.

```json
{
  "logging": {
    "level": "WARNING",
    "log_dir": "",
    "max_lines_per_file": 5000,
    "retention_days": 7
  }
}
```

Правила:

- `log_dir == ""` означает `%TEMP%/aissistant`
- `AIASSISTANT_LOG_DIR` может переопределить путь
- `LOG_LEVEL` может переопределить уровень для root/console
- файловый handler всегда пишет только `WARNING` и выше

## FastAPI

Middleware в `src/api/app.py`:

- не логирует `2xx`
- логирует `4xx` как `WARNING`
- логирует `5xx` как `ERROR`
- логирует необработанные исключения с `exc_info=True`

Global exception handler также пишет stack trace.

## Model/Chat

`route_generate()` в `src/models/router.py` оборачивает backend-вызовы:

- исключение backend-клиента -> `ERROR` и ответ `{"success": false}`
- ответ backend без success -> `ERROR`

Chat endpoints дополнительно пишут:

- обычный chat generation failure
- streaming chat failure
- ошибки chunk-ответов
- RAG enhancement degradation как `WARNING`

## Logs API

| Метод | URL | Описание |
|---|---|---|
| `GET` | `/api/v1/logs/files` | Список файлов в текущей log-dir |
| `GET` | `/api/v1/logs` | Чтение файла, фильтр уровня, поиск, пагинация |
| `GET` | `/api/v1/logs/settings` | Текущие настройки |
| `POST` | `/api/v1/logs/settings` | Сохранить `max_lines_per_file`, `retention_days`, `level` |
| `GET` | `/api/v1/logs/health` | Метрики warning/error для бейджей |
| `POST` | `/api/v1/logs/clear` | Очистить выбранный файл |
| `GET` | `/api/v1/logs/download` | Скачать выбранный файл |

`GET /api/v1/logs` без `file` читает самый свежий файл.

## Тесты

Модульные тесты находятся в:

```text
tests/unit/test_logging_system.py
```

Покрытие:

- запись только `WARNING+`
- ротация по количеству строк
- чтение настроек из `config.json`
- список файлов API
- чтение логов с фильтрами
- health-метрики warning/error

Запуск:

```powershell
venv\Scripts\python.exe -m pytest tests/unit/test_logging_system.py
```

