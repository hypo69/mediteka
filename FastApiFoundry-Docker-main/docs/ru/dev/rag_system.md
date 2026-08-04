# RAG система (Retrieval-Augmented Generation)

Модуль `src/rag/` — полный стек индексации и поиска по документам.

---

## Архитектура — компоненты и их роли

```
POST /rag/index/stream
        │
        ▼
  DocumentIngestor          ← извлечение текста (MarkItDown / TextExtractor)
  src/rag/document_ingestor.py
        │
        ▼
  RAGPipeline               ← координация: ingest → chunk → embed → store
  src/rag/rag_pipeline.py
        │
        ▼
  IncrementalIndexer        ← chunk + embed + FAISS IndexIDMap + SQLite
  src/rag/incremental_indexer.py
        │
        ├── DocumentStore   ← SQLite: documents + chunks (documents.db)
        │   src/rag/document_store.py
        │
        └── faiss.IndexIDMap  ← векторный индекс (faiss.index)

  RAGSystem                 ← поиск по активному индексу
  src/rag/rag_system.py
```

---

## Полный цикл индексации

```
ЗАГРУЗКА ФАЙЛА (POST /rag/index/stream)
  │
  ├─ DocumentIngestor.process_upload(file)
  │     ├─ tempfile.mkstemp()  ← байты → временный файл на диске
  │     ├─ _process_file_recursive()
  │     │     ├─ архивы (zip/7z/rar/tar): распаковать → рекурсия
  │     │     ├─ docx/pptx/xlsx/pdf/html: MarkItDown
  │     │     └─ остальное: TextExtractor
  │     └─ os.remove(temp)  ← гарантированно в finally
  │
  ├─ RAGPipeline.add_text(title, content, source)
  │     └─ IncrementalIndexer.add_document()
  │           ├─ _chunk_text()   ← нарезка: chunk_size // 8 overlap
  │           ├─ _embed()        ← SentenceTransformer, батчи по 16
  │           ├─ DocumentStore.add_document() + save_chunks()  ← SQLite
  │           ├─ faiss.IndexIDMap.add_with_ids()  ← векторы с chunk.id
  │           └─ _save_index()   ← атомарно через .tmp файл
  │
  └─ rag_system.reload_index()  ← обновить активный индекс в памяти

ПОИСК (POST /rag/search)
  │
  └─ RAGSystem.search(query, top_k)
        ├─ _search_cache[(query, top_k)]  ← кэш
        ├─ SentenceTransformer.encode(query)
        ├─ faiss.index.search(vector, top_k)
        └─ [{content, score, source, ...}, ...]
```

---

## Хранилище индекса

Каждый профиль — отдельная директория в `~/.ai-assist/rag/`:

```
~/.ai-assist/rag/
└── train_data/           ← имя профиля
    ├── faiss.index       ← FAISS IndexIDMap (векторы с ID = chunk.id)
    ├── documents.db      ← SQLite: таблицы documents + chunks
    ├── meta.json         ← chunks, model, updated_at
    └── README.md         ← описание базы (отображается в UI)
```

!!! warning "Устаревший формат"
    Старые профили могут содержать `chunks.json` вместо `documents.db`.
    Используйте `POST /api/v1/rag/migrate/index-id-map` для миграции.

Активный профиль задаётся в `config.json`:

```json
{
  "rag_system": {
    "index_dir": "~/.ai-assist/rag/train_data",
    "enabled": true
  }
}
```

---

## IncrementalIndexer

**Файл:** `src/rag/incremental_indexer.py`  
**Синглтон:** `get_indexer(index_dir)`

Управляет инкрементальными обновлениями FAISS + SQLite.

### Ключевые особенности

**FAISS IndexIDMap** — каждый вектор имеет стабильный ID, равный `chunk.id` из SQLite.
Это позволяет удалять документы без перестройки всего индекса: чанки помечаются
неактивными в SQLite, а при поиске фильтруются.

