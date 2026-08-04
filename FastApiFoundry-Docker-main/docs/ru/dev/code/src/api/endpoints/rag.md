# Rag

**Файл:** `src/api/endpoints/rag.py`  
**Тип:** `.py`

---

### `RAGConfig` — Класс

```python
class RAGConfig(BaseModel)
```

### `RAGSearchRequest` — Класс

```python
class RAGSearchRequest(BaseModel)
```

### `RAGQueryFilterRequest` — Класс

```python
class RAGQueryFilterRequest(BaseModel)
```

### `RAGQueryRequest` — Класс

```python
class RAGQueryRequest(BaseModel)
```

### `RAGBuildRequest` — Класс

```python
class RAGBuildRequest(BaseModel)
```

### `ExtractURLRequest` — Класс

```python
class ExtractURLRequest(BaseModel)
```

### `RAGSearchResult` — Класс

```python
class RAGSearchResult(BaseModel)
```

### `get_rag_status` — Функция

```python
@router.get('/status')
```

Получение статуса системы RAG.

Returns:
    dict: Информация о состоянии: enabled, index_dir, model, chunk_size, total_chunks.

Example:
    >>> status = await get_rag_status()
    >>> print(status['enabled'])
    True

### `update_rag_config` — Функция

```python
@router.put('/config')
```

Обновление конфигурации системы RAG.

Args:
    config (RAGConfig): Модель данных с новыми настройками.

Returns:
    dict: Статус выполнения операции.

### `search_rag` — Функция

```python
@router.post('/search')
```

Выполнение поиска в системе RAG.

Args:
    request (RAGSearchRequest): Запрос с текстом и параметром top_k.

Returns:
    dict: Список результатов с контентом и оценками схожести.

Example:
    >>> res = await search_rag(RAGSearchRequest(query="test", top_k=5, min_score=0.5))
    >>> len(res['results'])
    3

### `_to_service_query` — Функция

```python
def _to_service_query(request: RAGQueryRequest) -> ServiceRAGQueryRequest
```

Convert API request model to service request dataclass.

### `query_rag` — Функция

```python
@router.post('/query')
```

Run retrieval + prompt + generation with optional SSE streaming.

### `rebuild_rag_index` — Функция

```python
@router.post('/rebuild')
```

Пересборка векторного индекса.

Returns:
    dict: Статус запуска процесса пересборки.

### `index_document` — Функция

```python
@router.post('/index')
```

Индексация одного документа или архива через RAGPipeline.

Поддерживаемые форматы архивов: zip, tar, tar.gz, tgz, 7z, rar.
Содержимое архива рекурсивно извлекается и индексируется как единый документ.

### `index_stream` — Функция

```python
@router.post('/index/stream')
```

Индексация одного файла/архива с SSE-прогрессом по всему пайплайну.

Шлёт события вида:
  {"stage": "extract", "message": "..."}
  {"stage": "embed",   "done": 12, "total": 50, "message": "..."}
  {"stage": "index",   "done": true, "message": "..."}
  {"stage": "done",    "success": true, "chunks": 50, "chars": 12345}
  {"stage": "error",   "message": "..."}

Args:
    file (UploadFile): Файл для индексации.

Returns:
    StreamingResponse: text/event-stream с JSON-событиями.

### `index_batch` — Функция

```python
@router.post('/index/batch')
```

Пакетная индексация нескольких файлов или архивов за один запрос.

Args:
    files (List[UploadFile]): Список файлов. Поддерживаются все форматы
        включая zip, tar, tar.gz, tgz, 7z, rar.

Returns:
    dict: success, indexed, total, results, errors.

Example:
    POST /api/v1/rag/index/batch
    Content-Type: multipart/form-data
    files=@docs.zip&files=@manual.pdf

### `clear_rag_chunks` — Функция

```python
@router.post('/clear')
```

Очистка файлов индекса в настроенной директории.

Returns:
    dict: Количество удаленных файлов.

### `list_indexable_dirs` — Функция

```python
@router.get('/dirs')
```

Получение списка директорий, доступных для индексации.

Returns:
    dict: Список путей с количеством найденных текстовых файлов.

### `_rag_home` — Функция

```python
def _rag_home() -> Path
```

Получение домашней директории RAG (~/.aiassistant/rag).

### `_profile_index_dir` — Функция

```python
def _profile_index_dir(safe_name: str) -> Path
```

Получение пути к директории профиля.

### `get_cwd` — Функция

```python
@router.get('/cwd')
```

Получение текущей рабочей директории сервера.

### `browse_filesystem` — Функция

```python
@router.get('/browse')
```

Просмотр файловой системы для выбора папок.

Args:
    path (str): Абсолютный путь для обзора. По умолчанию домашняя папка.

