# Rag Ingestor

**Файл:** `src/api/endpoints/rag_ingestor.py`  
**Тип:** `.py`

---

### `DocumentIngestor` — Класс

```python
class DocumentIngestor
```

!
Класс, отвечающий за подготовку данных к RAG.
Инкапсулирует логику выбора инструментов и первичной обработки.

### `__init__` — Функция

```python
def __init__(self, settings: dict)
```

### `_clean_text` — Функция

```python
def _clean_text(self, text: str) -> str
```

Очистка текста от лишних пробелов и пустых строк перед отправкой в RAG.

### `process_upload` — Функция

```python
async def process_upload(self, file: UploadFile) -> Tuple[str, str, str, str]
```

Обработка загруженного файла.

### `process_url` — Функция

```python
async def process_url(self, url: str) -> Tuple[str, str, str, str]
```

Обработка контента по ссылке.


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
