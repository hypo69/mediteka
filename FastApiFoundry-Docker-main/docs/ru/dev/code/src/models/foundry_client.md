# Foundry Client

**Файл:** `src/models/foundry_client.py`  
**Тип:** `.py`

---

## Упрощённая логика Foundry

`FoundryClient` теперь является тонким адаптером над Microsoft Foundry Local. Он не пытается вести собственный менеджер состояния моделей и не полагается на устаревший порт из `config.json` как на источник истины.

Основные правила:

- живой Foundry URL определяется по фактическому ответу `GET /v1/models`;
- `config.foundry_base_url`, `FOUNDRY_BASE_URL` и `FOUNDRY_DYNAMIC_PORT` используются только как подсказки;
- `GET /v1/models` трактуется как список моделей, известных запущенному сервису, а не как гарантированный список моделей, загруженных в RAM;
- `load_model()` означает warm-up: короткий `POST /v1/chat/completions` с `max_tokens=1`;
- `unload_model()` выполняется best-effort: сначала `foundry-local-sdk`, затем CLI fallback `foundry model unload`;
- генерация всегда идёт через OpenAI-compatible endpoint `/v1/chat/completions`.

Это намеренно проще старой схемы: меньше скрытой магии, меньше рассинхронизации между портом в конфиге, состоянием Foundry и UI.

---

### `FoundryClient` — Класс

```python
class FoundryClient
```

Small OpenAI-compatible client for Foundry Local.

### `__init__` — Функция

```python
def __init__(self, base_url: str | None = None) -> None
```

Создаёт клиент. Если передан `base_url`, он будет проверен перед использованием. Если задан `FOUNDRY_DYNAMIC_PORT`, клиент сначала попробует `http://127.0.0.1:{port}/v1/`.

### `_update_base_url` — Функция

```python
async def _update_base_url(self) -> None
```

Находит живой OpenAI-compatible URL Foundry. Проверяет кандидаты и выбирает только тот URL, который реально отвечает на `GET /models`.

Порядок кандидатов:

1. текущий `self.base_url`;
2. `FOUNDRY_BASE_URL`;
3. `config.foundry_base_url`;
4. URL, найденный через `foundry service status` / port probing.

### `health_check` — Функция

```python
async def health_check(self) -> dict
```

Проверяет доступность Foundry.

Успешный ответ:

```json
{
  "status": "healthy",
  "url": "http://127.0.0.1:59420/v1/",
  "port": 59420,
  "models_count": 4
}
```

### `list_available_models` — Функция

```python
async def list_available_models(self) -> dict
```

Возвращает модели из `GET /v1/models`.

Важно: в текущем Foundry Local этот endpoint не является надёжным индикатором “модель загружена в RAM”. В API проекта такие модели помечаются как `available`, а не `loaded`.

### `load_model` — Функция

```python
async def load_model(self, model_id: str) -> dict
```

Готовит модель к работе через warm-up запрос:

```http
POST /v1/chat/completions
```

с коротким `ping` и `max_tokens=1`.

Успешный ответ означает, что модель отвечает на inference-запросы:

```json
{
  "success": true,
  "message": "Модель qwen3-0.6b-generic-cpu:4 готова"
}
```

### `unload_model` — Функция

```python
async def unload_model(self, model_id: str) -> dict
```

Best-effort выгрузка модели.

Порядок:

1. попытка через `foundry-local-sdk`;
2. fallback на `foundry model unload <model_id>`.

Foundry HTTP/OpenAI API не используется как основной механизм unload, потому что у него нет надёжного endpoint для этой операции.

### `generate_text` — Функция

```python
async def generate_text(self, prompt: str, model: str | None = None, temperature: float = 0.7, max_tokens: int = 2048, **kwargs: object) -> dict
```

Обычная генерация через `/v1/chat/completions`. Если `model` не указан, берётся первая модель из `list_available_models()`.

### `generate_stream` — Функция

```python
async def generate_stream(self, prompt: str, model: str | None = None, temperature: float = 0.7, max_tokens: int = 2048, **kwargs: object) -> AsyncIterator[dict]
```

Стриминговая генерация через `/v1/chat/completions` с `stream=true`.

### `completions` — Функция

```python
async def completions(self, prompt: str, model: str | None = None, temperature: float = 0.7, max_tokens: int = 512, **kwargs: object) -> dict
```

Прокси к `/v1/completions`.

### `embeddings` — Функция

```python
async def embeddings(self, input: str | list, model: str | None = None) -> dict
```

Прокси к `/v1/embeddings`.

---

*Проект: AI Assistant (ai_assist) · v0.8.0*
