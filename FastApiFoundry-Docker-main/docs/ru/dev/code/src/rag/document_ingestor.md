# Document Ingestor

**Файл:** `src/rag/document_ingestor.py`  
**Тип:** `.py`

---

### `DocumentIngestor` — Класс

```python
class DocumentIngestor
```

Подготовка документов к индексации в RAG.

Инкапсулирует выбор инструментов извлечения текста и первичную обработку.

Архитектурное ограничение — временные файлы:
    Все внутренние методы (_process_file_recursive, MarkItDown, zipfile,
    tarfile, py7zr, rarfile) работают с путями к файлам на диске, а не
    с байтами в памяти. Поэтому process_upload() обязан сохранить
    содержимое UploadFile во временный файл перед обработкой.

    Временный файл создаётся через tempfile.mkstemp() в системной
    temp-директории (например %TEMP% или /tmp).
    Суффикс берётся из basename(filename), чтобы избежать ошибок
    при именах вида "ru/about.md" (webkitdirectory upload).
    Файл гарантированно удаляется в блоке finally.

    TODO: рефакторинг на работу с io.BytesIO позволит убрать temp-файлы,
    но требует переписать все зависимые экстракторы.

### `__init__` — Функция

```python
def __init__(self, settings: dict)
```

### `_clean_text` — Функция

```python
def _clean_text(self, text: str) -> str
```

Очистка текста от лишних пробелов и пустых строк перед отправкой в RAG.

### `_detect_language` — Функция

```python
async def _detect_language(self, text: str) -> str
```

Определение языка с поддержкой различных стратегий (FastText или Translator).

### `_extract_pdf_metadata` — Функция

```python
def _extract_pdf_metadata(self, file_path: str) -> Dict[str, Any]
```

Извлечение метаданных из PDF-файла.

### `_extract_pdf_annotations` — Функция

```python
def _extract_pdf_annotations(self, file_path: str) -> str
```

Извлечение комментариев и заметок из PDF-файла.

### `_extract_pdf_form_data` — Функция

```python
def _extract_pdf_form_data(self, file_path: str) -> str
```

Извлечение данных из интерактивных форм PDF (AcroForms).

### `_ocr_images_in_docx` — Функция

```python
async def _ocr_images_in_docx(self, docx_path: str) -> str
```

Извлечение текста из изображений внутри DOCX через OCR.

### `_extract_docx_metadata` — Функция

```python
def _extract_docx_metadata(self, file_path: str) -> Dict[str, Any]
```

Извлечение метаданных из DOCX-файла.

### `_extract_docx_comments` — Функция

```python
def _extract_docx_comments(self, file_path: str) -> str
```

Извлечение комментариев и примечаний из DOCX-файла.

### `_extract_docx_hyperlinks` — Функция

```python
def _extract_docx_hyperlinks(self, file_path: str) -> str
```

Извлечение гиперссылок из DOCX-файла.

### `_extract_docx_tracked_changes` — Функция

```python
def _extract_docx_tracked_changes(self, file_path: str) -> str
```

Извлечение текста из заблокированных (Track Changes) правок в DOCX-файле.

### `_extract_docx_hidden_text` — Функция

```python
def _extract_docx_hidden_text(self, file_path: str) -> str
```

Извлечение скрытого текста из DOCX-файла (теги w:vanish).

### `_extract_docx_custom_properties` — Функция

```python
def _extract_docx_custom_properties(self, file_path: str) -> Dict[str, Any]
```

Извлечение пользовательских свойств (Custom Properties) из DOCX-файла.

### `_check_archive_limits` — Функция

```python
def _check_archive_limits(self, name: str, files: int, max_files: int, size: int, max_mb: int) -> None
```

Валидация количественных показателей архива перед распаковкой.

### `_process_file_recursive` — Функция

```python
async def _process_file_recursive(self, file_path: str, source_name: str) -> Tuple[str, str, Dict[str, Any]]
```

Внутренний метод для рекурсивной обработки файлов (включая ZIP).

### `_finalize_and_detect` — Функция

```python
async def _finalize_and_detect(self, raw_content: str, source_name: str, method: str, meta: Dict[str, Any]) -> Tuple[str, str, str, Dict[str, Any]]
```

### `process_upload` — Функция

```python
async def process_upload(self, file: UploadFile) -> Tuple[str, str, str, Dict[str, Any]]
```

Обработка загруженного файла через временный файл на диске.

Почему используется временный файл:
    FastAPI передаёт содержимое как UploadFile (SpooledTemporaryFile
    в памяти), но все нижележащие экстракторы (MarkItDown, zipfile,
    tarfile, py7zr, rarfile) требуют путь к файлу на диске.
    Поэтому байты сначала сбрасываются в tempfile.mkstemp(), а после
    обработки файл удаляется.

Почему mkstemp, а не f"temp_{filename}":
    file.filename при загрузке директории через <input webkitdirectory>
    содержит относительный путь (например "ru/about.md"). Конкатенация
    "temp_" + "ru/about.md" даёт несуществующий путь "temp_ru/about.md".
    mkstemp создаёт файл в системной temp-директории, используя только
    расширение из basename(filename).

Args:
    file (UploadFile): Загруженный файл. filename может содержать
        относительный путь (webkitdirectory), используется только
        как source_name для метаданных индекса.

Returns:
    Tuple[str, str, str, Dict]: (text, source_name, method, metadata).

### `process_url` — Функция

```python
async def process_url(self, url: str) -> Tuple[str, str, str, Dict[str, Any]]
```

Обработка URL через TextExtractor.


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
