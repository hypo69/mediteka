# Generate Nav

**Файл:** `scripts/Create-Doc/Generate-Nav.py`  
**Тип:** `.py`

---

### `nav_path` — Функция

```python
def nav_path(md_file: Path) -> str
```

Absolute path → relative to docs/ru/ for mkdocs nav.

### `file_title` — Функция

```python
def file_title(stem: str) -> str
```

### `dir_title` — Функция

```python
def dir_title(name: str) -> str
```

### `scan_code_dir` — Функция

```python
def scan_code_dir(src_dir: Path, indent: int) -> list[str]
```

Recursively scan docs/ru/dev/code/ and build nav lines.

### `build_nav` — Функция

```python
def build_nav() -> str
```

Build the complete nav YAML string.

### `main` — Функция

```python
def main() -> None
```


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
