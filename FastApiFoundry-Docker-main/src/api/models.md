# Model Management API

## Подготовка модели

Единый API маршрутизирует операции по префиксу модели:

| Префикс | Бэкенд | Поведение `load` |
|---|---|---|
| `foundry::` | Microsoft Foundry Local | Warm-up через короткий `/chat/completions` |
| `hf::` | HuggingFace Transformers | Загрузка pipeline/model в RAM/VRAM |
| `llama::` | llama.cpp | Запуск/переключение llama.cpp server |
| `ollama::` | Ollama | Pull/подготовка модели, памятью управляет Ollama |

Для Foundry слово `load` больше не означает “вызвать HTTP endpoint загрузки в RAM”. У Foundry Local нет надёжного OpenAI-compatible endpoint для этого. Поэтому FastAPI Foundry делает то, что действительно проверяет готовность модели: отправляет маленький inference-запрос.

**Endpoint:** `POST /api/v1/models/{model_id:path}/load`

**Пример Foundry:**

```bash
curl -X POST "http://localhost:9696/api/v1/models/foundry::qwen3-0.6b-generic-cpu:4/load"
```

Успешный ответ означает, что модель отвечает на запросы:

```json
{
  "success": true,
  "provider": "foundry",
  "model_id": "foundry::qwen3-0.6b-generic-cpu:4",
  "status": "ready"
}
```

## Выгрузка модели

Для Foundry выгрузка выполняется best-effort: сначала через `foundry-local-sdk`, затем через CLI `foundry model unload`. Для других провайдеров поведение зависит от бэкенда.

**Endpoint:** `POST /api/v1/models/{model_id:path}/unload`

**Пример Foundry:**

```bash
curl -X POST "http://localhost:9696/api/v1/models/foundry::qwen3-0.6b-generic-cpu:4/unload"
```

## Список моделей

Для Foundry `GET /v1/models` от Microsoft Foundry Local трактуется как список моделей, известных запущенному сервису. Это не гарантированный список моделей, загруженных в RAM. Поэтому FastAPI Foundry использует статус `available`, а не `loaded`.
