# Foundry Utils

**Файл:** `src/utils/foundry_utils.py`  
**Тип:** `.py`

---

### `_get_foundry_cache_dir` — Функция

```python
def _get_foundry_cache_dir() -> Path
```

### `test_foundry_port` — Функция

```python
def test_foundry_port(port: int) -> bool
```

Check whether Foundry is responding on the given port.

Args:
    port: TCP port to probe.

Returns:
    bool: True if Foundry API responds with HTTP 200.

### `find_foundry_port` — Функция

```python
def find_foundry_port() -> Optional[int]
```

Locate the port of a running Foundry service.
Order: 1. FOUNDRY_DYNAMIC_PORT env, 2. foundry service status output, 3. known ports, 4. default port 63995.

Returns:
    int | None: Port number if found, None otherwise.

### `find_foundry_url` — Функция

```python
def find_foundry_url() -> Optional[str]
```

Return the base URL of a running Foundry service.

### `model_id_to_cache_dir` — Функция

```python
def model_id_to_cache_dir(model_id: str) -> str
```

Convert a Foundry model ID to its filesystem directory name.

Foundry replaces ALL colons with dashes in the directory name.

Examples:
    qwen3-0.6b-generic-cpu:4    -> qwen3-0.6b-generic-cpu-4
    qwen3-0.6b-generic-cpu:4:4  -> qwen3-0.6b-generic-cpu-4-4
    deepseek-r1-distill-qwen-14b-generic-cpu:4 -> deepseek-r1-distill-qwen-14b-generic-cpu-4

### `_get_version_from_id` — Функция

```python
def _get_version_from_id(model_id: str) -> str
```

Extract the last version segment from a model ID (after the last colon).

### `is_foundry_model_cached` — Функция

```python
def is_foundry_model_cached(model_id: str) -> bool
```

Check whether a model exists in the local Foundry cache directory.

Foundry stores models under:
    <cache_dir>/Microsoft/<model_id_with_dashes>/v<version>/

The cache root is resolved fresh each call so config changes take effect
without restarting the server.


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
