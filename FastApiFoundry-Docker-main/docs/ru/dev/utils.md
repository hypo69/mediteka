# Утилиты

Проект содержит два уровня утилит:

- **`src/utils/`** — внутренние модули, используемые компонентами FastAPI Foundry (логирование, перевод, конфигурация)
- **`utils/`** — standalone-утилиты командной строки для управления, диагностики и обслуживания системы

---

## `utils/` — Standalone утилиты

| Файл | Назначение |
|---|---|
| `ai_model_scanner.py` | Сканирование AI моделей в системе (Foundry, Ollama, HuggingFace) |
| `foundry_model_finder.py` | Поиск и анализ доступных Foundry моделей |
| `port_manager.py` | Управление портами: поиск свободных, остановка процессов |
| `generate-ssl.py` | Генерация самоподписанных SSL сертификатов |
| `pc_component_processor.py` | Обработка и фильтрация JSON данных о компонентах ПК |

### Использование

```bash
# Сканирование AI моделей
python utils/ai_model_scanner.py

# Поиск свободного порта
python utils/port_manager.py --find-free

# Остановка процесса на порту
python utils/port_manager.py --kill-port 8000

# Генерация SSL сертификата
python utils/generate-ssl.py --domain localhost --days 365
```

### `pc_component_processor.py`

Обрабатывает JSON данные о компонентах ПК: классифицирует типы сборок, фильтрует запрещённые бренды, нормализует структуру.

```python
from utils.pc_component_processor import PCComponentProcessor

processor = PCComponentProcessor()
result = processor.execute("path/to/components.json")
# {"components": [{"name": "...", ...}, ...]}
```

**Класс `PCComponentProcessor`:**

| Метод | Описание |
|---|---|
| `execute(data_path)` | Запускает обработку JSON файла, возвращает нормализованный dict |
| `_process_items(data)` | Внутренняя обработка: фильтрация брендов, распаковка сборок |
| `_filter_brands(text)` | Удаляет упоминания запрещённых брендов из строки |

---

## `src/utils/` — Внутренние модули

Вспомогательные модули, используемые всеми компонентами FastAPI Foundry.

## Файлы

| Файл | Назначение |
|---|---|
| `translator.py` | Перевод текста через бесплатные онлайн-сервисы |
| `env_processor.py` | Загрузка `.env`, подстановка переменных, валидация конфигурации |
| `foundry_finder.py` | Автообнаружение порта Foundry Local |
| `logging_config.py` | Bootstrap-настройка уровня логирования |
| `logging_system.py` | Структурированный логгер с JSON-выводом и таймером |
| `log_analyzer.py` | Анализ лог-файлов: метрики, ошибки, производительность |
| `command_agent.py` | Асинхронный запуск CLI-команд через PowerShell, Circuit Breaker |
| `process_utils.py` | Стандартный запуск subprocess с проектными настройками |
| `text_utils.py` | Подсчёт токенов, санитизация имён файлов |

---

## Translator

`src/utils/translator.py` — утилита перевода текста. Переводит **входящие** запросы пользователя на английский перед отправкой в AI модель, и **исходящие** ответы модели обратно на язык пользователя.

Использует бесплатные онлайн-сервисы — API ключи не нужны по умолчанию.

### Провайдеры

| ID | Сервис | Ключ |
|---|---|---|
| `mymemory` | MyMemory API | Нет (500 слов/день; `MYMEMORY_EMAIL` → 50K) |
| `libretranslate` | LibreTranslate публичные инстансы | Нет |
| `deepl` | DeepL free tier | `DEEPL_API_KEY` |
| `google` | Google Cloud Translation | `GOOGLE_TRANSLATE_API_KEY` |

### Импорт

```python
from src.utils.translator import translator
# или через пакет
from src.utils import translator
```

### Методы

#### `translate(text, *, provider, source_lang, target_lang, api_key)`

Базовый метод перевода.

**Args:**

