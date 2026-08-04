# Env Processor

**Файл:** `src/utils/env_processor.py`  
**Тип:** `.py`

---

### `load_env_variables` — Функция

```python
def load_env_variables() -> bool
```

Load environment variables from .env file.

Returns:
    bool: True if .env was found and loaded.

### `substitute_env_vars` — Функция

```python
def substitute_env_vars(value: str) -> Union[str, int, float, bool, list]
```

Substitute environment variables in a string.

Supported formats:
    ${VAR_NAME}          — required variable
    ${VAR_NAME:default}  — with default value

Args:
    value: String potentially containing ${...} placeholders.

Returns:
    Substituted and type-converted value (str, int, float, bool, or list).

Raises:
    ValueError: If a required variable is not set.

### `convert_type` — Функция

```python
def convert_type(value: str) -> Union[str, int, float, bool, list]
```

Convert a string to the most appropriate Python type.

Args:
    value: String to convert.

Returns:
    Converted value: bool for 'true'/'false', int/float for numbers,
    list for comma-separated, str otherwise.

### `process_dict` — Функция

```python
def process_dict(data: Dict[str, Any]) -> Dict[str, Any]
```

Recursively substitute env vars in a config dict.

Args:
    data: Configuration dict to process.

Returns:
    dict: Processed configuration with all ${...} placeholders substituted.

### `process_config` — Функция

```python
def process_config(config_path: Union[str, Path]) -> Dict[str, Any]
```

Load and process a config file, substituting env vars.

Args:
    config_path: Path to config.json.

Returns:
    Processed configuration dict.

Raises:
    FileNotFoundError: Config file not found.
    json.JSONDecodeError: Invalid JSON in config file.
    ValueError: Required env variable not set.

### `validate_config` — Функция

```python
def validate_config(cfg: Dict[str, Any]) -> bool
```

Validate processed configuration.

Args:
    cfg: Configuration dict to check.

Returns:
    bool: True if all required sections (fastapi_server, foundry_ai, security) are present.

### `save_processed_config` — Функция

```python
def save_processed_config(cfg: Dict[str, Any], output_path: Union[str, Path]) -> None
```

Save processed configuration to a file.

Args:
    cfg: Configuration dict.
    output_path: Destination file path.

### `_replace` — Функция

```python
def _replace(match: re.Match) -> str
```


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
