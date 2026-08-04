# Generate Apireference

**Файл:** `scripts/Create-Doc/Generate-ApiReference.py`  
**Тип:** `.py`

---

### `extract_router_prefix` — Функция

```python
def extract_router_prefix(source: str) -> str
```

Extract prefix from APIRouter(prefix=...) declaration.

### `extract_routes` — Функция

```python
def extract_routes(filepath: Path, base_prefix: str) -> list[dict]
```

Parse a Python endpoint file and extract all route definitions.

### `format_docstring` — Функция

```python
def format_docstring(doc: str) -> str
```

Format docstring into clean markdown.

### `method_badge` — Функция

```python
def method_badge(method: str) -> str
```

### `generate_page` — Функция

```python
def generate_page(all_sections: list[tuple[str, list[dict]]]) -> str
```

### `main` — Функция

```python
def main() -> None
```


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