| Параметр | Тип | По умолчанию | Описание |
|---|---|---|---|
| `text` | `str` | — | Исходный текст |
| `provider` | `str` | `""` | Провайдер. Пусто = из `config.json` → `default_provider` |
| `source_lang` | `str` | `"auto"` | ISO 639-1 код или `"auto"` |
| `target_lang` | `str` | `"en"` | ISO 639-1 код целевого языка |
| `api_key` | `str` | `""` | Ключ API (переопределяет env-переменную) |

**Returns:** `dict` — `success`, `translated`, `provider`, `source_lang`, `target_lang`, `elapsed_ms`, `error`

```python
result = await translator.translate(
    "Привет мир",
    provider="mymemory",
    source_lang="auto",
    target_lang="en",
)
# {"success": True, "translated": "Hello world", "elapsed_ms": 340, ...}
```

---

#### `translate_for_model(text, *, provider, source_lang, api_key)`

Переводит текст на английский для AI модели. Если `source_lang="en"` — возвращает оригинал без запроса к сервису.

**Args:**

| Параметр | Тип | По умолчанию | Описание |
|---|---|---|---|
| `text` | `str` | — | Исходный текст |
| `provider` | `str` | `""` | Провайдер |
| `source_lang` | `str` | `"auto"` | ISO 639-1 код или `"auto"` |
| `api_key` | `str` | `""` | Ключ API |

**Returns:** `dict` — `success`, `translated`, `original`, `was_translated`, `provider`, `source_lang`, `target_lang`, `elapsed_ms`, `error`

```python
result = await translator.translate_for_model("Как дела?")
# {"was_translated": True, "translated": "How are you?", "original": "Как дела?", ...}
```

---

#### `translate_response(text, target_lang, *, provider, api_key)`

Переводит ответ AI модели обратно на язык пользователя. Если `target_lang="en"` — возвращает оригинал без запроса.

**Args:**

| Параметр | Тип | По умолчанию | Описание |
|---|---|---|---|
| `text` | `str` | — | Английский текст от AI модели |
| `target_lang` | `str` | — | ISO 639-1 код языка пользователя |
| `provider` | `str` | `""` | Провайдер |
| `api_key` | `str` | `""` | Ключ API |

**Returns:** `dict` — та же структура, что и `translate()`

```python
result = await translator.translate_response("I am fine", target_lang="ru")
# {"translated": "Я в порядке", ...}
```

---

#### `detect_language(text)`

Определяет язык текста через MyMemory (бесплатно, без ключа).

**Args:**

| Параметр | Тип | Описание |
|---|---|---|
| `text` | `str` | Текст для определения языка (используются первые 200 символов) |

**Returns:** `dict` — `success`, `language` (ISO 639-1), `language_name`, `error`

```python
result = await translator.detect_language("Bonjour le monde")
# {"language": "fr", "language_name": "French", "success": True}
```

---

#### `batch_translate(texts, *, provider, source_lang, target_lang, api_key)`

Переводит список строк последовательно.

**Args:**

| Параметр | Тип | По умолчанию | Описание |
|---|---|---|---|
| `texts` | `list[str]` | — | Список строк для перевода |
| `provider` | `str` | `""` | Провайдер |
| `source_lang` | `str` | `"auto"` | ISO 639-1 код или `"auto"` |
| `target_lang` | `str` | `"en"` | ISO 639-1 код целевого языка |
| `api_key` | `str` | `""` | Ключ API |

**Returns:** `dict` — `success`, `results` (список dict от `translate()`), `total`, `failed`, `elapsed_ms`

```python
result = await translator.batch_translate(["Hello", "Goodbye"], target_lang="ru")
# {"total": 2, "failed": 0, "results": [...]}
```

---

#### `close()`

Закрывает HTTP-сессию aiohttp. Вызывается автоматически при завершении lifespan FastAPI.

```python
await translator.close()
```

---

### Переменные окружения

