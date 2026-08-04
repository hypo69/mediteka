# Init Databases

**Файл:** `scripts/Install/Init-Databases.py`  
**Тип:** `.py`

---

### `init_chat_db` — Функция

```python
def init_chat_db(db_path: Path) -> None
```

Create chat history database with sessions and messages tables.

Args:
    db_path (Path): Absolute path to the SQLite file.

### `init_rag_db` — Функция

```python
def init_rag_db(db_path: Path) -> None
```

Create RAG document store database with documents and chunks tables.

Args:
    db_path (Path): Absolute path to the SQLite file.

### `main` — Функция

```python
def main() -> None
```

Read paths from config and initialise both databases.


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