Returns:
    dict: Список вложенных папок и информация о текущем пути.

Raises:
    HTTPException: Если путь не существует или не является директорией.

### `list_rag_profiles` — Функция

```python
@router.get('/profiles')
```

Получение списка всех профилей RAG в директории ~/.aiassistant/rag/.

Returns:
    dict: success, profiles.

### `load_rag_profile` — Функция

```python
@router.post('/profiles/load')
```

Переключение активного профиля RAG.

Args:
    request (dict): Тело запроса с полем 'name'.

Returns:
    dict: Результат загрузки и путь к новому индексу.

### `activate_rag_profile` — Функция

```python
@router.post('/profiles/{name}/activate')
```

Подключить RAG профиль и сделать его активным.

### `deactivate_rag_profiles` — Функция

```python
@router.post('/profiles/deactivate')
```

Отключить использование RAG без удаления индексов с диска.

### `delete_rag_profile` — Функция

```python
@router.delete('/profiles/{name}')
```

Удаление профиля RAG с диска.

Args:
    name (str): Имя профиля.

Returns:
    dict: Статус удаления.

### `build_rag_index` — Функция

```python
@router.post('/build')
```

Создание векторного индекса из локальной директории.

Args:
    request (RAGBuildRequest): Параметры сборки (путь, модель, размер чанка).

Returns:
    dict: Статистика сборки: количество сегментов, признак пересборки.

### `extract_text_from_file` — Функция

```python
@router.post('/extract/file')
```

Извлечение текста из загруженного файла.

Args:
    file (UploadFile): Файл для обработки.

Returns:
    dict: Извлеченный текст и метаданные.

### `extract_text_from_url` — Функция

```python
@router.post('/extract/url')
```

Извлечение контента с веб-страницы.

Args:
    request (ExtractURLRequest): URL и параметры парсинга (JS, изображения).

Returns:
    dict: Текстовое содержимое страницы.

### `get_supported_formats` — Функция

```python
@router.get('/extract/formats')
```

Получение списка поддерживаемых форматов для извлечения текста.

Returns:
    dict: Список расширений.

### `DocumentAddRequest` — Класс

```python
class DocumentAddRequest(BaseModel)
```

### `DocumentUpdateRequest` — Класс

```python
class DocumentUpdateRequest(BaseModel)
```

### `_get_indexer` — Функция

```python
def _get_indexer()
```

Return the IncrementalIndexer singleton.

### `_reload_active_rag_index` — Функция

```python
async def _reload_active_rag_index() -> None
```

Reload the active FAISS index after an incremental write.

### `list_documents` — Функция

```python
@router.get('/documents')
```

Список всех документов в хранилище.

Returns:
    dict: success, documents — список с id, title, chunk_count, updated_at.

### `add_document` — Функция

```python
@router.post('/documents')
```

Добавить документ и проиндексировать его инкрементально.

Args:
    request (DocumentAddRequest): title, content, source_path.

Returns:
    dict: success, doc_id, chunks_added.

Example:
    POST /api/v1/rag/documents
    {"title": "Manual", "content": "..."}

### `get_document` — Функция

```python
@router.get('/documents/{doc_id}')
```

Получить документ по id.

Args:
    doc_id (int): Document id.

Returns:
    dict: success, document.

### `update_document` — Функция

```python
@router.put('/documents/{doc_id}')
```

Обновить документ и переиндексировать если контент изменился.

Args:
    doc_id (int): Document id.
    request (DocumentUpdateRequest): title, content.

Returns:
    dict: success, chunks_added, changed.

### `delete_document` — Функция

```python
@router.delete('/documents/{doc_id}')
```

Удалить документ и деактивировать его чанки.

Args:
    doc_id (int): Document id.

Returns:
    dict: success.

### `reindex_document` — Функция

```python
@router.post('/documents/{doc_id}/reindex')
```

Принудительно переиндексировать один документ.

Args:
    doc_id (int): Document id.

Returns:
    dict: success, chunks_added.

### `compact_index` — Функция

```python
@router.post('/compact')
```

Перестроить FAISS индекс из активных чанков (удалить мёртвые векторы).

Returns:
    dict: success, vectors_before, vectors_after.

### `migrate_to_index_id_map` — Функция

```python
@router.post('/migrate/index-id-map')
```

Migrate legacy FAISS/chunks.json profile to SQLite-backed IndexIDMap.

### `get_document_stats` — Функция

```python
@router.get('/documents/stats')
```

Статистика хранилища документов и FAISS индекса.

Returns:
    dict: documents, active_chunks, inactive_chunks, faiss_vectors, compact_recommended.

### `_events` — Функция

```python
async def _events()
```

### `_events` — Функция

```python
async def _events()
```

### `_run` — Функция

```python
def _run() -> tuple[int, bool]
```


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
