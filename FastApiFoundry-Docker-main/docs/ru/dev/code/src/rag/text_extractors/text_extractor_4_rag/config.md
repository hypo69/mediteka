# Config

**Файл:** `src/rag/text_extractors/text_extractor_4_rag/config.py`  
**Тип:** `.py`

---

### `_cfg` — Функция

```python
def _cfg(key: str, default: Any=None) -> Any
```

Return a value from config.json → text_extractor section.

### `_env_int` — Функция

```python
def _env_int(key: str, fallback: int) -> int
```

### `_env_bool` — Функция

```python
def _env_bool(key: str, fallback: bool) -> bool
```

### `_env_str` — Функция

```python
def _env_str(key: str, fallback: str) -> str
```

### `Settings` — Класс

```python
class Settings
```

Text extractor settings resolved from the project Config singleton.

Resolution order (highest wins):
  1. Environment variable
  2. config.json → ``text_extractor`` section  (via Config singleton)
  3. Built-in default

### `_get_settings` — Функция

```python
def _get_settings() -> 'Settings'
```

Return the module-level Settings instance, creating it on first call.

### `_SettingsProxy` — Класс

```python
class _SettingsProxy
```

Proxy that forwards attribute access to the Settings singleton.

Allows callers to write ``settings.MAX_FILE_SIZE`` while still
supporting ``settings.reload()`` after ``config.reload_config()``.

### `__init__` — Функция

```python
def __init__(self) -> None
```

### `all_supported_extensions` — Функция

```python
@property
```

All supported file extensions as a flat list.

### `__getattr__` — Функция

```python
def __getattr__(self, name: str) -> Any
```

### `reload` — Функция

```python
def reload(self) -> None
```

Re-create the Settings instance from the current config.json values.


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