**Нарезка текста** — `_chunk_text()`:
- Размер чанка: `config.rag_chunk_size` (по умолчанию 1000 символов)
- Перекрытие: `chunk_size // 8` (~125 символов)
- Простая нарезка по символам без учёта границ предложений

**Эмбеддинги** — `_embed()`:
- Модель: `config.rag_model` (ленивая загрузка при первом вызове)
- Батчи по 16 чанков при наличии `progress_cb`
- L2-нормализация → Inner Product = cosine similarity

**Автоматический compact** — `_maybe_compact()`:
- Вызывается после каждого `add_document` / `update_document` / `delete_document`
- Срабатывает если `inactive_chunks / total > 0.2`
- Перестраивает FAISS только из активных чанков

### Методы

| Метод | Описание |
|---|---|
| `add_document(title, content, source_path)` | Добавить документ: chunk → embed → FAISS + DB |
| `update_document(doc_id, title, content)` | Обновить: деактивировать старые чанки, добавить новые |
| `delete_document(doc_id)` | Soft-delete: деактивировать чанки в SQLite |
| `compact()` | Перестроить FAISS только из активных чанков |
| `get_stats()` | Статистика: documents, active_chunks, faiss_vectors, compact_recommended |

---

## RAGPipeline

**Файл:** `src/rag/rag_pipeline.py`  
**Фабрика:** `get_pipeline(index_dir=None)`

Координирует полный цикл: ingest → index → reload.

### Методы

| Метод | Описание |
|---|---|
| `ingest_upload(file)` | Извлечь текст + проиндексировать, вернуть dict |
| `ingest_upload_stream(file)` | То же, но AsyncIterator с SSE-событиями прогресса |
| `ingest_url(url)` | Извлечь текст с URL + проиндексировать |
| `add_text(title, content, source)` | Проиндексировать уже извлечённый текст |
| `migrate_to_index_id_map()` | Мигрировать legacy chunks.json → SQLite + IndexIDMap |

### SSE-события `ingest_upload_stream`

| `stage` | Когда | Поля |
|---|---|---|
| `extract` | начало и конец извлечения | `message`, `done`, `chars`, `method` |
| `chunk` | перед нарезкой | `message` |
| `embed` | каждые 16 чанков | `message`, `done`, `total` |
| `index` | после записи в FAISS | `message`, `done` |
| `done` | финал | `success`, `source`, `chunks`, `chars` |
| `error` | при ошибке | `message` |

---

## DocumentIngestor

**Файл:** `src/rag/document_ingestor.py`

Извлекает текст из загруженных файлов перед индексацией.

### Стратегия выбора экстрактора

| Формат | Экстрактор |
|---|---|
| `.docx`, `.pptx`, `.xlsx`, `.pdf`, `.html` | MarkItDown (основной) → TextExtractor (fallback) |
| `.zip`, `.tar`, `.tar.gz`, `.tgz` | встроенный zipfile / tarfile + рекурсия |
| `.7z` | py7zr (опционально) |
| `.rar` | rarfile (опционально) |
| всё остальное | TextExtractor |

### Временные файлы

Все экстракторы работают с путями к файлам на диске, а не с байтами в памяти.
Поэтому `process_upload()` сохраняет `UploadFile` во временный файл:

```
UploadFile → tempfile.mkstemp(suffix=ext) → обработка → os.remove()
```

Суффикс берётся из `os.path.basename(filename)`, чтобы избежать ошибок
при именах вида `ru/about.md` (загрузка директории через `webkitdirectory`).

---

## RAGSystem

**Файл:** `src/rag/rag_system.py`  
**Синглтон:** `rag_system`

Управляет активным индексом в памяти и выполняет поиск.

### Методы

| Метод | Описание |
|---|---|
| `initialize()` | Загрузить индекс при старте (lifespan) |
| `reload_index(index_dir)` | Перезагрузить индекс без перезапуска сервера |
| `search(query, top_k)` | Векторный поиск, результаты кэшируются |
| `filter_by_score(results, min_score)` | Отфильтровать по порогу схожести |
| `format_context(results)` | Объединить чанки для передачи в LLM |

---

## Модели эмбеддингов

