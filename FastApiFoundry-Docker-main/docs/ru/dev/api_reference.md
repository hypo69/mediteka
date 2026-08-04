# API Reference

Базовый URL: `http://localhost:9696/api/v1`

Swagger UI: `http://localhost:9696/docs`

---

## Модели — универсальные endpoints {#models}

Единая точка доступа ко всем провайдерам. Модель идентифицируется **префиксом**:

| Префикс | Провайдер |
|---|---|
| `foundry::model-id` | Microsoft Foundry Local |
| `hf::model-id` | HuggingFace Transformers |
| `llama::path/to/model.gguf` | llama.cpp |
| `ollama::model-name` | Ollama |
| `lmstudio::model-key` | LM Studio |

### GET /models

Список всех локальных моделей от всех провайдеров с префиксами.

**Ответ:**
```json
{
  "success": true,
  "count": 8,
  "by_provider": { "foundry": 2, "huggingface": 1, "llama.cpp": 3, "ollama": 2 },
  "models": [
    {
      "id": "foundry::qwen3-0.6b-generic-cpu:4",
      "name": "qwen3-0.6b-generic-cpu:4",
      "provider": "foundry",
      "prefix": "foundry::qwen3-0.6b-generic-cpu:4",
      "loaded": false,
      "cached": true,
      "size": "",
      "device": "CPU"
    }
  ]
}
```

### POST /models/{model_id}/load

Загрузить модель в память. `model_id` в URL **обязан** содержать префикс провайдера.

```
POST /api/v1/models/foundry::qwen3-0.6b-generic-cpu:4/load
POST /api/v1/models/hf::Qwen%2FQwen2.5-0.5B-Instruct/load
POST /api/v1/models/llama::D:%2Fmodels%2Fgemma-4-E4B-it-Q4_K_M.gguf/load
POST /api/v1/models/ollama::qwen2.5:0.5b/load
```

**Ответ:**
```json
{ "success": true, "model_id": "hf::Qwen/Qwen2.5-0.5B-Instruct", "provider": "huggingface", "status": "loaded" }
```

**Ошибка (нет префикса):**
```json
{ "success": false, "error": "model_id must include provider prefix (foundry::, hf::, llama::, ollama::), got: qwen3" }
```

### POST /models/{model_id}/unload

Выгрузить модель из памяти.

```
POST /api/v1/models/hf::Qwen%2FQwen2.5-0.5B-Instruct/unload
POST /api/v1/models/foundry::qwen3-0.6b-generic-cpu:4/unload
```

---

## Health

### GET /health

Статус всех сервисов. Все провайдеры возвращают единый формат `{status, active_model}`.

**Ответ:**
```json
{
  "status": "healthy",
  "foundry_status":  { "status": "running", "active_model": "qwen3-0.6b-generic-cpu:4", "models_loaded": 1 },
  "llama_status":    { "status": "running", "active_model": "gemma-4-E4B-it-Q4_K_M.gguf", "url": "http://127.0.0.1:9780", "pid": 1234 },
  "hf_status":       { "status": "ready",   "active_model": "Qwen/Qwen2.5-0.5B-Instruct", "transformers": true, "torch": true, "token_set": true, "models_downloaded": 3, "models_loaded": 1, "models_dir": "D:/models" },
  "ollama_status":   { "status": "running", "active_model": "qwen2.5:0.5b", "models_count": 3 },
  "docs_status":     "stopped",
  "rag_status":      "enabled",
  "timestamp":       "2025-01-15T10:30:00+00:00"
}
```

Значения `status` для провайдеров: `running` | `stopped` | `loading` | `ready` | `libraries_missing` | `not_checked` | `error`

---

## Генерация текста {#generate}

### POST /generate

Генерация текста с маршрутизацией по префиксу модели.

**Тело запроса:**
```json
{
  "prompt": "Объясни квантовые вычисления",
  "model": "foundry::qwen3-0.6b-generic-cpu:4",
  "temperature": 0.7,
  "max_tokens": 512
}
```

### POST /ai/generate {#ai}

Расширенная генерация с опциональным RAG-контекстом.

**Тело запроса:**
```json
{
  "prompt": "Как настроить RAG?",
  "model": "hf::Qwen/Qwen2.5-0.5B-Instruct",
  "use_rag": true,
  "min_score": 0.5
}
```

### POST /ai/generate/stream

Стриминговая генерация (SSE). Только Foundry.

### POST /ai/chat

Чат с историей сообщений.

**Тело запроса:**
```json
{
  "messages": [
    { "role": "user", "content": "Привет!" }
  ],
  "model": "ollama::qwen2.5:0.5b",
  "use_rag": false
}
```

### POST /ai/chat/stream

Стриминговый чат с сохранением истории (SSE).

---

## Foundry Local {#foundry}

### Foundry Models {#foundry-models}

| Метод | Endpoint | Описание |
|---|---|---|
| GET | `/foundry/status` | Статус сервиса Foundry |
| GET | `/foundry/models` | Загруженные модели (alias → `/foundry/models/available`) |
| GET | `/foundry/models/catalog` | Полный каталог (CLI `foundry model list`) |
| GET | `/foundry/models/cached` | Модели на диске (filesystem scan) |
| GET | `/foundry/models/loaded` | Модели в памяти |
| POST | `/foundry/models/load` | Загрузить модель: `{"model_id": "qwen3-0.6b-generic-cpu:4"}` |
| POST | `/foundry/models/unload` | Выгрузить модель: `{"model_id": "qwen3-0.6b-generic-cpu:4"}` |
| POST | `/foundry/models/download` | Скачать модель: `{"model_id": "..."}` |
| GET | `/foundry/models/download/status/{pid}` | Статус скачивания |