```env
MYMEMORY_EMAIL=your@email.com        # Поднимает лимит MyMemory до 50K слов/день
LIBRETRANSLATE_API_KEY=...           # Для приватных инстансов LibreTranslate
DEEPL_API_KEY=...                    # Только для провайдера deepl
GOOGLE_TRANSLATE_API_KEY=...         # Только для провайдера google
```

### Настройка в config.json

```json
{
  "translator": {
    "default_provider": "mymemory",
    "request_timeout_sec": 30,
    "mymemory_email": "",
    "libretranslate_url": "https://libretranslate.com",
    "libretranslate_fallback_url": "https://translate.argosopentech.com"
  }
}
```

### Типичный сценарий использования

```python
# 1. Пользователь пишет на русском
user_input = "Объясни квантовую запутанность"

# 2. Переводим на английский для модели
req = await translator.translate_for_model(user_input)
english_prompt = req["translated"]   # "Explain quantum entanglement"
user_lang = req["source_lang"]       # "ru"

# 3. Отправляем в AI модель
ai_response = await foundry_client.generate_text(english_prompt)

# 4. Переводим ответ обратно на русский
resp = await translator.translate_response(ai_response["content"], target_lang=user_lang)
final_answer = resp["translated"]
```

---

## env_processor

`src/utils/env_processor.py` — загружает `.env`, подставляет переменные окружения в `config.json` и валидирует конфигурацию.

### Импорт

```python
from src.utils.env_processor import (
    load_env_variables,
    substitute_env_vars,
    process_config,
    validate_config,
    save_processed_config,
)
```

### Функции

#### `load_env_variables()`

Загружает переменные из файла `.env` в текущее окружение процесса.

**Returns:** `bool` — `True` если `.env` найден и загружен, `False` если файл отсутствует или произошла ошибка

```python
loaded = load_env_variables()
# True — .env загружен
```

---

#### `substitute_env_vars(value)`

Подставляет переменные окружения в строку.

Поддерживаемые форматы:
- `${VAR_NAME}` — обязательная переменная (исключение если не задана)
- `${VAR_NAME:default}` — с дефолтным значением

**Args:**

| Параметр | Тип | Описание |
|---|---|---|
| `value` | `str` | Строка с `${...}` плейсхолдерами |

**Returns:** Подставленное значение с автоматическим приведением типа (`str`, `int`, `float`, `bool`, `list`)

**Raises:** `ValueError` — если обязательная переменная не задана

```python
os.environ["PORT"] = "9696"
result = substitute_env_vars("${PORT:8000}")
# 9696  (int, не строка)

result = substitute_env_vars("${DEBUG:false}")
# False  (bool)
```

---

#### `convert_type(value)`

Приводит строку к наиболее подходящему Python-типу.

**Args:**

| Параметр | Тип | Описание |
|---|---|---|
| `value` | `str` | Строка для конвертации |

**Returns:** `bool` для `true/false/yes/no/1/0/on/off`, `int`/`float` для чисел, `list` для строк с запятыми, иначе `str`

```python
convert_type("true")    # True
convert_type("42")      # 42
convert_type("3.14")    # 3.14
convert_type("a,b,c")  # ["a", "b", "c"]
```

---

#### `process_config(config_path)`

Загружает `config.json` и подставляет все `${...}` переменные окружения.

**Args:**

| Параметр | Тип | Описание |
|---|---|---|
| `config_path` | `str \| Path` | Путь к файлу конфигурации |

**Returns:** `dict` — обработанная конфигурация

**Raises:**
- `FileNotFoundError` — файл не найден
- `json.JSONDecodeError` — невалидный JSON
- `ValueError` — обязательная env-переменная не задана

```python
cfg = process_config("config.json")
# {"fastapi_server": {"port": 9696, ...}, ...}
```

---

#### `validate_config(cfg)`

Проверяет наличие обязательных секций в конфигурации.

**Args:**

| Параметр | Тип | Описание |
|---|---|---|
| `cfg` | `dict` | Обработанная конфигурация |

