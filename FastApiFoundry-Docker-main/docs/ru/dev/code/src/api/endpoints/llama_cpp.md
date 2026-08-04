# Llama Cpp

**Файл:** `src/api/endpoints/llama_cpp.py`  
**Тип:** `.py`

---

### `_get_server_url` — Функция

```python
def _get_server_url() -> str
```

Собрать URL llama.cpp сервера из config.json.

Returns:
    str: URL вида http://host:port

### `_get_server_url_for_model` — Функция

```python
def _get_server_url_for_model(model_id: str | None=None) -> str
```

Build llama.cpp server URL for a configured model alias/path.

### `llama_status` — Функция

```python
@router.get('/status')
```

Статус llama.cpp сервера.

### `llama_copy_model` — Функция

```python
@router.post('/models/copy')
```

Скопировать .gguf модель в ~/.models.

Если модель уже там есть — пропускает копирование.

Body: {"model_path": "D:/gemma-2-2b-it-Q6_K.gguf"}

### `llama_start` — Функция

```python
@router.post('/start')
```

Запустить llama.cpp сервер с указанной GGUF моделью.

Body:
    model_path:   Путь к .gguf файлу или директории с моделями.
                  Если не указан — берётся из config.json (llama_cpp.model_path → directories.models).
                  Если указана директория — берётся первый .gguf файл в ней.
    port:         Порт (default: 9780)
    ctx_size:     Размер контекста (default: 4096)
    threads:      Количество потоков CPU (default: auto)
    n_gpu_layers: Слоёв на GPU, 0 = только CPU (default: 0)
    host:         Хост (default: 127.0.0.1)

### `llama_stop` — Функция

```python
@router.post('/stop')
```

Остановить llama.cpp сервер.

### `llama_props` — Функция

```python
@router.get('/props')
```

Параметры запущенного llama-server: модель, контекст, потоки, n_gpu_layers.

Проксирует GET /props нативного llama-server API.

Returns:
    dict: success, props (model_path, n_ctx, n_threads, n_gpu_layers, ...)

### `llama_slots` — Функция

```python
@router.get('/slots')
```

Активные слоты инференса llama-server.

Проксирует GET /slots нативного llama-server API.
Показывает параллельные запросы в обработке.

Returns:
    dict: success, slots (list)

### `llama_metrics` — Функция

```python
@router.get('/metrics')
```

Prometheus-метрики llama-server: токены/сек, TTFT, очередь.

Проксирует GET /metrics нативного llama-server API.
Возвращает text/plain в формате Prometheus.

Returns:
    Response: text/plain Prometheus metrics или JSON с ошибкой.

### `llama_completion` — Функция

```python
@router.post('/completion')
```

Нативная генерация llama-server (быстрее, больше параметров).

Проксирует POST /completion нативного llama-server API.
Поддерживает top_k, repeat_penalty, mirostat и другие параметры
недоступные в OpenAI-совместимом /v1/chat/completions.

Args:
    request: JSON body — любые параметры llama-server /completion.
        prompt (str):          Входной текст (обязательно).
        temperature (float):   Температура (default: 0.7).
        top_k (int):           Top-K sampling (default: 40).
        top_p (float):         Top-P sampling (default: 0.95).
        repeat_penalty (float): Штраф за повторения (default: 1.1).
        n_predict (int):       Макс. токенов (default: 512).
        stop (list[str]):      Стоп-последовательности.
        stream (bool):         Стриминг (default: false).

Returns:
    dict: success, content, tokens_predicted, tokens_evaluated, ...

### `llama_tokenize` — Функция

```python
@router.post('/tokenize')
```

Токенизация текста через llama-server.

Проксирует POST /tokenize нативного llama-server API.

Args:
    request: {"content": "текст для токенизации"}

Returns:
    dict: success, tokens (list[int])

### `llama_detokenize` — Функция

```python
@router.post('/detokenize')
```

Детокенизация (токены → текст) через llama-server.

Проксирует POST /detokenize нативного llama-server API.

Args:
    request: {"tokens": [1, 2, 3, ...]}

Returns:
    dict: success, content (str)

### `llama_v1_completions` — Функция

```python
@router.post('/v1/completions')
```

OpenAI-совместимый text completion через llama-server.

Проксирует POST /v1/completions llama-server API.

Args:
    request: OpenAI completions body (prompt, max_tokens, temperature, ...).

Returns:
    dict: OpenAI-совместимый ответ.

### `llama_v1_embeddings` — Функция

```python
@router.post('/v1/embeddings')
```

Получить эмбеддинги через llama-server.

Проксирует POST /v1/embeddings llama-server API.
Требует запуска llama-server с флагом --embedding.

Args:
    request: {"input": "текст или список текстов", "model": "..."}

Returns:
    dict: success, data (list of embedding vectors), usage.

### `llama_v1_chat_completions` — Функция

```python
@router.post('/v1/chat/completions')
```

OpenAI-совместимый chat completion через llama-server.

Проксирует POST /v1/chat/completions llama-server API.
Используется router.py для генерации через llama:: префикс.

Args:
    request: OpenAI chat completions body (messages, model, temperature, ...).

Returns:
    dict: OpenAI-совместимый ответ.

### `llama_v1_models` — Функция

```python
@router.get('/v1/models')
```

Список моделей загруженных в llama-server (OpenAI-совместимый).

Проксирует GET /v1/models llama-server API.

Returns:
    dict: success, data (list of model objects), model_name (str, первая модель).

### `llama_scan_models` — Функция

```python
@router.get('/models')
```

Сканировать .gguf файлы в ~/.models, ~/.ai-assist/gguf_models, ~/.lmstudio/models и опциональном extra_dir.

Основные директории: ~/.models, ~/.ai-assist/gguf_models, ~/.lmstudio/models
Дополнительная: extra_dir из query-параметра (например D:\ если модель ещё не скопирована)

### `_find_llama_server` — Функция

```python
def _find_llama_server() -> str | None
```

Find llama-server executable.

Search order:
    1. LLAMA_SERVER_PATH env var (explicit path)
    2. PATH (shutil.which)
    3. bin/<bin_version>/ from config.json
    4. Any subdirectory of bin/ (fallback scan)
    5. Standard Windows install locations

Returns:
    str | None: Full path to binary or None.

### `_copy` — Функция

```python
def _copy()
```


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
