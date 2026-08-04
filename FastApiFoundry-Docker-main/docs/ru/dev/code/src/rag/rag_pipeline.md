# Rag Pipeline

**Файл:** `src/rag/rag_pipeline.py`  
**Тип:** `.py`

---

High-level RAG indexing pipeline.

This module keeps the write path in one place:
ingest/extract -> chunk/embed/store -> FAISS IndexIDMap.

### `RAGPipeline` — Класс

```python
class RAGPipeline
```

Coordinates ingestion and incremental indexing.

### `get_pipeline` — Функция

```python
def get_pipeline(index_dir: Optional[str]=None) -> RAGPipeline
```

Return a pipeline for the requested index directory.

### `__init__` — Функция

```python
def __init__(self, index_dir: str | Path | None=None) -> None
```

### `_indexer` — Функция

```python
def _indexer(self) -> IncrementalIndexer
```

### `add_text` — Функция

```python
async def add_text(self, title: str, content: str, source_path: str='') -> Dict[str, Any]
```

Index already extracted text.

### `ingest_upload` — Функция

```python
async def ingest_upload(self, file: UploadFile) -> Dict[str, Any]
```

Extract and index a FastAPI upload.

### `ingest_upload_stream` — Функция

```python
async def ingest_upload_stream(self, file: UploadFile) -> AsyncIterator[Dict[str, Any]]
```

Extract and index a FastAPI upload, yielding SSE-style progress events.

Stages emitted via 'stage' field:
  extract   — text extraction from file/archive
  chunk     — text split into chunks
  embed     — embedding progress (done/total chunks)
  index     — FAISS write + DB save
  done      — final summary
  error     — on failure

Args:
    file (UploadFile): Uploaded file.

Returns:
    AsyncIterator[dict]: Progress event dicts.

### `ingest_url` — Функция

```python
async def ingest_url(self, url: str) -> Dict[str, Any]
```

Extract and index a URL.

### `migrate_to_index_id_map` — Функция

```python
def migrate_to_index_id_map(self) -> Dict[str, Any]
```

Migrate the active index directory to SQLite + FAISS IndexIDMap.

If documents.db already exists, compaction rebuilds FAISS from active SQLite
chunks. If only legacy chunks.json exists, this imports those chunks into
SQLite first and then rebuilds FAISS with chunk IDs as vector IDs.

### `_put` — Функция

```python
async def _put(event: dict) -> None
```

### `_run` — Функция

```python
async def _run() -> None
```

### `_progress_cb` — Функция

```python
def _progress_cb(done: int, total: int) -> None
```

### `_index_with_progress` — Функция

```python
def _index_with_progress() -> Dict[str, Any]
```


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
