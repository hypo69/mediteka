# API Reference — полный справочник

Базовый URL: `http://localhost:9696`  
Swagger UI: [`http://localhost:9696/docs`](http://localhost:9696/docs)

!!! tip "Интерактивный Swagger"
    Все методы можно вызвать прямо из браузера через Swagger UI.
    Откройте `http://localhost:9696/docs` — там живые формы для каждого endpoint.

---

## Префиксы моделей

| Префикс | Бэкенд |
|---|---|
| `foundry::model-id` | Microsoft Foundry Local |
| `hf::model-id` | HuggingFace Transformers |
| `llama::path/to/model.gguf` | llama.cpp |
| `ollama::model-name` | Ollama |
| `lmstudio::model-key` | LM Studio |

---

## 🏥 Health & Restart

### `POST` /api/v1/restart/{service}

Restart a background service.

**Path параметры:**

| Параметр | Тип |
|---|---|
| `service` | `str` |

**Тело запроса / параметры:**

| Поле | Описание |
|---|---|
| | service: One of 'foundry', 'llama', 'docs', 'rag'. |

**Ответ:**

> dict: success, message.

---

### `GET` /api/v1/health

Проверка здоровья сервиса.

**Ответ:**

> dict: status, foundry_status, llama_status, hf_status, ollama_status,
> docs_status, rag_status, timestamp.

---

## ⚡ Generate

### `POST` /api/v1/generate

Generate text via the AI Assistant orchestrator.

**Тело запроса / параметры:**

| Поле | Описание |
|---|---|
| | request: JSON body with fields: |
| `prompt` (str) | Input text (required). |
| `model` (str) | Model ID with prefix, e.g. 'foundry::qwen3-0.6b'. |
| `temperature` (float) | Generation temperature (default: 0.7). |
| `max_tokens` (int) | Max tokens (default: 1000). |
| `use_rag` (bool) | Inject RAG context (default: False). |
| `top_k` (int) | RAG results count (default: from config). |
| `translate_model_dialog` (bool) | Translate prompt→EN and response→user lang. |
| `user_language` (str|null) | User language ISO 639-1. null = auto-detect. |

**Ответ:**

> dict: success, content, model, usage, user_language, translated (bool)

---

## 🤖 AI (расширенная генерация)

### `POST` /api/v1/ai/generate

Generate text via AI Assistant orchestrator (all backends).

---

### `POST` /api/v1/ai/generate/stream

Стриминговая генерация текста (Foundry only).

---

### `POST` /api/v1/ai/chat

Chat with message history via AI Assistant orchestrator (all backends).

---

### `POST` /api/v1/ai/chat/stream

Стриминговый чат с автоматическим сохранением истории после завершения.

---

### `POST` /api/v1/ai/optimize

Оптимизация параметров генерации — не реализовано.

---

## 💬 Chat (сессии)

### `POST` /api/v1/chat/start

Start a new chat session.

**Тело запроса / параметры:**

| Поле | Описание |
|---|---|
| | request: JSON body with fields: |
| `model` (str) | Model ID (default: 'default'). |

**Ответ:**

> dict: success, session_id (UUID), model, message.

---

### `POST` /api/v1/chat/message

Send a message to an existing chat session.

**Тело запроса / параметры:**

| Поле | Описание |
|---|---|
| | request: JSON body with fields: |
| `session_id` (str) | Session ID (required). |
| `message` (str) | Message text (required). |
| `model` (str) | Model ID (optional). |
| `temperature` (float) | Sampling temperature (default: 0.7). |
| `max_tokens` (int) | Max tokens (default: 2048). |
| `source_lang` (str) | Input language (default: 'auto'). |
| `locale` (str) | Reply language override ('ru', 'he', etc.). |

**Ответ:**

> dict: success, response, session_id.
> Raises:
> HTTPException 400: Invalid session_id or empty message.

---

### `POST` /api/v1/chat/stream

Send a message with SSE streaming response.

**Тело запроса / параметры:**

| Поле | Описание |
|---|---|
| | request: JSON body with fields: |
| `session_id` (str) | Session ID (required). |
| `message` (str) | Message text (required). |
| `model` (str) | Model ID (optional). |
| `temperature` (float) | Sampling temperature (default: 0.7). |
| `max_tokens` (int) | Max tokens (default: 2048). |

**Ответ:**

> StreamingResponse: SSE stream with {chunk} events and final {done: True}.
> Raises:
> HTTPException 400: Invalid session_id or empty message.

---

### `GET` /api/v1/chat/history/{session_id}

Get in-memory session history.

**Path параметры:**

| Параметр | Тип |
|---|---|
| `session_id` | `str` |

**Тело запроса / параметры:**

| Поле | Описание |
|---|---|
| | session_id: Chat session UUID. |

**Ответ:**

> dict: success, session_id, history (list of {role, content}).
> Raises:
> HTTPException 404: Session not found.

---

### `DELETE` /api/v1/chat/session/{session_id}

Delete an in-memory chat session.

**Path параметры:**

| Параметр | Тип |
|---|---|
| `session_id` | `str` |

**Тело запроса / параметры:**

| Поле | Описание |
|---|---|
| | session_id: Chat session UUID. |

**Ответ:**

> dict: success, message.
> Raises:
> HTTPException 404: Session not found.

---

### `POST` /api/v1/chat/history/save

Persist chat history to disk.

**Тело запроса / параметры:**

| Поле | Описание |
|---|---|
| | request: JSON body with fields: |
| `messages` (list) | List of {role, content} (required). |
| `session_id` (str) | Session UUID (generated if empty). |
| `model` (str) | Model ID (optional). |
| `title` (str) | Dialog title (optional). |
| `aborted` (bool) | Whether chat was aborted (default: False). |

**Ответ:**

> dict: success, file (absolute path), session_id.
> Raises:
> HTTPException 400: messages missing or empty.

---

### `GET` /api/v1/chat/history/list

List saved dialog files from disk, newest first.

**Тело запроса / параметры:**

| Поле | Описание |
|---|---|
| `limit` (int) | Max number of entries to return (default: 50). |
| `offset` (int) | Pagination offset (default: 0). |

**Ответ:**

> dict: success, dialogs (list of metadata), total, dir.

---

### `GET` /api/v1/chat/history/file/{filename}

Load a single saved dialog from disk.

**Path параметры:**

| Параметр | Тип |
|---|---|
| `filename` | `str` |

**Тело запроса / параметры:**

| Поле | Описание |
|---|---|
| | filename: JSON filename (e.g. 'uuid_1234567890.json'). |

**Ответ:**

> dict: success + full dialog payload.
> Raises:
> HTTPException 400: Unsafe filename.

---

### `POST` /api/v1/chat/history/cleanup

Delete old and oversized dialog files.

**Тело запроса / параметры:**

| Поле | Описание |
|---|---|
| | request: Optional JSON body with fields: |
| `retention_days` (int) | Override retention period. |
| `max_size_mb` (int) | Override size limit. |

**Ответ:**

> dict: success, deleted (count), freed_bytes, remaining.

---

### `GET` /api/v1/chat/models

List chat models without probing Foundry.

**Ответ:**

> dict: success, models (list of {id, name, type, size}), count.

---

## 📋 Models (универсальные)

### `POST` /api/v1/models/{model_id:path}/load

Prepare a model by prefixed model id.

For Foundry this performs a warm-up inference request, because Foundry Local
does not expose a reliable HTTP load-into-RAM endpoint.

**Тело запроса / параметры:**

| Поле | Описание |
|---|---|
| | model_id: Provider-prefixed model id, e.g.: |
| | foundry::qwen3-0.6b-generic-cpu:4 |
| | hf::Qwen/Qwen2.5-0.5B-Instruct |
| | llama::D:/models/gemma-4-E4B-it-Q4_K_M.gguf |
| | ollama::qwen2.5:0.5b |

**Ответ:**

> dict: success, model_id, provider, status on success; success=False, error on failure.

---

### `POST` /api/v1/models/{model_id:path}/unload

Unload a model from memory by prefixed model id.

**Тело запроса / параметры:**

| Поле | Описание |
|---|---|
| | model_id: Provider-prefixed model id in the URL path. |

**Ответ:**

> dict: success, model_id, provider on success; success=False, error on failure.

---

### `GET` /api/v1/models

Get all local models from all providers with provider prefixes.

**Ответ:**

> dict: success, models (list), count, by_provider (dict with counts per provider).

---

### `GET` /api/v1/models/connected

Get models currently ready/connected across providers.

For Foundry, this reports models available from the running service, not a
guaranteed loaded-in-RAM state.

**Ответ:**

> dict: success, models (list), count.

---

## 🔗 OpenAI-совместимые

### `GET` /v1/v1/models

Get models in OpenAI-compatible format.

**Ответ:**

> OpenAI-compatible response dictionary

---

### `POST` /v1/v1/chat/completions

OpenAI-compatible chat completions endpoint for external tools.

---

## 🏭 Foundry — статус

### `GET` /api/v1/foundry/status

Получить статус сервиса Foundry

---

### `GET` /api/v1/foundry/models/list

Получить список всех доступных моделей

---

## 🏭 Foundry — управление сервисом

### `GET` /api/v1/foundry/status

Получение статуса службы Foundry через системный агент.

**Ответ:**

> FoundryStatus: Объект со статусом работы, портом и URL.

---

### `POST` /api/v1/foundry/start

Запуск службы Foundry через системный агент.

**Тело запроса / параметры:**

| Поле | Описание |
|---|---|
| `background_tasks` (BackgroundTasks) | Фоновые задачи FastAPI. |

**Ответ:**

> dict: Статус выполнения и сообщение.

---

### `POST` /api/v1/foundry/stop

Остановка службы Foundry через системный агент.

**Ответ:**

> dict: Сообщение о результате операции.

---

### `POST` /api/v1/foundry/reset-breaker

Ручной сброс предохранителя для команд Foundry.

---

## 🏭 Foundry — модели

### `POST` /api/v1/foundry/models/auto-load-default

Warm up the default model from config.json.

For Foundry, "load" means a tiny inference request that makes the model ready
for normal requests.

**Ответ:**

> dict: success, model_id, message on success; success=False on failure.

---

### `GET` /api/v1/foundry/models

Alias for /available.

---

### `GET` /api/v1/foundry/models/

Alias for /available.

---

### `GET` /api/v1/foundry/models/catalog

List the full Foundry model catalog via CLI (foundry model list).

**Ответ:**

> dict: success, models (list with id, alias, device, task, size, license, cached),
> count, source.

---

### `GET` /api/v1/foundry/models/available

List models reported by the running Foundry service.

Foundry Local does not expose a reliable separate "loaded in RAM" list here.
Treat these as available/registered models.

**Ответ:**

> dict: success, models, count, source ('foundry-api' or 'hardcoded').

---

### `GET` /api/v1/foundry/models/cached

List models downloaded to the local Foundry cache on disk.

**Ответ:**

> dict: success, models (list of model_id strings), items (full model dicts),
> count, cache_dir.

---

### `GET` /api/v1/foundry/models/loaded

Compatibility alias for models reported by Foundry.

Foundry Local does not reliably separate available from loaded in this API.

**Ответ:**

> dict: success, models (list of {id, name, status}), count.

---

### `POST` /api/v1/foundry/models/download

Download a model to the Foundry cache via CLI.

**Тело запроса / параметры:**

| Поле | Описание |
|---|---|
| | request: {"model_id": "qwen3-0.6b-generic-cpu:4"} |

**Ответ:**

> dict: success, model_id, status ('downloading'/'already_cached'), pid.

---

### `GET` /api/v1/foundry/models/download/status/{pid}

Check status of a background download process.

**Path параметры:**

| Параметр | Тип |
|---|---|
| `pid` | `str` |

**Тело запроса / параметры:**

| Поле | Описание |
|---|---|
| | pid: PID returned by /download. |

**Ответ:**

> dict: success, pid, model_id, status ('downloading'/'done'/'error').

---

### `POST` /api/v1/foundry/models/load

Warm up a model in Foundry.

The client sends a short chat completion request. This is intentionally simpler
than trying to track an internal loaded state.

**Тело запроса / параметры:**

| Поле | Описание |
|---|---|
| | request: {"model_id": "qwen3-0.6b-generic-cpu:4"} |

**Ответ:**

> dict: success, model_id, message on success; success=False, error on failure.

---

### `POST` /api/v1/foundry/models/unload

Best-effort unload of a Foundry model.

**Тело запроса / параметры:**

| Поле | Описание |
|---|---|
| | request: {"model_id": "qwen3-0.6b-generic-cpu:4"} |

**Ответ:**

> dict: success, model_id, message on success; success=False, error on failure.

---

### `GET` /api/v1/foundry/models/status/{model_id:path}

Get model status: available in service and/or cached on disk.

**Тело запроса / параметры:**

| Поле | Описание |
|---|---|
| | model_id: Model identifier (path parameter). |

**Ответ:**

> dict: success, model_id, available (bool), cached (bool), status.

---

### `POST` /api/v1/foundry/models/completions

Text completion через Foundry /v1/completions.

**Тело запроса / параметры:**

| Поле | Описание |
|---|---|
| | request: {"prompt": str, "model": str (optional), |
| | "temperature": float, "max_tokens": int, ...} |

**Ответ:**

> dict: OpenAI-совместимый ответ или success=False.

---

### `POST` /api/v1/foundry/models/embeddings

Эмбеддинги через Foundry /v1/embeddings.

**Тело запроса / параметры:**

| Поле | Описание |
|---|---|
| | request: {"input": str | list[str], "model": str (optional)} |

**Ответ:**

> dict: success, data (list of embedding vectors), usage.

---

## 🤗 HuggingFace

### `GET` /api/v1/hf/hub/models

Список моделей пользователя с HuggingFace Hub.

**Ответ:**

> dict: success, username, user_models (list), public_models (list);
> success=False, error, user_models=[], public_models if no token.

---

### `GET` /api/v1/hf/models

Список скачанных и загруженных HF моделей.

**Ответ:**

> dict: success, downloaded (list), loaded (list).

---

### `POST` /api/v1/hf/models/download

Download model from HuggingFace Hub (blocking, no progress).

**Тело запроса / параметры:**

| Поле | Описание |
|---|---|
| | request: {model_id (str), token (str, optional)} |

**Ответ:**

> dict: success, model_id, path on success; success=False, error on failure.
> Raises:
> HTTPException 400: model_id not provided.

---

### `GET` /api/v1/hf/models/download/stream

Download HuggingFace model with SSE progress stream.

**Тело запроса / параметры:**

| Поле | Описание |
|---|---|
| | model_id: HuggingFace model ID, e.g. 'Qwen/Qwen2.5-0.5B-Instruct'. |
| | token:    Optional HF token (overrides HF_TOKEN env var). |

**Ответ:**

> StreamingResponse: text/event-stream

---

### `POST` /api/v1/hf/models/load

Загрузить скачанную модель в память для inference.

**Тело запроса / параметры:**

| Поле | Описание |
|---|---|
| | request: JSON body с полями: |
| `model_id` (str) | HuggingFace model ID (обязательно). |
| `device` (str) | 'auto', 'cpu', 'cuda' (default: 'auto'). |

**Ответ:**

> dict: success, model_id, device on success; success=False, error on failure.
> Raises:
> HTTPException 400: model_id не передан.

---

### `POST` /api/v1/hf/models/unload

Выгрузить модель из памяти (освободить RAM/VRAM).

**Тело запроса / параметры:**

| Поле | Описание |
|---|---|
| | request: JSON body с полями: |
| `model_id` (str) | HuggingFace model ID (обязательно). |

**Ответ:**

> dict: success, model_id on success; success=False, error on failure.
> Raises:
> HTTPException 400: model_id не передан.

---

### `POST` /api/v1/hf/generate

Генерация текста через локальную HF модель.

**Тело запроса / параметры:**

| Поле | Описание |
|---|---|
| | request: JSON body с полями: |
| `model_id` (str) | ID модели (должна быть загружена или скачана). |
| `prompt` (str) | Входной текст. |
| `max_new_tokens` (int) | Максимум новых токенов (default: 512). |
| `temperature` (float) | Температура (default: 0.7). |

**Ответ:**

> dict: success, content, model on success; success=False, error on failure.
> Raises:
> HTTPException 400: model_id или prompt не переданы.

---

### `GET` /api/v1/hf/status

Статус HuggingFace интеграции — доступность библиотек.

**Ответ:**

> dict: success, transformers ({available, version}),
> huggingface_hub ({available, version}),
> torch ({available, version, cuda}),

---

## 🦙 llama.cpp

### `GET` /api/v1/llama/status

Статус llama.cpp сервера.

---

### `POST` /api/v1/llama/models/copy

Скопировать .gguf модель в ~/.models.

---

### `POST` /api/v1/llama/start

Запустить llama.cpp сервер с указанной GGUF моделью.

---

### `POST` /api/v1/llama/stop

Остановить llama.cpp сервер.

---

### `GET` /api/v1/llama/props

Параметры запущенного llama-server: модель, контекст, потоки, n_gpu_layers.

**Ответ:**

> dict: success, props (model_path, n_ctx, n_threads, n_gpu_layers, ...)

---

### `GET` /api/v1/llama/slots

Активные слоты инференса llama-server.

**Ответ:**

> dict: success, slots (list)

---

### `GET` /api/v1/llama/metrics

Prometheus-метрики llama-server: токены/сек, TTFT, очередь.

**Ответ:**

> Response: text/plain Prometheus metrics или JSON с ошибкой.

---

### `POST` /api/v1/llama/completion

Нативная генерация llama-server (быстрее, больше параметров).

**Тело запроса / параметры:**

| Поле | Описание |
|---|---|
| | request: JSON body — любые параметры llama-server /completion. |
| `prompt` (str) | Входной текст (обязательно). |
| `temperature` (float) | Температура (default: 0.7). |
| `top_k` (int) | Top-K sampling (default: 40). |
| `top_p` (float) | Top-P sampling (default: 0.95). |
| `repeat_penalty` (float) | Штраф за повторения (default: 1.1). |
| `n_predict` (int) | Макс. токенов (default: 512). |
| `stop` (list[str]) | Стоп-последовательности. |
| `stream` (bool) | Стриминг (default: false). |

**Ответ:**

> dict: success, content, tokens_predicted, tokens_evaluated, ...

---

### `POST` /api/v1/llama/tokenize

Токенизация текста через llama-server.

**Тело запроса / параметры:**

| Поле | Описание |
|---|---|
| | request: {"content": "текст для токенизации"} |

**Ответ:**

> dict: success, tokens (list[int])

---

### `POST` /api/v1/llama/detokenize

Детокенизация (токены → текст) через llama-server.

**Тело запроса / параметры:**

| Поле | Описание |
|---|---|
| | request: {"tokens": [1, 2, 3, ...]} |

**Ответ:**

> dict: success, content (str)

---

### `POST` /api/v1/llama/v1/completions

OpenAI-совместимый text completion через llama-server.

**Тело запроса / параметры:**

| Поле | Описание |
|---|---|
| | request: OpenAI completions body (prompt, max_tokens, temperature, ...). |

**Ответ:**

> dict: OpenAI-совместимый ответ.

---

### `POST` /api/v1/llama/v1/embeddings

Получить эмбеддинги через llama-server.

**Тело запроса / параметры:**

| Поле | Описание |
|---|---|
| | request: {"input": "текст или список текстов", "model": "..."} |

**Ответ:**

> dict: success, data (list of embedding vectors), usage.

---

### `POST` /api/v1/llama/v1/chat/completions

OpenAI-совместимый chat completion через llama-server.

**Тело запроса / параметры:**

| Поле | Описание |
|---|---|
| | request: OpenAI chat completions body (messages, model, temperature, ...). |

**Ответ:**

> dict: OpenAI-совместимый ответ.

---

### `GET` /api/v1/llama/v1/models

Список моделей загруженных в llama-server (OpenAI-совместимый).

**Ответ:**

> dict: success, data (list of model objects), model_name (str, первая модель).

---

### `GET` /api/v1/llama/models

Сканировать .gguf файлы в ~/.models, ~/.ai-assist/gguf_models, ~/.lmstudio/models и опциональном extra_dir.

---

## 🐋 Ollama

### `GET` /api/v1/ollama/status

Ollama server status — running, version, URL.

**Ответ:**

> dict: success, running (bool), url, openai_url, version.

---

### `GET` /api/v1/ollama/models

List locally available Ollama models.

**Ответ:**

> dict: success, models (list of {name, size_gb, modified_at, digest}), count.

---

### `POST` /api/v1/ollama/models/pull

Pull (download) a model from Ollama Hub.

**Тело запроса / параметры:**

| Поле | Описание |
|---|---|
| | request: JSON body с полями: |
| `model` (str) | Model name, e.g. 'qwen2.5:0.5b' (обязательно). |

**Ответ:**

> dict: success, model, status on success; success=False, error on failure.
> Raises:
> HTTPException 400: model не передан.

---

### `POST` /api/v1/ollama/models/delete

Delete a local Ollama model to free disk space.

**Тело запроса / параметры:**

| Поле | Описание |
|---|---|
| | request: JSON body с полями: |
| `model` (str) | Model name, e.g. 'qwen2.5:0.5b' (обязательно). |

**Ответ:**

> dict: success, model on success; success=False, error on failure.
> Raises:
> HTTPException 400: model не передан.

---

### `POST` /api/v1/ollama/generate

Generate text via Ollama.

**Тело запроса / параметры:**

| Поле | Описание |
|---|---|
| | request: JSON body с полями: |
| `model` (str) | Model name (обязательно). |
| `prompt` (str) | Input text (обязательно). |
| `max_tokens` (int) | Max tokens to generate (default: 512). |
| `temperature` (float) | Sampling temperature (default: 0.7). |

**Ответ:**

> dict: success, content, model on success; success=False, error on failure.
> Raises:
> HTTPException 400: model или prompt не переданы.

---

## 🎛️ LM Studio

### `GET` /api/v1/lmstudio/status

LM Studio server status.

---

### `GET` /api/v1/lmstudio/models

List LM Studio models.

---

### `POST` /api/v1/lmstudio/models/load

Load a model in LM Studio.

---

### `POST` /api/v1/lmstudio/models/unload

Unload a loaded LM Studio model instance.

---

### `POST` /api/v1/lmstudio/models/download

Start an LM Studio model download job.

---

### `GET` /api/v1/lmstudio/models/download/status/{job_id}

Get LM Studio model download status.

**Path параметры:**

| Параметр | Тип |
|---|---|
| `job_id` | `str` |

---

### `POST` /api/v1/lmstudio/generate

Generate text through LM Studio /api/v1/chat.

---

## 🔍 RAG

### `GET` /api/v1/rag/status

Получение статуса системы RAG.

**Ответ:**

> dict: Информация о состоянии: enabled, index_dir, model, chunk_size, total_chunks.

---

### `PUT` /api/v1/rag/config

Обновление конфигурации системы RAG.

**Тело запроса / параметры:**

| Поле | Описание |
|---|---|
| `config` (RAGConfig) | Модель данных с новыми настройками. |

**Ответ:**

> dict: Статус выполнения операции.

---

### `POST` /api/v1/rag/search

Выполнение поиска в системе RAG.

**Тело запроса / параметры:**

| Поле | Описание |
|---|---|
| `request` (RAGSearchRequest) | Запрос с текстом и параметром top_k. |

**Ответ:**

> dict: Список результатов с контентом и оценками схожести.

---

### `POST` /api/v1/rag/query

Run retrieval + prompt + generation with optional SSE streaming.

---

### `POST` /api/v1/rag/rebuild

Пересборка векторного индекса.

**Ответ:**

> dict: Статус запуска процесса пересборки.

---

### `POST` /api/v1/rag/index

Индексация одного документа или архива через RAGPipeline.

---

### `POST` /api/v1/rag/index/stream

Индексация одного файла/архива с SSE-прогрессом по всему пайплайну.

**Тело запроса / параметры:**

| Поле | Описание |
|---|---|
| `file` (UploadFile) | Файл для индексации. |

**Ответ:**

> StreamingResponse: text/event-stream с JSON-событиями.

---

### `POST` /api/v1/rag/index/batch

Пакетная индексация нескольких файлов или архивов за один запрос.

**Тело запроса / параметры:**

| Поле | Описание |
|---|---|
| `files` (List[UploadFile]) | Список файлов. Поддерживаются все форматы |
| | включая zip, tar, tar.gz, tgz, 7z, rar. |

**Ответ:**

> dict: success, indexed, total, results, errors.

---

### `POST` /api/v1/rag/clear

Очистка файлов индекса в настроенной директории.

**Ответ:**

> dict: Количество удаленных файлов.

---

### `GET` /api/v1/rag/dirs

Получение списка директорий, доступных для индексации.

**Ответ:**

> dict: Список путей с количеством найденных текстовых файлов.

---

### `GET` /api/v1/rag/cwd

Получение текущей рабочей директории сервера.

---

### `GET` /api/v1/rag/browse

Просмотр файловой системы для выбора папок.

**Тело запроса / параметры:**

| Поле | Описание |
|---|---|
| `path` (str) | Абсолютный путь для обзора. По умолчанию домашняя папка. |

**Ответ:**

> dict: Список вложенных папок и информация о текущем пути.
> Raises:
> HTTPException: Если путь не существует или не является директорией.

---

### `GET` /api/v1/rag/profiles

Получение списка всех профилей RAG в директории ~/.aiassistant/rag/.

**Ответ:**

> dict: success, profiles.

---

### `POST` /api/v1/rag/profiles/load

Переключение активного профиля RAG.

**Тело запроса / параметры:**

| Поле | Описание |
|---|---|
| `request` (dict) | Тело запроса с полем 'name'. |

**Ответ:**

> dict: Результат загрузки и путь к новому индексу.

---

### `POST` /api/v1/rag/profiles/{name}/activate

Подключить RAG профиль и сделать его активным.

**Path параметры:**

| Параметр | Тип |
|---|---|
| `name` | `str` |

---

### `POST` /api/v1/rag/profiles/deactivate

Отключить использование RAG без удаления индексов с диска.

---

### `DELETE` /api/v1/rag/profiles/{name}

Удаление профиля RAG с диска.

**Path параметры:**

| Параметр | Тип |
|---|---|
| `name` | `str` |

**Тело запроса / параметры:**

| Поле | Описание |
|---|---|
| `name` (str) | Имя профиля. |

**Ответ:**

> dict: Статус удаления.

---

### `POST` /api/v1/rag/build

Создание векторного индекса из локальной директории.

**Тело запроса / параметры:**

| Поле | Описание |
|---|---|
| `request` (RAGBuildRequest) | Параметры сборки (путь, модель, размер чанка). |

**Ответ:**

> dict: Статистика сборки: количество сегментов, признак пересборки.

---

### `POST` /api/v1/rag/extract/file

Извлечение текста из загруженного файла.

**Тело запроса / параметры:**

| Поле | Описание |
|---|---|
| `file` (UploadFile) | Файл для обработки. |

**Ответ:**

> dict: Извлеченный текст и метаданные.

---

### `POST` /api/v1/rag/extract/url

Извлечение контента с веб-страницы.

**Тело запроса / параметры:**

| Поле | Описание |
|---|---|
| `request` (ExtractURLRequest) | URL и параметры парсинга (JS, изображения). |

**Ответ:**

> dict: Текстовое содержимое страницы.

---

### `GET` /api/v1/rag/extract/formats

Получение списка поддерживаемых форматов для извлечения текста.

**Ответ:**

> dict: Список расширений.

---

### `GET` /api/v1/rag/documents

Список всех документов в хранилище.

**Ответ:**

> dict: success, documents — список с id, title, chunk_count, updated_at.

---

### `POST` /api/v1/rag/documents

Добавить документ и проиндексировать его инкрементально.

**Тело запроса / параметры:**

| Поле | Описание |
|---|---|
| `request` (DocumentAddRequest) | title, content, source_path. |

**Ответ:**

> dict: success, doc_id, chunks_added.

---

### `GET` /api/v1/rag/documents/{doc_id}

Получить документ по id.

**Path параметры:**

| Параметр | Тип |
|---|---|
| `doc_id` | `str` |

**Тело запроса / параметры:**

| Поле | Описание |
|---|---|
| `doc_id` (int) | Document id. |

**Ответ:**

> dict: success, document.

---

### `PUT` /api/v1/rag/documents/{doc_id}

Обновить документ и переиндексировать если контент изменился.

**Path параметры:**

| Параметр | Тип |
|---|---|
| `doc_id` | `str` |

**Тело запроса / параметры:**

| Поле | Описание |
|---|---|
| `doc_id` (int) | Document id. |
| `request` (DocumentUpdateRequest) | title, content. |

**Ответ:**

> dict: success, chunks_added, changed.

---

### `DELETE` /api/v1/rag/documents/{doc_id}

Удалить документ и деактивировать его чанки.

**Path параметры:**

| Параметр | Тип |
|---|---|
| `doc_id` | `str` |

**Тело запроса / параметры:**

| Поле | Описание |
|---|---|
| `doc_id` (int) | Document id. |

**Ответ:**

> dict: success.

---

### `POST` /api/v1/rag/documents/{doc_id}/reindex

Принудительно переиндексировать один документ.

**Path параметры:**

| Параметр | Тип |
|---|---|
| `doc_id` | `str` |

**Тело запроса / параметры:**

| Поле | Описание |
|---|---|
| `doc_id` (int) | Document id. |

**Ответ:**

> dict: success, chunks_added.

---

### `POST` /api/v1/rag/compact

Перестроить FAISS индекс из активных чанков (удалить мёртвые векторы).

**Ответ:**

> dict: success, vectors_before, vectors_after.

---

### `POST` /api/v1/rag/migrate/index-id-map

Migrate legacy FAISS/chunks.json profile to SQLite-backed IndexIDMap.

---

### `GET` /api/v1/rag/documents/stats

Статистика хранилища документов и FAISS индекса.

**Ответ:**

> dict: documents, active_chunks, inactive_chunks, faiss_vectors, compact_recommended.

---

## 🕵️ Agent

### `GET` /api/v1/agent/list

Список зарегистрированных агентов

---

### `GET` /api/v1/agent/{agent_name}/tools

Список инструментов конкретного агента

**Path параметры:**

| Параметр | Тип |
|---|---|
| `agent_name` | `str` |

---

### `POST` /api/v1/agent/run

Запустить агента.

---

## 🔌 MCP PowerShell

### `GET` /api/v1/mcp-powershell/servers

List all MCP servers from settings.json with their status

---

### `POST` /api/v1/mcp-powershell/servers/{name}/start

Start an MCP server by name

**Path параметры:**

| Параметр | Тип |
|---|---|
| `name` | `str` |

---

### `POST` /api/v1/mcp-powershell/servers/{name}/stop

Stop an MCP server by name

**Path параметры:**

| Параметр | Тип |
|---|---|
| `name` | `str` |

---

### `GET` /api/v1/mcp-powershell/servers/{name}/status

Status of a specific MCP server

**Path параметры:**

| Параметр | Тип |
|---|---|
| `name` | `str` |

---

### `GET` /api/v1/mcp-powershell/settings

Get the contents of mcp-powershell-servers/settings.json

---

### `POST` /api/v1/mcp-powershell/settings

Save mcp-powershell-servers/settings.json

---

## 🔌 MCP Agent

### `GET` /api/v1/mcp-agent/tools

List all MCP tools discovered from local MCP servers.

**Ответ:**

> dict: success, tools list, total count.
> Example response:
> {

---

### `POST` /api/v1/mcp-agent/refresh-tools

Re-discover tools from all MCP servers in settings.json.

**Ответ:**

> dict: success, total discovered tools count.

---

### `GET` /api/v1/mcp-agent/servers

List MCP servers with their discovered tool counts.

**Ответ:**

> dict: success, servers list with tool counts per server.
> Example response:
> {

---

## ⚙️ Config

### `GET` /api/v1/config

Получить конфигурацию для веб-интерфейса

---

### `PATCH` /api/v1/config

Частичное обновление конфигурации. Поддерживает dot-notation: 'foundry_ai.default_model'

---

### `POST` /api/v1/config

Сохранить конфигурацию

---

### `GET` /api/v1/config/env-raw

Чтение .env файла как сырой текст для редактора

---

### `POST` /api/v1/config/env-raw

Запись .env файла из редактора (сырой текст)

---

### `GET` /api/v1/config/raw

Чтение config.json как сырой текст для редактора

---

### `POST` /api/v1/config/raw

Запись config.json из редактора (сырой текст).

---

### `POST` /api/v1/config/env

Сохранение одной переменной окружения в .env файл.

---

### `GET` /api/v1/config/export

Экспорт ВСЕХ настроек проекта в один JSON: config.json + .env + MCP конфиги

---

### `GET` /api/v1/config/provider-keys

Читает ключи провайдеров из .env. Возвращает замаскированные значения.

---

### `POST` /api/v1/config/provider-keys

Сохраняет ключи провайдеров в .env.

---

### `GET` /api/v1/config/extension-export

Экспортирует ключи провайдеров в формат расширения (chrome.storage.sync).

---

### `POST` /api/v1/config/extension-import

Импортирует ключи из формата расширения (v1/v2) в .env.

---

### `GET` /api/v1/config/provider-models/{provider}

Proxy: fetch model list from external provider API server-side to avoid CORS.

**Path параметры:**

| Параметр | Тип |
|---|---|
| `provider` | `str` |

---

### `POST` /api/v1/config/import

Импорт полного бэкапа настроек. merge=True — слияние, False — полная замена

---

## 📜 Logs

### `GET` /api/v1/logs/files

Return available log files with size info.

---

### `GET` /api/v1/logs/settings

Return log storage and retention settings.

---

### `GET` /api/v1/logs/health

Return simple warning/error metrics for the settings page.

---

### `POST` /api/v1/logs/settings

Persist log viewer retention settings to config.json and apply them.

---

### `GET` /api/v1/logs

Return filtered log lines from the requested file.

---

### `POST` /api/v1/logs/clear

Truncate a log file.

---

### `GET` /api/v1/logs/download

Download a log file.

---

## 🔄 Converter

### `GET` /api/v1/converter/status

Проверить доступность зависимостей конвертера

---

### `POST` /api/v1/converter/convert

Конвертировать .gguf файл в ONNX.

---

## 📊 System Stats

### `GET` /api/v1/system/stats

RAM, CPU, disk and GPU usage.

**Ответ:**

> dict: success, ram_used_mb, ram_available_mb, ram_total_mb, ram_pct,
> cpu_pct, disk_used_gb, disk_total_gb, disk_pct,
> proc_ram_mb, proc_cpu_pct, proc_threads,

---

## 🌍 Translator

### `POST` /api/v1/translate

Translate text using the configured provider.

**Тело запроса / параметры:**

| Поле | Описание |
|---|---|
| | request: JSON body with fields: |
| `text` (str) | Source text (required). |
| `source_lang` (str) | ISO 639-1 code or 'auto' (default: 'auto'). |
| `target_lang` (str) | ISO 639-1 target code (default: 'en'). |
| `provider` (str) | Override provider (default: from config). |
| `api_key` (str) | Optional API key override. |

**Ответ:**

> dict: success, translated, provider, source_lang, target_lang,
> elapsed_ms, error.

---

### `POST` /api/v1/translate/detect

Detect language of the given text.

**Тело запроса / параметры:**

| Поле | Описание |
|---|---|
| | request: JSON body with fields: |
| `text` (str) | Text to detect language for (required). |

**Ответ:**

> dict: success, language (ISO 639-1), language_name, error.

---

### `GET` /api/v1/translate/config

Return current translator configuration (no secrets).

**Ответ:**

> dict: enabled, default_provider, available_providers.

---

## 🆘 Support

### `GET` /api/v1/support/dialogs

Return all support dialogs grouped by chat_id.

**Ответ:**

> Dict: {success, dialogs: {chat_id: [{role, text, ts, username}]}}

---

### `GET` /api/v1/support/rag-profiles

Return available RAG profiles.

**Ответ:**

> Dict: {success, profiles: [...]}

---

### `POST` /api/v1/support/rag-profiles

Create a new RAG profile directory.

**Тело запроса / параметры:**

| Поле | Описание |
|---|---|
| `body` (Dict) | {name, description} |

**Ответ:**

> Dict: {success, path}

---

### `DELETE` /api/v1/support/rag-profiles/{name}

Soft-delete a RAG profile (rename with ~ suffix).

**Path параметры:**

| Параметр | Тип |
|---|---|
| `name` | `str` |

**Тело запроса / параметры:**

| Поле | Описание |
|---|---|
| `name` (str) | Profile name. |

**Ответ:**

> Dict: {success}

---

### `GET` /api/v1/support/config

Return current support bot configuration.

**Ответ:**

> Dict: {success, enabled, rag_profile}

---

## 🎧 HelpDesk

### `GET` /api/v1/helpdesk/dialogs

Return all helpdesk dialogs grouped by chat_id.

**Ответ:**

> Dict: {success, dialogs: {chat_id: [{role, text, ts, username}]}}

---

### `GET` /api/v1/helpdesk/rag-profiles

Return available RAG profiles.

**Ответ:**

> Dict: {success, profiles: [...]}

---

### `POST` /api/v1/helpdesk/rag-profiles

Create a new RAG profile directory.

**Тело запроса / параметры:**

| Поле | Описание |
|---|---|
| `body` (Dict) | {name, description} |

**Ответ:**

> Dict: {success, path}

---

### `DELETE` /api/v1/helpdesk/rag-profiles/{name}

Soft-delete a RAG profile (rename with ~ suffix).

**Path параметры:**

| Параметр | Тип |
|---|---|
| `name` | `str` |

**Тело запроса / параметры:**

| Поле | Описание |
|---|---|
| `name` (str) | Profile name. |

**Ответ:**

> Dict: {success}

---

### `GET` /api/v1/helpdesk/config

Return current helpdesk bot configuration.

**Ответ:**

> Dict: {success, enabled, rag_profile}

---

## 🎓 Training

### `POST` /api/v1/training/pairs

Add a new QA training pair.

**Тело запроса / параметры:**

| Поле | Описание |
|---|---|
| `request` (dict) | Fields: |
| | - question (str): User question. |
| | - answer_correct (str): Ideal answer. |
| | - answer_wrong (str, optional): Example of a bad answer. |
| | - source (str, optional): Origin tag. Default: "manual". |
| | - metadata (dict, optional): Extra fields. |

**Ответ:**

> dict: ``{success, pair}``

---

### `PATCH` /api/v1/training/pairs/{pair_id}/approve

Approve a QA pair — mark it ready for training.

**Path параметры:**

| Параметр | Тип |
|---|---|
| `pair_id` | `str` |

**Тело запроса / параметры:**

| Поле | Описание |
|---|---|
| `pair_id` (str) | UUID of the pair. |

**Ответ:**

> dict: ``{success}``

---

### `PATCH` /api/v1/training/pairs/{pair_id}/reject

Reject a QA pair — exclude it from training.

**Path параметры:**

| Параметр | Тип |
|---|---|
| `pair_id` | `str` |

**Тело запроса / параметры:**

| Поле | Описание |
|---|---|
| `pair_id` (str) | UUID of the pair. |

**Ответ:**

> dict: ``{success}``

---

### `DELETE` /api/v1/training/pairs/{pair_id}

Permanently delete a QA pair.

**Path параметры:**

| Параметр | Тип |
|---|---|
| `pair_id` | `str` |

**Тело запроса / параметры:**

| Поле | Описание |
|---|---|
| `pair_id` (str) | UUID of the pair. |

**Ответ:**

> dict: ``{success}``

---

### `GET` /api/v1/training/pairs

List QA pairs with optional filtering.

**Тело запроса / параметры:**

| Поле | Описание |
|---|---|
| `status` (str, optional) | pending / approved / rejected. |
| `source` (str, optional) | Filter by source tag. |
| `limit` (int) | Max results. Default 100. |
| `offset` (int) | Skip first N. Default 0. |

**Ответ:**

> dict: ``{success, pairs, total}``

---

### `GET` /api/v1/training/pairs/{pair_id}

Get a single QA pair by ID.

**Path параметры:**

| Параметр | Тип |
|---|---|
| `pair_id` | `str` |

**Тело запроса / параметры:**

| Поле | Описание |
|---|---|
| `pair_id` (str) | UUID of the pair. |

**Ответ:**

> dict: ``{success, pair}``

---

### `GET` /api/v1/training/stats

Return dataset statistics.

**Ответ:**

> dict: ``{success, stats}`` where stats has total/pending/approved/rejected.

---

### `GET` /api/v1/training/export

Export all approved QA pairs as JSON.

**Ответ:**

> dict: ``{success, pairs, total}``

---

### `POST` /api/v1/training/run

Launch a fine-tuning run over approved QA pairs.

**Тело запроса / параметры:**

| Поле | Описание |
|---|---|
| `request` (dict) | Fields: |
| | - strategy (str): "sft" / "dpo" / "lora". Default: "sft". |
| | - model_id (str, optional): Base model to fine-tune. |
| | - output_dir (str, optional): Output directory. Default: "training_output". |
| | - max_pairs (int, optional): Max approved pairs to use. Default: 10000. |

**Ответ:**

> dict: ``{success, result}``

---

## 💡 Recommender

### `POST` /api/v1/recommender/track

Record a page view event from the browser extension.

**Тело запроса / параметры:**

| Поле | Описание |
|---|---|
| | event: PageViewEvent with user_id, url, title, time_spent, timestamp. |

**Ответ:**

> dict: success status and total views count for the user.

---

### `POST` /api/v1/recommender/recommendations

Generate AI-powered recommendations based on browsing history.

**Тело запроса / параметры:**

| Поле | Описание |
|---|---|
| | request: RecommendRequest with user_id, optional model, top_k. |

**Ответ:**

> dict: success, answer (recommendations text), tool_calls log.

---

### `GET` /api/v1/recommender/history

Return filtered browsing history for a user.

**Тело запроса / параметры:**

| Поле | Описание |
|---|---|
| | user_id: User identifier. |
| | min_time: Minimum seconds on page to include (default 10). |

**Ответ:**

> dict: success, user_id, views list, count.

---

## 📦 Content Blocks

### `GET` /api/v1/content/blocks

List locally available content blocks.

---

### `GET` /api/v1/content/blocks/{slug}

Return a structured content block.

**Path параметры:**

| Параметр | Тип |
|---|---|
| `slug` | `str` |

---

### `GET` /api/v1/content/blocks/{slug}/html

Return a sanitized HTML rendering of a content block.

**Path параметры:**

| Параметр | Тип |
|---|---|
| `slug` | `str` |

---

## 🔐 Security

### `POST` /api/v1/security/api-key/generate

Generate a new cryptographically secure API key for this server.

**Ответ:**

> dict: ``{"success": True, "api_key": "<new key>"}``

---

### `GET` /api/v1/security/api-key/status

Return whether an API key is currently configured.

**Ответ:**

> dict: ``{"success": True, "configured": bool, "preview": "abcd...ef12"}``

---

### `DELETE` /api/v1/security/api-key

Remove the API key, disabling key-based protection.

**Ответ:**

> dict: ``{"success": True, "message": "API key removed"}``

---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-ApiReference.py`*
