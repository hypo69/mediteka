# Generate Codereference

**Файл:** `scripts/Create-Doc/Generate-CodeReference.py`  
**Тип:** `.py`

---

### `should_skip_dir` — Функция

```python
def should_skip_dir(name: str) -> bool
```

### `dir_title` — Функция

```python
def dir_title(name: str) -> str
```

### `file_title` — Функция

```python
def file_title(stem: str) -> str
```

### `file_to_module` — Функция

```python
def file_to_module(py_file: Path) -> str
```

src/api/app.py → src.api.app

### `make_index_md` — Функция

```python
def make_index_md(directory: Path, out_md: Path) -> None
```

Generate index.md for a directory from its README.md or a stub.

### `make_file_md` — Функция

```python
def make_file_md(py_file: Path, out_md: Path) -> None
```

Generate <stem>.md with mkdocstrings directive.

### `nav_path` — Функция

```python
def nav_path(md_file: Path) -> str
```

Absolute path → relative to docs/ru/ for mkdocs nav.

### `process_dir` — Функция

```python
def process_dir(src_dir: Path, docs_dir: Path, indent: int) -> list[str]
```

Recursively process src_dir → docs_dir.
Returns nav lines (indented yaml list).

### `update_mkdocs_nav` — Функция

```python
def update_mkdocs_nav(nav_lines: list[str]) -> None
```

### `main` — Функция

```python
def main() -> None
```


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
