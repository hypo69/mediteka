# Generate Fullreference

**Файл:** `scripts/Create-Doc/Generate-FullReference.py`  
**Тип:** `.py`

---

### `should_skip_dir` — Функция

```python
def should_skip_dir(path: Path, is_root_child: bool=False) -> bool
```

### `should_skip_file` — Функция

```python
def should_skip_file(path: Path) -> bool
```

### `file_title` — Функция

```python
def file_title(stem: str) -> str
```

### `dir_title` — Функция

```python
def dir_title(name: str) -> str
```

### `code_block` — Функция

```python
def code_block(lang: str, code: str) -> str
```

### `to_nav_path` — Функция

```python
def to_nav_path(md_file: Path) -> str
```

### `strip_relative_links` — Функция

```python
def strip_relative_links(content: str) -> str
```

Replace [text](../x) and [text](./x) with just text to avoid broken links.

### `extract_py` — Функция

```python
def extract_py(source: str) -> str
```

### `extract_ps1` — Функция

```python
def extract_ps1(source: str) -> str
```

### `extract_js` — Функция

```python
def extract_js(source: str) -> str
```

### `extract_json` — Функция

```python
def extract_json(source: str) -> str
```

### `extract_html` — Функция

```python
def extract_html(source: str) -> str
```

### `extract` — Функция

```python
def extract(filepath: Path) -> str
```

### `make_index_md` — Функция

```python
def make_index_md(directory: Path, out_md: Path) -> None
```

### `make_file_md` — Функция

```python
def make_file_md(filepath: Path, out_md: Path) -> None
```

### `process_dir` — Функция

```python
def process_dir(src_dir: Path, docs_dir: Path, indent: int, is_root_child: bool=False) -> list[str]
```

### `update_mkdocs` — Функция

```python
def update_mkdocs(nav_lines: list[str]) -> None
```

### `main` — Функция

```python
def main() -> None
```


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
