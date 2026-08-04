# src/rag — RAG System

**Version:** 0.7.1  
**Project:** AI Assistant (ai_assist)

Модуль реализует полный цикл RAG (Retrieval-Augmented Generation): индексацию документов, векторный поиск, управление профилями и извлечение текста из 40+ форматов.

---

## Структура

```
src/rag/
├── rag_system.py            # Singleton RAGSystem — поиск и управление индексом
├── indexer.py               # RAGIndexer — построение FAISS индекса из файлов
├── incremental_indexer.py   # IncrementalIndexer — инкрементальные обновления
├── document_store.py        # DocumentStore — SQLite хранилище документов и чанков
├── rag_profile_manager.py   # RAGProfileManager — управление профилями (~/.ai-assist/rag/)
└── text_extractor_4_rag/
    ├── extractors.py        # TextExtractor — извлечение текста из файлов и URL
    ├── config.py            # Settings — конфигурация экстрактора
    ├── main.py              # Standalone FastAPI микросервис (опционально)
    └── utils.py             # Вспомогательные функции
```

---

## Компоненты

### RAGSystem (`rag_system.py`)

Основной singleton для поиска. Загружается при старте приложения через `lifespan`.

```python
from src.rag.rag_system import rag_system

await rag_system.initialize()                    # загрузить индекс из config.rag_index_dir
results = await rag_system.search("запрос", top_k=5)
await rag_system.reload_index("/path/to/profile") # переключить профиль
context = rag_system.format_context(results)
```

Возможности:
- Ленивая загрузка модели SentenceTransformers
- Кэш поиска (сбрасывается при `reload_index`)
- Проверка целостности индекса перед загрузкой
- Проверка совместимости размерности векторов
- Удаление дубликатов чанков
- Фильтрация по источнику (`filter_by_source`) и оценке (`filter_by_score`)

---

### RAGIndexer (`indexer.py`)

Построение FAISS индекса из директории с документами. Поддерживает инкрементальную индексацию (пропускает неизменённые файлы по MD5).

**Поддерживаемые форматы:** `.md`, `.txt`, `.html`, `.rst`

```python
from src.rag.indexer import RAGIndexer
from pathlib import Path

indexer = RAGIndexer(model_name="sentence-transformers/all-mpnet-base-v2")
indexer.load_model()
indexer.index_directory(Path("docs"), chunk_size=1000, overlap=50)
indexer.create_embeddings()
indexer.save_index(Path("rag_index"))
```

CLI:
```powershell
python -m src.rag.indexer --docs-dir docs --output-dir rag_index --chunk-size 1000
```

Артефакты в `output-dir`:
- `faiss.index` — векторный индекс
- `chunks.json` — метаданные чанков
- `index_info.json` — информация о модели и дате создания

---

### IncrementalIndexer (`incremental_indexer.py`)

Инкрементальные обновления FAISS без полной перестройки. Использует `IndexIDMap` для стабильных ID векторов.

```python
from src.rag.incremental_indexer import get_indexer

indexer = get_indexer()
result = indexer.add_document("Заголовок", "Текст документа", source_path="file.txt")
# → {"success": True, "doc_id": 1, "chunks_added": 3}

indexer.update_document(doc_id=1, title="Новый заголовок", content="Новый текст")
indexer.delete_document(doc_id=1)
indexer.compact()          # перестроить индекс из активных чанков (при >20% неактивных)
stats = indexer.get_stats()
```

Workflow:
```
add_document    → chunk → embed → add vectors to FAISS → save chunks to DB
update_document → deactivate old chunks → re-embed → add new vectors
delete_document → deactivate chunks in DB (FAISS vectors stay, filtered at search)
compact         → rebuild FAISS from active chunks only
```

---

### DocumentStore (`document_store.py`)

SQLite хранилище для документов и их чанков. Обеспечивает инкрементальную индексацию через отслеживание хешей содержимого.

**Схема БД:**
```sql
documents(id, title, content, source_path, content_hash, created_at, updated_at)
chunks(id, document_id, vector_id, chunk_no, text, active)
```

