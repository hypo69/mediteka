# Extractor

**Файл:** `src/rag/text_extractors/whisper/extractor.py`  
**Тип:** `.py`

---

### `WhisperExtractor` — Класс

```python
class WhisperExtractor
```

Local audio transcription extractor using faster-whisper.

Transcribes audio files to text suitable for RAG indexing.
Model is lazy-loaded on first use and cached for subsequent calls.

Args:
    model_size (str): Whisper model size. One of: tiny, base, small,
        medium, large-v2, large-v3. Default: 'base'.
    device (str): Compute device — 'cpu' or 'cuda'. Default: 'cpu'.
    compute_type (str): Quantization type. 'int8' for CPU (fastest),
        'float16' for GPU. Default: 'int8'.
    language (str | None): Force language code (e.g. 'ru', 'en').
        None = auto-detect. Default: None.

Example:
    >>> extractor = WhisperExtractor(model_size="base")
    >>> result = extractor.extract_from_file("interview.mp3")
    >>> print(result["text"])

### `__init__` — Функция

```python
def __init__(self, model_size: str='base', device: str='cpu', compute_type: str='int8', language: str | None=None) -> None
```

### `_get_model` — Функция

```python
def _get_model(self) -> Any
```

Lazy-initialize faster-whisper model.

Returns:
    WhisperModel: Loaded faster-whisper model instance.

Exceptions:
    ImportError: If faster-whisper is not installed.

### `is_supported` — Функция

```python
def is_supported(self, filename: str) -> bool
```

Check if the file extension is supported for transcription.

Args:
    filename (str): Filename or path to check.

Returns:
    bool: True if the extension is in the supported set.

Example:
    >>> WhisperExtractor().is_supported("lecture.mp3")
    True
    >>> WhisperExtractor().is_supported("report.pdf")
    False

### `extract_from_file` — Функция

```python
def extract_from_file(self, file_path: str | Path) -> dict[str, Any]
```

Transcribe audio from a local file.

Args:
    file_path (str | Path): Path to the audio file.

Returns:
    dict[str, Any]: Dict with keys:
        - 'text' (str): Full transcription joined by spaces.
        - 'filename' (str): Original filename.
        - 'language' (str): Detected or forced language code.
        - 'segments' (list[dict]): Per-segment dicts with
          'start', 'end', 'text'.

Exceptions:
    FileNotFoundError: If file_path does not exist.
    ValueError: If file extension is not supported.
    ImportError: If faster-whisper is not installed.

Example:
    >>> extractor = WhisperExtractor()
    >>> result = extractor.extract_from_file("meeting.wav")
    >>> result["language"]
    'ru'

### `extract_from_bytes` — Функция

```python
def extract_from_bytes(self, content: bytes, filename: str) -> dict[str, Any]
```

Transcribe audio from raw bytes.

Writes bytes to a temp file, transcribes, then cleans up.

Args:
    content (bytes): Raw audio file bytes.
    filename (str): Original filename (used for extension detection).

Returns:
    dict[str, Any]: Same structure as extract_from_file.

Exceptions:
    ValueError: If file extension is not supported.
    ImportError: If faster-whisper is not installed.

Example:
    >>> with open("audio.mp3", "rb") as f:
    ...     data = f.read()
    >>> result = extractor.extract_from_bytes(data, "audio.mp3")

### `_transcribe` — Функция

```python
def _transcribe(self, path: Path, filename: str) -> dict[str, Any]
```

Run faster-whisper transcription on a file path.

Args:
    path (Path): Path to the audio file on disk.
    filename (str): Display name for logging and result.

Returns:
    dict[str, Any]: Transcription result with text, language, segments.


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
