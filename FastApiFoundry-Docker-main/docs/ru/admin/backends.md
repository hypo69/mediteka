# Бэкенды и модели

Система поддерживает пять AI-бэкендов. Маршрутизация происходит по префиксу в поле `model`.

| Префикс | Бэкенд | Запускается |
|---|---|---|
| `foundry::` | Microsoft Foundry Local | `start.ps1` (если `auto_start=true`) |
| `hf::` | HuggingFace Transformers | внутри FastAPI процесса |
| `llama::` | llama.cpp | `start.ps1` (если `auto_start=true`) |
| `ollama::` | Ollama | отдельно, не управляется |
| `lmstudio::` | LM Studio | отдельно, не управляется |

---

## Автозапуск по умолчанию

`start.ps1` автоматически определяет, какие бэкенды нужно запустить:

1. Если `foundry_ai.auto_start=true` — запускает Foundry
2. Если `llama_cpp.auto_start=true` и задан `model_path` — запускает llama.cpp
3. **Если `auto_start=false`, но `default_model` указывает на этот бэкенд** — `auto_start` включается автоматически

Пример: если `foundry_ai.default_model = "foundry::qwen3-0.6b"` и `auto_start=false` — Foundry всё равно запустится, потому что без него модель недоступна.

---

## Microsoft Foundry Local

### Что это

Локальный сервис Microsoft для ONNX-моделей. Запускается как системный процесс, слушает на динамическом порту (обычно 50477–62376). `start.ps1` автоматически находит порт через `netstat`.

### Установка

```powershell
.\install\install-foundry.ps1
# или вручную:
winget install Microsoft.FoundryLocal
```

### Конфигурация

```json
{
  "foundry_ai": {
    "auto_start": false,
    "auto_load_default": false,
    "default_model": "foundry::qwen3-0.6b-generic-cpu:4",
    "startup_models": ["qwen3-0.6b-generic-cpu:4"],
    "temperature": 0.7,
    "max_tokens": 2048
  }
}
```

| Параметр | Описание |
|---|---|
| `auto_start` | Запускать `foundry service start` при старте `start.ps1`. По умолчанию `false`. |
| `auto_load_default` | Выполнять warm-up `default_model` после старта FastAPI. По умолчанию `false`. |
| `startup_models` | Список моделей для warm-up при старте. Для Foundry это короткий inference-запрос, а не отдельный HTTP load endpoint. |
| `default_model` | Модель по умолчанию для чата. Должна содержать префикс `foundry::`. |

### Почему Microsoft Foundry Local — ключевой компонент

В архитектуре проекта Foundry является самым «своеобразным» и технически сложным компонентом. В то время как Ollama или HuggingFace работают по стандартным сценариям, Foundry диктует свои правила:

1.  **Архитектурная обособленность (System Service)**: 
    В отличие от HuggingFace (внутри процесса) или llama.cpp (дочерний процесс), Foundry — это внешняя системная служба Microsoft. Код не управляет её жизненным циклом напрямую; API должен уметь «обнаруживать» уже запущенную службу.

2.  **Динамическая природа (Dynamic Ports)**: 
    Foundry занимает случайный свободный порт в диапазоне динамических портов Windows. Логика `FoundryClient` включает «прощупывание» портов и анализ вывода `netstat`, что делает его значительно сложнее обычного HTTP-клиента.

3.  **Специфика «Загрузки» (Warm-up vs Load)**: 
    У Foundry Local нет надёжного OpenAI-совместимого эндпоинта для явной загрузки в RAM. В проекте реализован механизм **Warm-up**: отправка короткого холостого запроса (`max_tokens=1`). Если пришел ответ — значит, Foundry «прогрел» модель и она готова в памяти. Это уникальная логика, отсутствующая у других бэкендов.

4.  **Оптимизация под Windows и ONNX**: 
    Foundry — это проприетарное решение от Microsoft, заточенное под **DirectML и ONNX**. Это позволяет запускать модели (Qwen, Phi) с невероятной эффективностью на обычных процессорах и встроенной графике Intel/AMD, где стандартные библиотеки Python могут тормозить. Это превращает проект в мощный инструмент для обычных рабочих станций.

5.  **Сложность выгрузки (Best-effort Unload)**: 
    Программная выгрузка требует комбинации `foundry-local-sdk` и вызовов CLI-команд. В коде это помечено как `best-effort`, так как система борется с ограничениями внешней службы для освобождения памяти пользователя.

**Резюме**: Foundry — это «сердце» интеграции с экосистемой Microsoft. Именно поддержка этого бэкенда делает `FastApiFoundry` уникальным инструментом, эффективно работающим в среде Windows.

