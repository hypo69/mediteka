# Rag Service

**Файл:** `src/rag/rag_service.py`  
**Тип:** `.py`

---

RAG query service: retrieve -> filter/rerank -> prompt -> generate.

### `RAGQueryFilters` — Класс

```python
@dataclass
```

Optional retrieval filters.

### `RAGQueryRequest` — Класс

```python
@dataclass
```

Internal request object for the query service.

### `RAGService` — Класс

```python
class RAGService
```

High-level RAG read path.

### `sse` — Функция

```python
def sse(data: Dict[str, Any]) -> str
```

Serialize a dict as a Server-Sent Event frame.

### `__init__` — Функция

```python
def __init__(self) -> None
```

### `retrieve` — Функция

```python
async def retrieve(self, query: str, top_k: int=5, filters: Optional[RAGQueryFilters]=None, rerank: bool=True) -> List[Dict[str, Any]]
```

Retrieve chunks, apply filters and optional lightweight reranking.

### `build_prompt` — Функция

```python
def build_prompt(self, query: str, chunks: List[Dict[str, Any]], system_prompt: str='') -> str
```

Build a grounded prompt with citations.

### `query` — Функция

```python
async def query(self, request: RAGQueryRequest) -> Dict[str, Any]
```

Run a complete non-streaming RAG query.

### `stream_query` — Функция

```python
async def stream_query(self, request: RAGQueryRequest) -> AsyncGenerator[Dict[str, Any], None]
```

Stream retrieval metadata followed by generated answer deltas.

### `_apply_filters` — Функция

```python
def _apply_filters(self, results: List[Dict[str, Any]], filters: RAGQueryFilters) -> List[Dict[str, Any]]
```

### `_rerank` — Функция

```python
def _rerank(self, query: str, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]
```

Lightweight lexical rerank layered on top of vector score.

### `_generate` — Функция

```python
async def _generate(self, prompt: str, request: RAGQueryRequest) -> Dict[str, Any]
```

### `_generate_stream` — Функция

```python
async def _generate_stream(self, prompt: str, request: RAGQueryRequest) -> AsyncGenerator[Dict[str, Any], None]
```

### `_generate_opencode` — Функция

```python
async def _generate_opencode(self, prompt: str) -> Dict[str, Any]
```

Call opencode CLI when explicitly requested.

### `_stream_event` — Функция

```python
@staticmethod
```

### `_source_matches` — Функция

```python
@staticmethod
```

### `_terms` — Функция

```python
@staticmethod
```

### `_citations` — Функция

```python
@staticmethod
```

### `_wants_opencode` — Функция

```python
@staticmethod
```


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