```python
from src.rag.document_store import get_store

store = get_store("rag_index")
doc_id = store.add_document("Заголовок", "Текст", source_path="file.txt")
docs = store.list_documents()
changed = store.content_changed(doc_id, new_content)
store.save_chunks(doc_id, chunks)
stats = store.stats()  # → {"documents": N, "active_chunks": N, "inactive_chunks": N}
```

---

### RAGProfileManager (`rag_profile_manager.py`)

Управление именованными профилями RAG под `~/.ai-assist/rag/<profile>/`. Каждый профиль — отдельный FAISS индекс.

```python
from src.rag.rag_profile_manager import rag_profile_manager

profiles = rag_profile_manager.list_profiles()
path = rag_profile_manager.create_profile("my-docs", description="Документация проекта")
rag_profile_manager.delete_profile("old-profile")  # мягкое удаление (переименование с ~)
```

Переключение профиля:
```python
await rag_system.reload_index(str(path))
```

---

### TextExtractor (`text_extractor_4_rag/`)

Извлечение текста из 40+ форматов файлов и веб-страниц.

**Поддерживаемые форматы:**

| Категория | Форматы |
|---|---|
| Документы | PDF, DOCX, DOC, RTF, ODT |
| Таблицы | XLS, XLSX, CSV, ODS |
| Презентации | PPTX, PPT |
| Изображения (OCR) | JPG, PNG, TIFF, BMP, GIF, WebP |
| Веб | HTML, HTM, MD, EPUB |
| Данные | JSON, XML, YAML |
| Исходный код | Python, JS, TS, Java, C/C++, C#, PHP, Go, Rust, SQL, Shell, PowerShell и др. |
| Архивы | ZIP, RAR, 7Z, TAR, GZ, BZ2 (с защитой от zip-bomb) |
| Email | EML, MSG |

```python
from src.rag.text_extractor_4_rag.extractors import TextExtractor

extractor = TextExtractor()

# Из файла
with open("document.pdf", "rb") as f:
    results = extractor.extract_text(f.read(), "document.pdf")

# С URL
results = extractor.extract_from_url("https://example.com/page")
```

Каждый результат:
```python
{
    "filename": "document.pdf",
    "path": "document.pdf",
    "size": 12345,
    "type": "pdf",
    "text": "Извлечённый текст..."
}
```

**Конфигурация** (`config.json` → секция `text_extractor`):

| Параметр | По умолчанию | Описание |
|---|---|---|
| `max_file_size_mb` | 20 | Максимальный размер файла |
| `processing_timeout_seconds` | 300 | Таймаут обработки |
| `ocr_languages` | `rus+eng` | Языки Tesseract OCR |
| `tesseract_cmd` | `""` | Путь к tesseract (задаётся `install-tesseract.ps1`) |
| `enable_javascript` | `false` | JS-рендеринг через Playwright |
| `max_images_per_page` | 20 | Лимит изображений при веб-извлечении |
| `web_page_timeout` | 30 | Таймаут загрузки страницы (сек) |

---

## Файлы индекса

| Файл | Назначение |
|---|---|
| `rag_index/faiss.index` | Векторный индекс FAISS |
| `rag_index/chunks.json` | Метаданные текстовых чанков |
| `rag_index/documents.db` | SQLite БД (IncrementalIndexer) |
| `rag_index/index_info.json` | Информация о модели и дате создания |
| `~/.ai-assist/rag/<profile>/` | Директории профилей |
| `~/.ai-assist/rag/<profile>/meta.json` | Метаданные профиля |

---

## Конфигурация

Параметры RAG в `config.json`:

```json
{
  "rag_system": {
    "enabled": true,
    "index_dir": "rag_index",
    "model": "sentence-transformers/all-mpnet-base-v2",
    "chunk_size": 1000,
    "top_k": 5,
    "source_dirs": ["docs/"]
  }
}
```

Доступ через Config singleton:
```python
from src.core.config import config

config.rag_enabled      # bool
config.rag_index_dir    # str
config.rag_model        # str
config.rag_chunk_size   # int
config.rag_top_k        # int
```

---

## Зависимости

```
faiss-cpu
sentence-transformers
numpy
pdfplumber, PyPDF2
python-docx, python-pptx, openpyxl, pandas
beautifulsoup4, lxml
pytesseract, Pillow
odfpy, striprtf, PyYAML
rarfile, py7zr
requests, playwright (опционально, для JS-рендеринга)
```
