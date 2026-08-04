# Document Store

**Файл:** `src/rag/document_store.py`  
**Тип:** `.py`

---

### `DocumentStore` — Класс

```python
class DocumentStore
```

SQLite-backed store for RAG documents and chunk metadata.

Provides CRUD for documents and tracks which FAISS vector IDs
belong to which document so incremental updates are possible.

Args:
    db_path (str | Path): Path to the SQLite database file.

### `get_store` — Функция

```python
def get_store(index_dir: str='rag_index') -> DocumentStore
```

Return (or create) the module-level DocumentStore singleton.

Args:
    index_dir (str): Directory that contains the FAISS index.

Returns:
    DocumentStore: Singleton instance.

### `__init__` — Функция

```python
def __init__(self, db_path: str | Path | None=None) -> None
```

### `_conn` — Функция

```python
@contextmanager
```

Context manager that yields an open SQLite connection.

### `_init_schema` — Функция

```python
def _init_schema(self) -> None
```

Create tables if they do not exist yet.

### `_hash` — Функция

```python
@staticmethod
```

### `add_document` — Функция

```python
def add_document(self, title: str, content: str, source_path: str='') -> int
```

Insert a new document and return its id.

Args:
    title (str): Human-readable title.
    content (str): Full text content.
    source_path (str): Optional file path this content came from.

Returns:
    int: New document id.

### `get_document` — Функция

```python
def get_document(self, doc_id: int) -> Optional[Dict[str, Any]]
```

Fetch a single document by id.

Args:
    doc_id (int): Document primary key.

Returns:
    dict | None: Document row as dict, or None if not found.

### `list_documents` — Функция

```python
def list_documents(self) -> List[Dict[str, Any]]
```

Return all documents ordered by updated_at desc.

Returns:
    List[dict]: List of document rows.

### `update_document` — Функция

```python
def update_document(self, doc_id: int, title: str, content: str) -> bool
```

Update title and content of an existing document.

Args:
    doc_id (int): Document id.
    title (str): New title.
    content (str): New content.

Returns:
    bool: True if a row was updated.

### `delete_document` — Функция

```python
def delete_document(self, doc_id: int) -> bool
```

Delete a document and cascade-delete its chunks.

Args:
    doc_id (int): Document id.

Returns:
    bool: True if a row was deleted.

### `content_changed` — Функция

```python
def content_changed(self, doc_id: int, new_content: str) -> bool
```

Check whether content hash differs from stored value.

Args:
    doc_id (int): Document id.
    new_content (str): Candidate new content.

Returns:
    bool: True if content has changed.

### `save_chunks` — Функция

```python
def save_chunks(self, doc_id: int, chunks: List[Dict[str, Any]]) -> None
```

Deactivate old chunks and insert new ones for a document.

Args:
    doc_id (int): Document id.
    chunks (List[dict]): Each dict must have 'text', 'vector_id', 'chunk_no'.

### `get_active_chunks` — Функция

```python
def get_active_chunks(self, doc_id: int) -> List[Dict[str, Any]]
```

Return active chunks for a document.

Args:
    doc_id (int): Document id.

Returns:
    List[dict]: Active chunk rows.

### `get_all_active_chunks` — Функция

```python
def get_all_active_chunks(self) -> List[Dict[str, Any]]
```

Return all active chunks across all documents.

Returns:
    List[dict]: All active chunk rows with document title.

### `get_active_chunks_by_ids` — Функция

```python
def get_active_chunks_by_ids(self, chunk_ids: List[int]) -> Dict[int, Dict[str, Any]]
```

Return active chunks keyed by chunk id.

Args:
    chunk_ids (List[int]): SQLite chunk primary keys, usually returned by FAISS IndexIDMap.

Returns:
    Dict[int, dict]: Active chunk rows enriched with document metadata.

### `stats` — Функция

```python
def stats(self) -> Dict[str, int]
```

Return basic statistics.

Returns:
    dict: documents, active_chunks, inactive_chunks counts.


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