**Returns:** `bool` — `True` если присутствуют все обязательные секции (`fastapi_server`, `foundry_ai`, `security`)

```python
if not validate_config(cfg):
    raise RuntimeError("Конфигурация неполная")
```

---

#### `save_processed_config(cfg, output_path)`

Сохраняет обработанную конфигурацию в файл.

**Args:**

| Параметр | Тип | Описание |
|---|---|---|
| `cfg` | `dict` | Конфигурация для сохранения |
| `output_path` | `str \| Path` | Путь к выходному файлу |

**Raises:** `OSError` — ошибка записи (диск заполнен, нет прав)

```python
save_processed_config(cfg, "config.processed.json")
```

---

### Синтаксис подстановки в config.json

```json
{
  "fastapi_server": {
    "port": "${FASTAPI_PORT:9696}",
    "host": "${FASTAPI_HOST:0.0.0.0}"
  },
  "foundry_ai": {
    "base_url": "${FOUNDRY_BASE_URL:http://localhost:50477/v1/}"
  },
  "security": {
    "api_key": "${API_KEY:}"
  }
}
```

---

## foundry_finder

`src/utils/foundry_finder.py` — автоматически обнаруживает порт, на котором запущен Foundry Local.

### Импорт

```python
from src.utils.foundry_finder import find_foundry_port, find_foundry_url
```

### Функции

#### `find_foundry_port()`

Ищет запущенный Foundry Local. Сначала проверяет переменную окружения `FOUNDRY_DYNAMIC_PORT`, затем сканирует известные порты.

**Returns:** `int | None` — номер порта если Foundry найден, `None` если не найден

**Порядок поиска:**
1. `FOUNDRY_DYNAMIC_PORT` из окружения
2. Порт `62171`
3. Порт `50477`
4. Порт `58130`

```python
port = find_foundry_port()
if port:
    print(f"Foundry на порту {port}")
else:
    print("Foundry не запущен")
```

---

#### `find_foundry_url()`

Возвращает полный базовый URL Foundry.

**Returns:** `str | None` — URL вида `http://localhost:50477/v1/` или `None`

```python
url = find_foundry_url()
# "http://localhost:50477/v1/"
```

---

#### `_test_foundry_port(port)` *(внутренняя)*

Проверяет, отвечает ли Foundry на указанном порту.

**Args:**

| Параметр | Тип | Описание |
|---|---|---|
| `port` | `int` | TCP-порт для проверки |

**Returns:** `bool` — `True` если `/v1/models` вернул HTTP 200

---

### Переменные окружения

```env
FOUNDRY_DYNAMIC_PORT=50477   # Принудительно задать порт (пропускает сканирование)
```

---

## logging_config

`src/utils/logging_config.py` — тонкий bootstrap для настройки уровня логирования. Вся конфигурация обработчиков (файлы, форматы) находится в `src/logger/__init__.py`.

### Импорт

```python
from src.utils.logging_config import setup_logging
```

### Функции

#### `setup_logging(log_level)`

Устанавливает уровень логирования и подавляет шумные сторонние библиотеки.

**Args:**

| Параметр | Тип | По умолчанию | Описание |
|---|---|---|---|
| `log_level` | `str` | `"INFO"` | Уровень: `DEBUG`, `INFO`, `WARNING`, `ERROR` |

**Подавляемые логгеры:** `watchfiles`, `watchfiles.main`, `uvicorn.access` → уровень `WARNING`

```python
setup_logging("DEBUG")   # Включить подробный вывод
setup_logging("WARNING") # Только предупреждения и ошибки
```

---

## logging_system

`src/utils/logging_system.py` — структурированный логгер-фасад поверх stdlib `logging`. Добавляет JSON-поля к сообщениям и контекстный таймер.

### Импорт

```python
from src.utils.logging_system import get_logger, logger

# Создать именованный логгер
log = get_logger("my-module")

# Использовать глобальный синглтон
from src.utils.logging_system import info, warning, error
```

### `get_logger(name)`

**Args:**

