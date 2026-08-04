# Text Utils

**Файл:** `src/utils/text_utils.py`  
**Тип:** `.py`

---

### `count_tokens_approx` — Функция

```python
def count_tokens_approx(text: str) -> int
```

Approximate token count: ~4 chars per token.

Args:
    text: Input string.

Returns:
    int: Estimated token count (minimum 1).

### `sanitize_for_filesystem` — Функция

```python
def sanitize_for_filesystem(name: str) -> str
```

Convert an arbitrary string to a safe directory or filename.
Removes non-alphanumeric characters except hyphens and underscores.

Args:
    name: Input string.
Returns:
    str: Sanitized string.


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
