# Content Blocks

**Файл:** `src/api/endpoints/content_blocks.py`  
**Тип:** `.py`

---

Local content blocks API.

These endpoints expose structured content that can be rendered by external
surfaces such as WordPress blocks without coupling WordPress to MkDocs.

### `_block_path` — Функция

```python
def _block_path(slug: str) -> Path
```

### `_load_block` — Функция

```python
def _load_block(slug: str) -> dict[str, Any]
```

### `_render_block_html` — Функция

```python
def _render_block_html(block: dict[str, Any]) -> str
```

### `list_content_blocks` — Функция

```python
@router.get('/blocks')
```

List locally available content blocks.

### `get_content_block` — Функция

```python
@router.get('/blocks/{slug}')
```

Return a structured content block.

### `get_content_block_html` — Функция

```python
@router.get('/blocks/{slug}/html', response_class=HTMLResponse)
```

Return a sanitized HTML rendering of a content block.


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