| Параметр | Тип | Описание |
|---|---|---|
| `name` | `str` | Имя логгера (отображается в выводе) |

**Returns:** `StructuredLogger`

```python
log = get_logger("rag-system")
log.info("Index loaded", chunks=512, vectors=512)
# [INFO] Index loaded | {"chunks": 512, "vectors": 512}
```

---

### Класс `StructuredLogger`

#### Методы логирования

Все методы принимают `message: str` и произвольные `**kwargs`, которые сериализуются как JSON и добавляются к сообщению.

| Метод | Уровень |
|---|---|
| `debug(message, **kwargs)` | DEBUG |
| `info(message, **kwargs)` | INFO |
| `warning(message, **kwargs)` | WARNING |
| `error(message, exc_info=None, **kwargs)` | ERROR |
| `critical(message, **kwargs)` | CRITICAL |
| `exception(message, **kwargs)` | ERROR + traceback |

```python
log.info("Request handled", status=200, duration=0.12)
# [INFO] Request handled | {"status": 200, "duration": 0.12}

log.error("Connection failed", exc_info=True, host="localhost", port=50477)
# [ERROR] Connection failed | {"host": "localhost", "port": 50477}
# + traceback
```

---

#### `timer(operation, **kwargs)` *(контекстный менеджер)*

Логирует время выполнения блока кода.

**Args:**

| Параметр | Тип | Описание |
|---|---|---|
| `operation` | `str` | Название операции для лога |
| `**kwargs` | | Дополнительные поля в JSON |

При успехе пишет `INFO` с `duration`. При исключении — `ERROR` с `duration` и `error`, затем пробрасывает исключение.

```python
with log.timer("rag-search", query="quantum"):
    results = await rag_system.search("quantum")
# ✅ rag-search | {"duration": 0.043, "query": "quantum"}
```

---

#### `log_api_request(method, path, status_code, duration, **kwargs)`

Логирует HTTP-запрос к API.

**Args:**

| Параметр | Тип | Описание |
|---|---|---|
| `method` | `str` | HTTP-метод (`GET`, `POST`, ...) |
| `path` | `str` | Путь запроса |
| `status_code` | `int` | Код ответа |
| `duration` | `float` | Время обработки в секундах |

```python
log.log_api_request("POST", "/api/v1/generate", 200, 1.23)
# [INFO] API POST /api/v1/generate → 200 (1.230s) | {...}
```

---

#### `log_model_operation(model_id, operation, status, duration, **kwargs)`

Логирует операцию с моделью.

**Args:**

| Параметр | Тип | Описание |
|---|---|---|
| `model_id` | `str` | Идентификатор модели |
| `operation` | `str` | Название операции: `load`, `unload`, `generate` |
| `status` | `str` | `"success"` или `"error"` |
| `duration` | `float \| None` | Длительность в секундах |

```python
log.log_model_operation("qwen3-0.6b", "load", "success", duration=3.5)
# [INFO] Model load: qwen3-0.6b → success (3.500s) | {...}
```

---

### Глобальные алиасы

Для удобства модуль экспортирует функции-алиасы глобального синглтона:

```python
from src.utils.logging_system import info, warning, error, debug, critical, exception

info("Server started", port=9696)
warning("Foundry not found")
error("Critical failure", exc_info=True)
```

---

## log_analyzer

`src/utils/log_analyzer.py` — анализирует лог-файлы из директории `logs/`. Читает структурированные `.jsonl` логи и предоставляет метрики производительности, сводки ошибок и состояние системы.

### Импорт

```python
from src.utils.log_analyzer import log_analyzer  # глобальный синглтон
# или
from src.utils.log_analyzer import LogAnalyzer
analyzer = LogAnalyzer(logs_dir="logs")
```

### Методы

#### `get_system_health()`

Анализирует состояние системы за последний час.

**Returns:** `dict`

