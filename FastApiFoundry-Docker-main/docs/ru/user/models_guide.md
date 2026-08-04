# Работа с моделями

## Вкладка «Модели» — обзор

Вкладка **Модели** — центральная точка управления всеми AI-моделями в системе.
Она показывает что сейчас загружено в память и что доступно для загрузки, не требуя переключаться между вкладками провайдеров.

---

## Раздел «Активные модели»

Здесь отображаются модели, **загруженные в оперативную память** и готовые принимать запросы через API прямо сейчас.

Для каждой активной модели показывается:

- **Провайдер** — Foundry, HuggingFace, llama.cpp или Ollama
- **Префикс** — строка вида `foundry::qwen3-0.6b`, которую нужно передавать в поле `model` при API-запросах
- **Кнопка «Set Active»** — делает модель активной по умолчанию для чата
- **Кнопка выгрузки** — освобождает RAM/VRAM

!!! tip "Активная модель"
    Нажмите **Set Active** на нужной модели — она автоматически выберется в чате и станет моделью по умолчанию для всех запросов без явного указания `model`.

---

## Раздел «Доступные модели»

Список всех моделей, известных системе, **сгруппированных по провайдерам**:

| Провайдер | Источник данных | Что показывается |
|---|---|---|
| **Microsoft Foundry** | Foundry HTTP API `GET /v1/models` | Загруженные модели; кэш — filesystem scan |
| **HuggingFace** | `scan_cache_dir()` (официальный HF API) | Скачанные локально модели |
| **llama.cpp** | Статус сервера | Текущая запущенная модель |
| **Ollama** | Ollama API | Все локальные Ollama модели |

### Действия с моделью

Для каждой модели в списке доступны:

- **▶ Load** — загрузить модель в память (она появится в разделе «Активные»)
- **■ Unload** — выгрузить из памяти (освободить ресурсы)
- **📋 Copy** — скопировать префикс модели в буфер обмена

Значки статуса:

| Значок | Смысл |
|---|---|
| `Loaded` (зелёный) | Модель в памяти, готова к работе |
| `Loading` (жёлтый) | Модель загружается |
| *(нет значка)* | Модель на диске, не загружена |

---

## Как загрузить модель

### Через вкладку Модели

1. Найдите нужную модель в разделе «Доступные модели»
2. Нажмите **▶ Load**
3. Дождитесь появления модели в разделе «Активные модели» (обновление автоматическое)
4. Нажмите **Set Active** — модель готова к использованию

### Через специализированные вкладки

Если модели ещё нет на диске — сначала скачайте её:

| Провайдер | Где скачать |
|---|---|
| Foundry | Вкладка **Foundry** → Downloaded Models → Download |
| HuggingFace | Вкладка **HuggingFace** → Download Model |
| llama.cpp | Вкладка **llama.cpp** → выбрать `.gguf` файл → Start |
| Ollama | Вкладка **llama.cpp** → Ollama → Pull Model |

После скачивания вернитесь на вкладку **Модели** и нажмите Refresh.

---

## Маршрутизация по префиксу

Система определяет бэкенд по префиксу в поле `model`:

| Префикс | Бэкенд | Пример |
|---|---|---|
| `foundry::` | Microsoft Foundry Local | `foundry::qwen3-0.6b` |
| `hf::` | HuggingFace Transformers | `hf::google/gemma-2-2b-it` |
| `llama::` | llama.cpp | `llama::llama-server` |
| `ollama::` | Ollama | `ollama::qwen2.5:0.5b` |

Скопируйте префикс кнопкой 📋 и используйте его в запросах:

=== "Python"

    ```python
    import requests

    r = requests.post(
        "http://localhost:9696/api/v1/generate",
        json={"prompt": "Привет!", "model": "foundry::qwen3-0.6b"}
    )
    print(r.json()["content"])
    ```

=== "PowerShell"

    ```powershell
    $r = Invoke-RestMethod -Uri "http://localhost:9696/api/v1/generate" `
        -Method POST -ContentType "application/json" `
        -Body (@{prompt="Привет!"; model="foundry::qwen3-0.6b"} | ConvertTo-Json)
    Write-Host $r.content
    ```

=== "curl"

    ```bash
    curl -X POST http://localhost:9696/api/v1/generate \
      -H "Content-Type: application/json" \
      -d '{"prompt": "Привет!", "model": "foundry::qwen3-0.6b"}'
    ```

---

## Особенности запуска сервисов для моделей

`./start.ps1` запускает не только FastAPI, но и локальные сервисы инференса, если это разрешено в `config.json`.

### Foundry

Microsoft Foundry Local — это локальный сервис Microsoft для запуска оптимизированных моделей через OpenAI-совместимый HTTP API. Служба Foundry может быть запущена без модели в памяти: в этом режиме API доступен, но конкретная модель загрузится только по команде `foundry model load <model-id>` или при включённой автозагрузке.

Настройки:

```json
"foundry_ai": {
  "auto_start": true,
  "auto_load_default": false,
  "default_model": "foundry::qwen3-0.6b-generic-cpu:4",
  "startup_models": [
    "qwen3-0.6b-generic-cpu:4"
  ]
}
```

