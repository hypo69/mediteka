# Llama Registry

**Файл:** `src/models/llama_registry.py`  
**Тип:** `.py`

---

llama.cpp model registry built from config.json.

This module keeps the mapping between a configured GGUF model and the
dedicated llama-server port that serves it.

### `LlamaServerConfig` — Класс

```python
@dataclass(frozen=True)
```

### `get_configured_llama_servers` — Функция

```python
def get_configured_llama_servers() -> list[LlamaServerConfig]
```

Return llama.cpp server entries configured in config.json.

Supported config shape:

```json
"llama_cpp": {
  "host": "127.0.0.1",
  "port": 9780,
  "models": [
    {"alias": "coder", "model_path": "D:/models/coder.gguf", "port": 9781},
    "D:/models/general.gguf"
  ]
}
```

If `models` is empty, the legacy single `model_path`/`port` pair is used.

### `resolve_llama_server` — Функция

```python
def resolve_llama_server(model_id: str | None=None) -> LlamaServerConfig | None
```

Find the configured llama.cpp server for a requested model ID.

### `_parse_entry` — Функция

```python
def _parse_entry(entry: Any, index: int, base_host: str, base_port: int) -> LlamaServerConfig | None
```

### `_optional_int` — Функция

```python
def _optional_int(value: Any) -> int | None
```

### `_normalize` — Функция

```python
def _normalize(value: str | None) -> str
```

### `model_name` — Функция

```python
@property
```

### `openai_url` — Функция

```python
@property
```

### `url` — Функция

```python
@property
```

### `matches` — Функция

```python
def matches(self, model_id: str) -> bool
```


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