| Поле | Тип | Описание |
|---|---|---|
| `status` | `str` | `"healthy"` / `"warning"` / `"critical"` / `"error"` |
| `timestamp` | `datetime` | Время анализа |
| `period` | `str` | `"1h"` |
| `metrics.errors_count` | `int` | Количество ошибок за час |
| `metrics.warnings_count` | `int` | Количество предупреждений за час |
| `metrics.api_requests` | `int` | Количество API-запросов |
| `metrics.avg_response_time` | `float` | Среднее время ответа (сек) |
| `metrics.active_models` | `int` | Количество активных моделей |
| `metrics.failed_model_operations` | `int` | Количество неудачных операций с моделями |
| `details` | `dict` | Детали: `api_performance`, `model_performance` |

**Пороги статуса:**
- `critical` — ошибок > 10
- `warning` — ошибок > 5 или предупреждений > 20
- `healthy` — иначе

```python
health = await log_analyzer.get_system_health()
print(health["status"])          # "healthy"
print(health["metrics"]["errors_count"])  # 2
```

---

#### `get_error_summary(hours=24)`

Сводка ошибок за указанный период.

**Args:**

| Параметр | Тип | По умолчанию | Описание |
|---|---|---|---|
| `hours` | `int` | `24` | Глубина анализа в часах |

**Returns:** `dict`

| Поле | Тип | Описание |
|---|---|---|
| `period` | `str` | Например `"24h"` |
| `total_errors` | `int` | Общее количество ошибок |
| `error_types` | `dict` | Топ-10 типов ошибок с количеством |
| `error_modules` | `dict` | Топ-10 модулей с ошибками |
| `timeline` | `dict` | Ошибки по часам `{"2025-12-09 14:00": 3, ...}` |
| `recent_errors` | `list` | Последние 10 ошибок |
| `timestamp` | `datetime` | Время анализа |

**Типы ошибок** (автоклассификация по тексту сообщения):

| Тип | Ключевые слова |
|---|---|
| `connection_error` | `connection`, `timeout` |
| `model_error` | `model` |
| `api_error` | `api`, `http` |
| `configuration_error` | `config`, `setting` |
| `file_error` | `file`, `path` |
| `general_error` | всё остальное |

```python
summary = await log_analyzer.get_error_summary(hours=6)
print(summary["total_errors"])          # 5
print(summary["error_types"])           # {"connection_error": 3, "model_error": 2}
```

---

#### `get_performance_metrics(hours=24)`

Метрики производительности за период.

**Args:**

| Параметр | Тип | По умолчанию | Описание |
|---|---|---|---|
| `hours` | `int` | `24` | Глубина анализа в часах |

**Returns:** `dict`

| Поле | Описание |
|---|---|
| `api_performance` | Статистика API-запросов (см. ниже) |
| `model_performance` | Статистика операций с моделями (см. ниже) |
| `system_performance` | Системные метрики |
| `period` | Например `"24h"` |
| `timestamp` | Время анализа |

**`api_performance`:**

| Поле | Описание |
|---|---|
| `total_requests` | Общее количество запросов |
| `avg_response_time` | Среднее время ответа (сек) |
| `max_response_time` | Максимальное время ответа |
| `min_response_time` | Минимальное время ответа |
| `endpoints` | Топ-10 эндпоинтов по количеству запросов |
| `status_codes` | Распределение HTTP-кодов ответа |
| `requests_per_hour` | Запросов в час |

**`model_performance`:**

| Поле | Описание |
|---|---|
| `models` | Статистика по каждой модели: `operations`, `successful`, `failed`, `avg_duration` |
| `total_operations` | Всего операций |
| `failed_operations` | Количество неудачных операций |

**`system_performance`:**

| Поле | Описание |
|---|---|
| `uptime_hours` | Время работы в часах |
| `log_files_count` | Количество `.log` файлов |
| `structured_logs_count` | Количество `.jsonl` файлов |

```python
metrics = await log_analyzer.get_performance_metrics(hours=1)
api = metrics["api_performance"]
print(api["total_requests"])      # 142
print(api["avg_response_time"])   # 0.234
print(api["endpoints"])           # {"/api/v1/generate": 89, "/api/v1/health": 53}
```