### Жизненный цикл модели Foundry

В проекте Foundry управляется как внешний сервис, а не как локальный процесс FastAPI. Логика намеренно простая: найти живой порт, показать доступные модели, проверить модель коротким inference-запросом.

```
foundry service start        ← запуск службы (занимает ~5-20 сек)
        │
foundry model download <id>  ← скачать модель (~0.5-7 GB)
        │
POST /v1/chat/completions    ← warm-up: короткий запрос ping
        │
POST /v1/chat/completions    ← модель готова к запросам
        │
foundry-local-sdk / CLI      ← best-effort unload
        │
foundry service stop         ← остановить службу
```

Важно: `GET /v1/models` в Foundry Local трактуется как список моделей, известных запущенному сервису. Это не надёжный список “загружено в RAM”. Поэтому API FastAPI Foundry маркирует такие модели как `available`, а не `loaded`.

### Где хранятся модели

```
~/.foundry/cache/models/Microsoft/
├── qwen3-0.6b-generic-cpu-4/
│   └── v4/
│       └── model files...
└── deepseek-r1-distill-qwen-7b-generic-cpu-3/
    └── v3/
```

Путь задаётся в `config.json → foundry_ai.models_dir` (по умолчанию `~/.foundry/cache/models`).

### Особенности

- Foundry — **внешний системный сервис Microsoft**, не дочерний процесс FastAPI
- `stop.ps1` не останавливает Foundry по умолчанию (только с флагом `-StopFoundry`)
- FastAPI Foundry не ведёт собственный сложный state-manager для моделей Foundry
- Порт определяется динамически при каждом запуске; источник истины — URL, который реально отвечает на `GET /v1/models`
- Без запущенного Foundry модели с префиксом `foundry::` недоступны

### Скачивание моделей через CLI

```powershell
foundry model list                              # каталог доступных моделей
foundry model download qwen3-0.6b-generic-cpu:4 # скачать
foundry service status                          # узнать живой порт службы
foundry model unload qwen3-0.6b-generic-cpu:4   # best-effort выгрузка через CLI
foundry service stop                            # остановить службу
```

---

## llama.cpp

### Что это

Нативный C++ runtime для GGUF-моделей. Запускается как отдельный процесс `llama-server.exe`, предоставляет OpenAI-совместимый HTTP API на порту 9780.

### Установка бинарника

Бинарник поставляется в `bin/` в виде zip-архива. `start.ps1` автоматически распаковывает его при первом запуске и обновляет при появлении новой версии.

Чтобы добавить новую версию — положите zip в `bin/` и перезапустите `start.ps1`.

### Конфигурация

```json
{
  "llama_cpp": {
    "auto_start": false,
    "model_path": "~/.models/qwen2.5-0.5b-q4_k_m.gguf",
    "port": 9780,
    "host": "127.0.0.1",
    "models": [
      { "model_path": "~/.models/small.gguf", "port": 9780, "auto_start": true },
      { "model_path": "~/.models/code.gguf",  "port": 9781, "auto_start": false }
    ]
  }
}
```

| Параметр | Описание |
|---|---|
| `auto_start` | Запускать `llama-server.exe` при старте `start.ps1`. По умолчанию `false`. |
| `model_path` | Путь к `.gguf` файлу. Поддерживает `~` для домашней директории. |
| `port` | Порт HTTP API (по умолчанию 9780). |
| `models` | Список инстансов для запуска нескольких моделей на разных портах. |

### Один процесс — одна модель

llama.cpp держит **одну модель на один процесс**. Для нескольких моделей одновременно — запускайте несколько инстансов на разных портах через секцию `models`.

### Где хранятся модели

По умолчанию: `~/.models/` (задаётся в `config.json → directories.models`).

Система также ищет модели в:
- `~/.lmstudio/models/` — модели LM Studio
- `~/.lmstudio/models/lmstudio-community/` — модели сообщества LM Studio

### Скачивание GGUF моделей

```powershell
# Через huggingface_hub CLI
pip install huggingface_hub
hf download bartowski/Qwen2.5-0.5B-Instruct-GGUF --include "*Q4_K_M.gguf" --local-dir ~/.models

# Через скрипт проекта
.\install\install-models.ps1
```

| Квантование | Размер | Рекомендация |
|---|---|---|
| Q4_K_M | ~4-5 GB | Лучший баланс — по умолчанию |
| Q5_K_M | ~5-6 GB | Лучше качество при достаточной RAM |
| Q8_0 | ~8-9 GB | Максимальное качество |

### Особенности