```json
"rag_system": {
  "model": "sentence-transformers/all-MiniLM-L6-v2"
}
```

| Модель | Размерность | Размер | Рекомендация |
|---|---|---|---|
| `all-MiniLM-L6-v2` | 384 | ~80 MB | по умолчанию, быстрая |
| `all-mpnet-base-v2` | 768 | ~420 MB | лучшее качество |
| `paraphrase-multilingual-MiniLM-L12-v2` | 384 | ~120 MB | мультиязычные тексты |

!!! warning "Модель при индексации и поиске должна совпадать"
    При несовпадении размерности векторов индекс отклоняется.
    Нужно пересобрать индекс с новой моделью.

---

## API Endpoints

**Файл:** `src/api/endpoints/rag.py`  
**Prefix:** `/api/v1/rag`

| Метод | Путь | Описание |
|---|---|---|
| `GET` | `/rag/status` | Статус: enabled, index_dir, model, total_chunks |
| `PUT` | `/rag/config` | Обновить секцию `rag_system` в config.json |
| `POST` | `/rag/search` | Поиск: `{query, top_k, min_score}` |
| `POST` | `/rag/query` | Поиск + генерация ответа LLM, поддерживает SSE |
| `POST` | `/rag/build` | Построить индекс из серверной директории |
| `POST` | `/rag/index` | Загрузить файл/архив и проиндексировать |
| `POST` | `/rag/index/stream` | То же с SSE-прогрессом по этапам |
| `POST` | `/rag/index/batch` | Пакетная загрузка нескольких файлов |
| `POST` | `/rag/clear` | Удалить файлы индекса из index_dir |
| `POST` | `/rag/compact` | Перестроить FAISS из активных чанков |
| `POST` | `/rag/migrate/index-id-map` | Мигрировать legacy chunks.json → SQLite |
| `GET` | `/rag/profiles` | Список профилей из `~/.ai-assist/rag/` |
| `POST` | `/rag/profiles/load` | Переключить активный профиль |
| `POST` | `/rag/profiles/{name}/activate` | Активировать профиль |
| `POST` | `/rag/profiles/deactivate` | Отключить RAG |
| `DELETE` | `/rag/profiles/{name}` | Удалить профиль |
| `GET` | `/rag/documents` | Список документов в хранилище |
| `POST` | `/rag/documents` | Добавить документ вручную |
| `GET` | `/rag/documents/{id}` | Получить документ по id |
| `PUT` | `/rag/documents/{id}` | Обновить документ |
| `DELETE` | `/rag/documents/{id}` | Удалить документ |
| `POST` | `/rag/documents/{id}/reindex` | Принудительно переиндексировать |
| `GET` | `/rag/documents/stats` | Статистика: documents, chunks, faiss_vectors |
| `GET` | `/rag/dirs` | Список директорий с текстовыми файлами |
| `GET` | `/rag/cwd` | Текущая рабочая директория сервера |
| `GET` | `/rag/browse` | Обзор файловой системы |
| `POST` | `/rag/extract/file` | Извлечь текст из файла (без индексации) |
| `POST` | `/rag/extract/url` | Извлечь текст с URL (без индексации) |
| `GET` | `/rag/extract/formats` | Список поддерживаемых форматов |

---

## Построение индекса в Google Colab

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/hypo69/FastApiFoundry-Docker/blob/master/notebooks%5Crag_colab.ipynb)

На слабом CPU индексация тысяч документов может занять часы.
Google Colab предоставляет бесплатный GPU T4, который ускоряет процесс в 10–30 раз.

| Ситуация | Локально | Colab T4 |
|---|---|---|
| 1 000 чанков | ~2–5 мин | ~10–20 сек |
| 10 000 чанков | ~20–50 мин | ~2–5 мин |

После скачивания `rag_index.zip` распакуйте в профиль:

```powershell
Expand-Archive rag_index.zip -DestinationPath "$env:USERPROFILE\.ai-assist\rag\my_docs"
```

Затем в веб-интерфейсе: **RAG → RAG Bases → Load**.
