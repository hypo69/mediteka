# Инкрементальный RAG — управление знаниями

**Версия:** 0.7.1  
**Файлы:** `src/rag/document_store.py`, `src/rag/incremental_indexer.py`

---

## Концепция

Статический RAG-индекс устаревает при постоянном добавлении контента.
Инкрементальный пайплайн решает это без полного rebuild:

```
Добавить/Изменить документ
        ↓
  hash-проверка (изменился?)
        ↓
  деактивировать старые чанки
        ↓
  chunk → embed → FAISS.add_with_ids
        ↓
  сохранить в SQLite (DocumentStore)
```

При поиске мёртвые векторы фильтруются через `active=1` в метаданных.
Когда доля неактивных чанков превышает 20% — рекомендуется **Compact**.

---

## Архитектура

```
rag_index/
├── faiss.index       ← IndexIDMap (векторы с явными ID)
├── documents.db      ← SQLite: documents + chunks
└── chunks.json       ← legacy (для совместимости с RAGSystem)
```

### Таблицы SQLite

```sql
documents(id, title, content, source_path, content_hash, created_at, updated_at)
chunks(id, document_id, vector_id, chunk_no, text, active)
```

`chunks.id` используется как `vector_id` в FAISS `IndexIDMap` — это позволяет
точно знать, какой вектор принадлежит какому документу.

---

## API Endpoints

Базовый URL: `/api/v1/rag`

| Метод | Путь | Описание |
|---|---|---|
| `GET` | `/documents` | Список всех документов |
| `POST` | `/documents` | Добавить документ и проиндексировать |
| `GET` | `/documents/{id}` | Получить документ по id |
| `PUT` | `/documents/{id}` | Обновить (переиндексирует если контент изменился) |
| `DELETE` | `/documents/{id}` | Удалить (деактивирует чанки) |
| `POST` | `/documents/{id}/reindex` | Принудительная переиндексация |
| `GET` | `/documents/stats` | Статистика: документы, чанки, FAISS векторы |
| `POST` | `/compact` | Перестроить FAISS из активных чанков |

### Примеры

**Добавить документ:**
```bash
curl -X POST http://localhost:9696/api/v1/rag/documents \
  -H "Content-Type: application/json" \
  -d '{"title": "Руководство", "content": "Текст документа..."}'
```

**Обновить документ:**
```bash
curl -X PUT http://localhost:9696/api/v1/rag/documents/1 \
  -H "Content-Type: application/json" \
  -d '{"title": "Руководство v2", "content": "Обновлённый текст..."}'
```

Если контент не изменился — embeddings не пересчитываются (`changed: false`).

**Compact:**
```bash
curl -X POST http://localhost:9696/api/v1/rag/compact
# {"success": true, "vectors_before": 150, "vectors_after": 120}
```

---

## Веб-интерфейс

Вкладка **RAG** → секция **Document Manager**:

- **Add Document** — открывает модальное окно с полями title / content / source path
- **Edit** (карандаш) — редактировать существующий документ
- **Reindex** (стрелки) — принудительная переиндексация одного документа
- **Delete** (корзина) — удалить документ
- **Compact** — появляется автоматически когда `compact_recommended = true`

Строка статистики показывает: документов / активных чанков / векторов FAISS.

---

## Когда запускать Compact

Compact рекомендуется автоматически когда:

```
inactive_chunks / (active_chunks + inactive_chunks) > 20%
```

Compact перестраивает FAISS из активных чанков, удаляя мёртвые векторы.
Занимает несколько секунд на типичных объёмах.

---

## Классы

### `DocumentStore` (`src/rag/document_store.py`)

SQLite-хранилище. Методы:

- `add_document(title, content, source_path)` → `int` (doc_id)
- `get_document(doc_id)` → `dict | None`
- `list_documents()` → `List[dict]`
- `update_document(doc_id, title, content)` → `bool`
- `delete_document(doc_id)` → `bool`
- `content_changed(doc_id, new_content)` → `bool`
- `save_chunks(doc_id, chunks)` — деактивирует старые, вставляет новые
- `get_active_chunks(doc_id)` → `List[dict]`
- `stats()` → `dict`

### `IncrementalIndexer` (`src/rag/incremental_indexer.py`)

Управляет FAISS + DocumentStore. Методы:

- `add_document(title, content, source_path)` → `dict`
- `update_document(doc_id, title, content)` → `dict`
- `delete_document(doc_id)` → `dict`
- `compact()` → `dict`
- `get_stats()` → `dict`

Синглтон: `get_indexer(index_dir)`.

---

## Важные детали реализации

**IndexIDMap** — FAISS индекс с явными ID:
```python
idx = faiss.IndexIDMap(faiss.IndexFlatIP(dim))
idx.add_with_ids(vectors, ids)  # ids = chunk.id из SQLite
```

**Мягкое удаление** — при удалении документа векторы в FAISS остаются,
но `chunks.active = 0`. При поиске через `RAGSystem` они не возвращаются
(FAISS возвращает ID → проверяем `active` в SQLite).

!!! warning "Совместимость с RAGSystem"
    `IncrementalIndexer` пишет в тот же `faiss.index` что и `RAGSystem`.
    После операций через Document Manager вызывайте `rag_system.reload_index()`
    или перезапустите сервер для обновления in-memory индекса.