- `start.ps1` останавливает предыдущий инстанс на том же порту перед запуском нового
- При падении процесса `start.ps1` автоматически переизвлекает бинарник и повторяет запуск (до 2 попыток)
- `stop.ps1` останавливает llama.cpp по порту из `config.json`
- Путь к `llama-server.exe` ищется в порядке: `LLAMA_SERVER_PATH` env → PATH → `bin/<bin_version>/` → сканирование `bin/`

---

## HuggingFace Transformers

### Что это

Модели HuggingFace загружаются **внутри процесса FastAPI** через библиотеку `transformers`. Отдельный сервер не нужен — модель занимает RAM/VRAM самого FastAPI процесса.

### Конфигурация

```json
{
  "huggingface": {
    "device": "auto",
    "default_max_new_tokens": 512,
    "default_temperature": 0.7
  },
  "directories": {
    "hf_models": "~/.cache/huggingface/hub"
  }
}
```

```env
HF_TOKEN=hf_ваш_токен   # нужен для закрытых моделей (Gemma, Llama, Mistral)
```

| Параметр | Описание |
|---|---|
| `device` | `auto` — GPU если есть, иначе CPU. `cpu` — принудительно CPU. `cuda` — принудительно GPU. |
| `default_max_new_tokens` | Максимальная длина ответа по умолчанию. |
| `directories.hf_models` | Директория кэша моделей. По умолчанию `~/.cache/huggingface/hub`. |

### Где хранятся модели

```
~/.cache/huggingface/hub/
├── models--google--gemma-2-2b-it/
│   └── snapshots/...
└── models--Qwen--Qwen2.5-0.5B-Instruct/
    └── snapshots/...
```

Чтобы перенести кэш на другой диск — задайте в `.env`:
```env
HF_MODELS_DIR=D:\models
```

### Скачивание моделей

```powershell
# Через CLI
.\install\install-huggingface-cli.ps1

# Вручную
pip install huggingface_hub
hf auth login
hf download google/gemma-2-2b-it --local-dir ~/.cache/huggingface/hub
```

### Особенности

- **Нет отдельного сервера** — модель загружается в память FastAPI при первом запросе
- Первый запрос к HF-модели медленный (загрузка в RAM/VRAM)
- Для закрытых моделей (Gemma, Llama, Mistral) нужен `HF_TOKEN` и принятая лицензия на HuggingFace
- HF-модели особенно чувствительны к объёму RAM/VRAM — на слабом железе используйте Foundry или llama.cpp
- `auto_start` не применяется — HF-модели не требуют предварительного запуска сервера

### Требования к памяти

| Размер модели | RAM (CPU) | VRAM (GPU) |
|---|---|---|
| 0.5B параметров | ~2 GB | ~1 GB |
| 2B параметров | ~6 GB | ~4 GB |
| 7B параметров | ~16 GB | ~8 GB |
| 13B параметров | ~32 GB | ~16 GB |

---

## Ollama

### Что это

Отдельный менеджер моделей. Ollama скачивает модели командой `ollama pull`, хранит их в своём каталоге и предоставляет API на порту 11434.

### Конфигурация

Ollama **не управляется** `start.ps1` — запускайте его отдельно. FastAPI только подключается к уже работающему Ollama.

```powershell
# Установка
winget install Ollama.Ollama

# Скачать модель
ollama pull qwen2.5:0.5b
ollama pull deepseek-r1:7b

# Запустить сервис
ollama serve
```

---

## LM Studio

### Что это

GUI-приложение для запуска GGUF-моделей. Предоставляет OpenAI-совместимый API на порту 1234.

### Конфигурация

```json
{
  "lmstudio": {
    "base_url": "http://localhost:1234",
    "default_model": "",
    "request_timeout_sec": 300
  }
}
```

LM Studio **не управляется** `start.ps1` — запускайте его отдельно через GUI.

```powershell
# Установка
.\install\Install-LMStudio.ps1
```

---

## Несколько бэкендов одновременно

Можно держать несколько бэкендов активными одновременно:

```json
{
  "foundry_ai": { "auto_start": true },
  "llama_cpp": {
    "auto_start": true,
    "model_path": "~/.models/small.gguf"
  }
}
```

Пользователь выбирает нужный бэкенд через префикс в поле `model`:
- `foundry::qwen3-0.6b` → Foundry
- `llama::llama-server` → llama.cpp
- `hf::google/gemma-2-2b-it` → HuggingFace

!!! warning "Память"
    Каждый бэкенд занимает RAM. На слабом железе держите активным только один.
    Для экономии памяти: `auto_start=false` для неиспользуемых бэкендов.