!!! warning "Foundry-specific endpoints принимают bare model_id без префикса"
    `POST /foundry/models/load` принимает `{"model_id": "qwen3-0.6b-generic-cpu:4"}` — без `foundry::`.
    Универсальный `POST /models/load` принимает `{"model_id": "foundry::qwen3-0.6b-generic-cpu:4"}` — с префиксом.

---

## HuggingFace

| Метод | Endpoint | Описание |
|---|---|---|
| GET | `/hf/models` | Скачанные и загруженные модели |
| GET | `/hf/hub/models` | Модели пользователя с HF Hub |
| GET | `/hf/status` | Статус библиотек (transformers, torch, token) |
| POST | `/hf/models/download` | Скачать: `{"model_id": "Qwen/Qwen2.5-0.5B-Instruct"}` |
| GET | `/hf/models/download/stream` | Скачать с SSE прогрессом: `?model_id=...` |
| POST | `/hf/models/load` | Загрузить в память: `{"model_id": "...", "device": "auto"}` |
| POST | `/hf/models/unload` | Выгрузить: `{"model_id": "..."}` |
| POST | `/hf/generate` | Генерация: `{"model_id": "...", "prompt": "..."}` |

---

## llama.cpp

| Метод | Endpoint | Описание |
|---|---|---|
| GET | `/llama/status` | Статус сервера + `active_model` |
| POST | `/llama/start` | Запустить: `{"model_path": "D:/models/gemma.gguf"}` |
| POST | `/llama/stop` | Остановить сервер |
| GET | `/llama/models` | GGUF файлы на диске |
| POST | `/llama/completion` | Нативная генерация (top_k, mirostat, ...) |
| POST | `/llama/v1/chat/completions` | OpenAI-совместимый chat |
| POST | `/llama/v1/completions` | OpenAI-совместимый text completion |
| POST | `/llama/v1/embeddings` | Эмбеддинги |
| GET | `/llama/v1/models` | Загруженные модели (OpenAI формат) |
| GET | `/llama/props` | Параметры сервера |
| GET | `/llama/metrics` | Prometheus-метрики |

---

## Ollama

| Метод | Endpoint | Описание |
|---|---|---|
| GET | `/ollama/status` | Статус сервиса |
| GET | `/ollama/models` | Локальные модели |
| POST | `/ollama/models/pull` | Скачать: `{"model": "qwen2.5:0.5b"}` |
| POST | `/ollama/models/delete` | Удалить: `{"model": "qwen2.5:0.5b"}` |
| POST | `/ollama/generate` | Генерация: `{"model": "...", "prompt": "..."}` |

---

## RAG

| Метод | Endpoint | Описание |
|---|---|---|
| POST | `/rag/search` | Поиск: `{"query": "...", "top_k": 5}` |
| POST | `/rag/build` | Построить индекс: `{"docs_dir": "...", "profile": "default"}` |
| POST | `/rag/extract/file` | Извлечь текст из файла (multipart) |
| POST | `/rag/extract/url` | Извлечь текст с URL: `{"url": "..."}` |
| GET | `/rag/extract/formats` | Поддерживаемые форматы |

### Пример индексации через API

=== "Python"
    ```python
    import requests
    requests.post("http://localhost:9696/api/v1/rag/build", json={
        "docs_dir": "C:/MyDocs",
        "chunk_size": 1000,
        "profile": "default",
        "force_rebuild": True,
    })
    ```
=== "PowerShell"
    ```powershell
    Invoke-RestMethod -Uri "http://localhost:9696/api/v1/rag/build" -Method Post `
        -ContentType "application/json" `
        -Body '{"docs_dir":"C:/MyDocs","profile":"default"}'
    ```
=== "curl"
    ```bash
    curl -X POST http://localhost:9696/api/v1/rag/build \
      -H "Content-Type: application/json" \
      -d '{"docs_dir":"C:/MyDocs","profile":"default"}'
    ```

---

## Chat (сессии) {#chat}

| Метод | Endpoint | Описание |
|---|---|---|
| POST | `/chat/start` | Начать сессию |
| POST | `/chat/message` | Отправить сообщение |
| POST | `/chat/stream` | SSE стриминг |
| GET | `/chat/history/list` | Список сохранённых диалогов |
| GET | `/chat/history/file/{filename}` | Загрузить диалог |
| POST | `/chat/history/cleanup` | Очистить устаревшие диалоги |

---

## Прочие endpoints

### Agent {#agent}

| Метод | Endpoint | Описание |
|---|---|---|
| POST | `/agent/run` | Запустить AI агента |

### MCP PowerShell {#mcp-powershell}

| Метод | Endpoint | Описание |
|---|---|---|
| GET | `/mcp-powershell/servers` | Список MCP серверов |

### Config {#config}

| Метод | Endpoint | Описание |
|---|---|---|
| GET | `/config` | Текущая конфигурация |
| PATCH | `/config` | Обновить конфигурацию |

### Logs {#logs}

| Метод | Endpoint | Описание |
|---|---|---|
| GET | `/logs` | Логи приложения |

### Converter {#converter}

| Метод | Endpoint | Описание |
|---|---|---|
| POST | `/converter/gguf-to-onnx` | Конвертация GGUF → ONNX |

### System {#system}

| Метод | Endpoint | Описание |
|---|---|---|
| GET | `/system/stats` | RAM / CPU статистика |

### HelpDesk {#helpdesk}

| Метод | Endpoint | Описание |
|---|---|---|
| GET | `/helpdesk/dialogs` | HelpDesk диалоги |

### Other

| Метод | Endpoint | Описание |
|---|---|---|
| POST | `/translate` | Перевод текста |
| POST | `/restart/{service}` | Перезапустить сервис: `foundry\|llama\|docs\|rag` |
