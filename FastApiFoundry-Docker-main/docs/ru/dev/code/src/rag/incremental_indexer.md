# Incremental Indexer

**Файл:** `src/rag/incremental_indexer.py`  
**Тип:** `.py`

---

### `IncrementalIndexer` — Класс

```python
class IncrementalIndexer
```

Manages incremental FAISS updates backed by DocumentStore.

Args:
    index_dir (str | Path): Directory for faiss.index and documents.db.

### `get_indexer` — Функция

```python
def get_indexer(index_dir: str | None=None) -> IncrementalIndexer
```

Return (or create) the module-level IncrementalIndexer singleton.

Args:
    index_dir (str | None): Override index directory.

Returns:
    IncrementalIndexer: Singleton instance.

### `__init__` — Функция

```python
def __init__(self, index_dir: str | Path | None=None) -> None
```

### `_get_model` — Функция

```python
def _get_model(self) -> Any
```

Lazy-load the sentence-transformer model.

Returns:
    SentenceTransformer: Loaded embedding model.

### `_load_or_create_index` — Функция

```python
def _load_or_create_index(self) -> faiss.Index
```

Load existing IndexIDMap or create a new one.

Returns:
    faiss.Index: IndexIDMap wrapping IndexFlatIP.

### `_build_index_from_store` — Функция

```python
def _build_index_from_store(self) -> faiss.Index
```

Build a fresh IndexIDMap from active SQLite chunks.

### `_save_index` — Функция

```python
def _save_index(self, idx: faiss.Index) -> None
```

Persist FAISS index to disk.

Args:
    idx (faiss.Index): Index to save.

### `_maybe_compact` — Функция

```python
def _maybe_compact(self) -> None
```

Compact automatically when inactive chunks exceed the recommended threshold.

### `_chunk_text` — Функция

```python
def _chunk_text(self, text: str) -> List[str]
```

Split text into overlapping chunks using config values.

Args:
    text (str): Source text.

Returns:
    List[str]: List of text chunks.

### `_embed` — Функция

```python
def _embed(self, texts: List[str], progress_cb=None) -> np.ndarray
```

Compute L2-normalised embeddings for a list of texts.

Args:
    texts (List[str]): Texts to embed.
    progress_cb (callable | None): Optional callback(done, total) called per batch.

Returns:
    np.ndarray: Float32 array of shape (len(texts), dim).

### `add_document` — Функция

```python
def add_document(self, title: str, content: str, source_path: str='') -> Dict[str, Any]
```

Add a new document: chunk → embed → insert into FAISS + DB.

Args:
    title (str): Document title.
    content (str): Full text.
    source_path (str): Optional origin path.

Returns:
    dict: success, doc_id, chunks_added.

### `update_document` — Функция

```python
def update_document(self, doc_id: int, title: str, content: str) -> Dict[str, Any]
```

Update document: deactivate old chunks, re-embed new content.

Args:
    doc_id (int): Existing document id.
    title (str): New title.
    content (str): New content.

Returns:
    dict: success, chunks_added, changed.

### `delete_document` — Функция

```python
def delete_document(self, doc_id: int) -> Dict[str, Any]
```

Mark document chunks as inactive and remove document record.

Args:
    doc_id (int): Document id.

Returns:
    dict: success.

### `compact` — Функция

```python
def compact(self) -> Dict[str, Any]
```

Rebuild FAISS index from active chunks only.

Should be called when inactive_chunks / total_chunks > 0.2.

Returns:
    dict: success, vectors_before, vectors_after.

### `get_stats` — Функция

```python
def get_stats(self) -> Dict[str, Any]
```

Return index and store statistics.

Returns:
    dict: documents, active_chunks, inactive_chunks, faiss_vectors, compact_recommended.

### `_index_document` — Функция

```python
def _index_document(self, doc_id: int, content: str, progress_cb=None) -> int
```

Chunk, embed and add vectors for one document.

Args:
    doc_id (int): Document id in the store.
    content (str): Text to index.
    progress_cb (callable | None): Optional callback(done, total) for embed progress.

Returns:
    int: Number of chunks added.


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