---

### Формат структурированных логов

`log_analyzer` читает файлы `logs/*-structured.jsonl`. Каждая строка — JSON-объект:

```json
{
  "timestamp": "2025-12-09T14:32:01.123456",
  "level": "info",
  "logger": "src.api.endpoints.generate",
  "message": "API POST /api/v1/generate → 200 (1.230s)",
  "api_method": "POST",
  "api_path": "/api/v1/generate",
  "status_code": 200,
  "duration": 1.23
}
```

Для попадания в метрики модели запись должна содержать поля `model_id` и `operation`:

```json
{
  "timestamp": "2025-12-09T14:30:00.000000",
  "level": "info",
  "message": "Model load: qwen3-0.6b → success (3.500s)",
  "model_id": "qwen3-0.6b",
  "operation": "load",
  "status": "success",
  "duration": 3.5
}
```

---

## command_agent

`src/utils/command_agent.py` — асинхронный оркестратор запуска CLI-команд через PowerShell wrapper. Реализует паттерн **Circuit Breaker** для защиты от циклических сбоев.

Синглтон: `CommandAgent()` — состояние Circuit Breaker сохраняется между вызовами API.

### Импорт

```python
from src.utils.command_agent import CommandAgent
agent = CommandAgent()
```

### Circuit Breaker

При 3 последовательных ошибках одной команды агент блокирует её на 60 секунд. При изменении системного `PATH` все счётчики сбрасываются автоматически.

| Параметр | Значение |
|---|---|
| `FAILURE_THRESHOLD` | 3 ошибки |
| `COOLDOWN_SECONDS` | 60 секунд |

### Методы

#### `run(command, args, timeout) -> dict`

Запускает команду через PowerShell wrapper с Circuit Breaker.

```python
result = await agent.run("foundry", ["service", "status"], timeout=30)
# {"exit_code": 0, "stdout": "...", "stderr": "..."}
```

#### `test_command_available(command) -> bool`

Проверяет наличие команды в `PATH` через `Get-Command`.

```python
if await agent.test_command_available("foundry"):
    ...
```

#### `parse_foundry_status() -> dict`

Парсит вывод `foundry service status`.

**Returns:** `{"status": "running", "pid": 1234, "port": 50477, "health_check": "ok"}`

#### `reset_circuit_breaker(command=None)`

Сбрасывает счётчик ошибок. Без аргумента — сбрасывает все.

---

## process_utils

`src/utils/process_utils.py` — тонкая обёртка над `subprocess.run` с проектными настройками по умолчанию.

### Импорт

```python
from src.utils.process_utils import run_command
```

### `run_command(args, timeout, shell, capture_output) -> CompletedProcess`

Запускает команду с `encoding="utf-8"`, `errors="replace"`, логирует ошибки.

```python
result = run_command(["foundry", "model", "list"], timeout=10)
print(result.stdout)
```

**Raises:** `subprocess.TimeoutExpired`, `Exception` — логирует и пробрасывает.

---

## text_utils

`src/utils/text_utils.py` — минимальные утилиты для работы с текстом.

### Импорт

```python
from src.utils.text_utils import count_tokens_approx, sanitize_for_filesystem
```

### `count_tokens_approx(text) -> int`

Приблизительный подсчёт токенов: ~4 символа на токен. Минимум 1.

```python
count_tokens_approx("Hello world")  # 2
count_tokens_approx("")             # 1
```

### `sanitize_for_filesystem(name) -> str`

Преобразует произвольную строку в безопасное имя файла/директории. Оставляет только `[a-zA-Z0-9_-]`, остальное заменяет на `_`.

```python
sanitize_for_filesystem("my model v2.0!")  # "my_model_v2_0_"
sanitize_for_filesystem("qwen::3-0.6b")    # "qwen__3-0_6b"
```

Используется при создании RAG профилей и именовании файлов диалогов.
