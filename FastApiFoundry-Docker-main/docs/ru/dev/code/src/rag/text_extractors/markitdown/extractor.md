# Extractor

**Файл:** `src/rag/text_extractors/markitdown/extractor.py`  
**Тип:** `.py`

---

### `MarkItDownExtractor` — Класс

```python
class MarkItDownExtractor
```

Text extractor using Microsoft MarkItDown library.

Converts files and URLs to Markdown text suitable for LLM/RAG pipelines.
Preserves document structure: headings, lists, tables, links.

Args:
    enable_plugins (bool): Enable third-party MarkItDown plugins. Default: False.
    llm_client (Any): Optional OpenAI-compatible client for image descriptions. Default: None.
    llm_model (str): Model name for LLM-based image descriptions. Default: None.
    docintel_endpoint (str): Azure Document Intelligence endpoint URL. Default: None.

Example:
    >>> extractor = MarkItDownExtractor()
    >>> result = extractor.extract_from_file("document.pdf")
    >>> print(result["text"])

### `__init__` — Функция

```python
def __init__(self, enable_plugins: bool=False, llm_client: Any=None, llm_model: str | None=None, docintel_endpoint: str | None=None) -> None
```

### `_get_client` — Функция

```python
def _get_client(self) -> Any
```

Lazy-initialize MarkItDown client.

Returns:
    MarkItDown: Initialized MarkItDown instance.

Exceptions:
    ImportError: If markitdown package is not installed.

### `extract_from_file` — Функция

```python
def extract_from_file(self, file_path: str | Path) -> dict[str, str]
```

Extract text from a local file.

Args:
    file_path (str | Path): Path to the file to convert.

Returns:
    dict[str, str]: Dict with keys 'text' (Markdown content) and 'filename'.

Exceptions:
    FileNotFoundError: If file_path does not exist.
    Exception: On conversion failure.

Example:
    >>> extractor = MarkItDownExtractor()
    >>> result = extractor.extract_from_file("report.docx")
    >>> result["text"]
    '# Report Title'

### `extract_from_bytes` — Функция

```python
def extract_from_bytes(self, content: bytes, filename: str) -> dict[str, str]
```

Extract text from file bytes.

Writes bytes to a temp file, converts, then cleans up.

Args:
    content (bytes): Raw file bytes.
    filename (str): Original filename (used to determine format by extension).

Returns:
    dict[str, str]: Dict with keys 'text' and 'filename'.

Exceptions:
    Exception: On conversion failure.

Example:
    >>> with open("doc.pdf", "rb") as f:
    ...     data = f.read()
    >>> result = extractor.extract_from_bytes(data, "doc.pdf")

### `extract_from_url` — Функция

```python
def extract_from_url(self, url: str) -> dict[str, str]
```

Extract text from a URL (web page, YouTube, remote file).

Args:
    url (str): URL to fetch and convert.

Returns:
    dict[str, str]: Dict with keys 'text' and 'url'.

Exceptions:
    ValueError: If URL is empty.
    Exception: On fetch or conversion failure.

Example:
    >>> result = extractor.extract_from_url("https://example.com/page")
    >>> result["text"]
    '# Page Title'

### `extract_from_stream` — Функция

```python
def extract_from_stream(self, stream: Any, filename: str) -> dict[str, str]
```

Extract text from a file-like stream.

Args:
    stream (Any): File-like object with a read() method.
    filename (str): Filename hint for format detection.

Returns:
    dict[str, str]: Dict with keys 'text' and 'filename'.

Exceptions:
    Exception: On conversion failure.

Example:
    >>> with open("data.xlsx", "rb") as f:
    ...     result = extractor.extract_from_stream(f, "data.xlsx")


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