- `auto_start=false` — `start.ps1` не запускает службу Foundry.
- `auto_load_default=false` — служба стартует без загрузки модели в RAM.
- `startup_models` — список Foundry моделей, которые нужно заранее загрузить в память.

### llama.cpp

llama.cpp — это нативный C/C++ runtime для GGUF моделей. `llama-server.exe` обычно держит одну GGUF модель в памяти на один процесс. Если нужно несколько моделей одновременно, запускайте несколько инстансов на разных портах:

```json
"llama_cpp": {
  "auto_start": true,
  "host": "127.0.0.1",
  "port": 9780,
  "model_path": "~/.models/small.gguf",
  "models": [
    { "model_path": "~/.models/small.gguf", "port": 9780, "auto_start": true },
    { "model_path": "~/.models/code.gguf",  "port": 9781, "auto_start": true }
  ]
}
```

FastAPI UI и общий маршрут `llama::` по умолчанию работают с портом из `llama_cpp.port`. Дополнительные инстансы полезны для ручного обращения к их OpenAI-compatible API: `http://127.0.0.1:9781/v1`.

### Ollama

Ollama — отдельный локальный менеджер моделей. Он скачивает модели командой `ollama pull`, сам хранит их в своём каталоге и отдаёт API на порту `11434`. В этом проекте Ollama не стартует через `start.ps1`; интерфейс и API только подключаются к уже работающему Ollama.

### Hugging Face

Hugging Face — каталог моделей, датасетов и библиотек. В проекте HF используется двумя способами: как локальный кэш скачанных моделей (`~/.cache/huggingface/hub`) и как runtime через Transformers. Такие модели загружаются самим FastAPI процессом, поэтому занимают RAM/VRAM Python-процесса, а не отдельного сервиса.

### Несколько моделей в памяти

Можно держать несколько моделей одновременно, но каждая занимает RAM/VRAM:

- Foundry умеет держать несколько загруженных моделей, если хватает памяти.
- llama.cpp держит одну модель на один `llama-server`; для нескольких моделей нужны разные порты.
- Ollama сам управляет загрузкой и выгрузкой моделей.
- Hugging Face модели загружаются в процесс FastAPI и особенно чувствительны к объёму RAM/VRAM.

Для слабого компьютера лучше запускать Foundry без автозагрузки модели и включать только один основной backend.

---

## Управление моделями через API

Все операции вкладки доступны через REST API.

### Получить список активных моделей

```bash
# Все модели (Foundry + llama.cpp)
GET /api/v1/models

# Только загруженные в Foundry
GET /api/v1/foundry/models/loaded

# Скачанные HuggingFace модели
GET /api/v1/hf/models

# Ollama модели
GET /api/v1/ollama/models

# Статус llama.cpp
GET /api/v1/llama/status
```

### Загрузить модель в память

```bash
# Foundry
POST /api/v1/foundry/models/load
{"model_id": "qwen3-0.6b-generic-cpu:4:4"}

# HuggingFace
POST /api/v1/hf/models/load
{"model_id": "google/gemma-2-2b-it", "device": "auto"}

# llama.cpp
POST /api/v1/llama/start
{"model_path": "~/.models/gemma-2-2b-it-Q6_K.gguf", "port": 9780}
```

### Выгрузить модель из памяти

```bash
# Foundry
POST /api/v1/foundry/models/unload
{"model_id": "qwen3-0.6b-generic-cpu:4:4"}

# HuggingFace
POST /api/v1/hf/models/unload
{"model_id": "google/gemma-2-2b-it"}

# llama.cpp
POST /api/v1/llama/stop
```

### Статус конкретной модели

```bash
GET /api/v1/foundry/models/status/qwen3-0.6b-generic-cpu:4:4
```

**Ответ:**
```json
{
  "success": true,
  "model_id": "qwen3-0.6b-generic-cpu:4:4",
  "loaded": true,
  "cached": true,
  "status": "loaded"
}
```

---

## Рекомендации по выбору модели

| Задача | Рекомендуемая модель | Почему |
|---|---|---|
| Быстрый чат, ответы на вопросы | `foundry::qwen3-0.6b` | Минимальный RAM, быстрый старт |
| Рассуждения и анализ | `ollama::deepseek-r1:7b` | Глубокое понимание |
| Написание кода | `ollama::codellama:7b` | Специализирован на коде |
| Работа с документами (RAG) | `llama::` + большой контекст | Длинный контекст |
| Перевод | `hf::facebook/nllb-200-distilled-600M` | Многоязычность |

!!! warning "Память"
    Одновременно держите в памяти только одну крупную модель. Загрузка второй при занятой RAM приведёт к замедлению или ошибке. Используйте кнопку **Unload** перед переключением.

---

## Что дальше

- [Быстрый старт](getting_started.md) — первый запуск системы
- [Веб-интерфейс](web_interface.md) — описание всех вкладок
- [Конфигурация](configuration.md) — настройка модели по умолчанию
- [llama.cpp — бинарники и утилиты](llama_cpp.md) — описание всех `.exe` файлов в `bin/`
