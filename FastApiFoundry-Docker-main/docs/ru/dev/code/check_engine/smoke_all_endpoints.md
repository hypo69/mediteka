# Smoke All Endpoints

**Файл:** `check_engine/smoke_all_endpoints.py`  
**Тип:** `.py`

---

### `_stdout_utf8` — Функция

```python
def _stdout_utf8() -> None
```

### `_load_default_model` — Функция

```python
def _load_default_model(config_path: str) -> str
```

### `_http_request_json` — Функция

```python
def _http_request_json(url: str, payload: Dict[str, Any], timeout_s: int) -> Tuple[int, Dict[str, Any], str]
```

### `_http_get_json` — Функция

```python
def _http_get_json(url: str, timeout_s: int) -> Tuple[int, Dict[str, Any], str]
```

### `_http_post_raw` — Функция

```python
def _http_post_raw(url: str, payload: Dict[str, Any], timeout_s: int) -> Tuple[int, str, bytes]
```

### `_fail` — Функция

```python
def _fail(name: str, details: str) -> None
```

### `_pick_model_by_probe` — Функция

```python
def _pick_model_by_probe(base_url: str, candidates: list, timeout_s: int) -> str
```

### `main` — Функция

```python
def main() -> int
```

Основная функция.


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
