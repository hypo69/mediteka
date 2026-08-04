# Rag

**Файл:** `js/rag.js`  
**Тип:** `.js`

---

### `refreshRAGStatus`

rag.js — Система RAG
 *
 * Содержит:
 *  - refreshRAGStatus()      — статус активной базы
 *  - ragLoadProfiles()       — список баз в ~/.ai-assist/rag
 *  - ragAddDirectory()       — добавить строку выбора директории
 *  - ragRemoveDirectory(idx) — удалить строку директории
 *  - ragOpenBrowserFor(idx)  — открыть браузер для конкретной строки
 *  - ragBuildIndex(force)    — собрать индексы для всех выбранных директорий
 *  - testRAGSearch()         — тестовый поиск
 *  - clearRAGChunks()        — очистить активный индекс
 *  - handleRAGToggle()       — переключатель Enable RAG

### `ragLoadProfiles`

Загружает список RAG баз из ~/.ai-assist/rag и отрисовывает в #rag-profiles-list.
 * Каждая база показывает кнопки Activate, Disable и Delete.

### `ragLoadProfile`

Активирует выбранную RAG базу — переключает index_dir в config.json
 * и перезагружает RAG систему.
 *

| Параметр | Тип | Описание |
|---|---|---|
| `name` | `string` | */ |

### `ragDeactivateProfiles`

Отключает RAG без удаления индексов.

### `ragDeleteProfile`

Удаляет RAG базу из ~/.ai-assist/rag/<name>/.
 *

| Параметр | Тип | Описание |
|---|---|---|
| `name` | `string` | */ |

### `ragAddDirectory`

Adds a new directory row and immediately opens the browser for it.

### `ragRemoveDirectory`

Removes a directory row by its index.
 *

| Параметр | Тип | Описание |
|---|---|---|
| `idx` | `number` | */ |

### `ragGetSelectedDirs`

Returns all non-empty directory paths from the list.
 *

### `ragOpenBrowserFor`

Opens the directory browser modal for a specific row index.

### `ragOpenDirBrowser`

Opens the directory browser for the "Index Directory" tab.

### `ragOpenBrowser`

### `ragBrowseTo`

Навигация в директорию path.

### `ragBrowserUp`

Переход на уровень выше.

### `ragBrowserConfirm`

Подтверждает выбор текущей директории и записывает в целевую строку.

### `ragBuildIndex`

Builds RAG index for each selected directory sequentially.
 *

| Параметр | Тип | Описание |
|---|---|---|
| `force` | `boolean` | rebuild even if index already exists |

### `ragIndexDirectoryFiles`

Indexes files from a locally selected directory (via <input webkitdirectory>).
 * Sends all files one-by-one through /rag/index/stream with SSE progress.

### `_progressHtml`

| Параметр | Тип | Описание |
|---|---|---|
| `msg` | `string` | @param {number} pct @param {string} cls */ |

### `ragUploadArchive`

Uploads files/archives one-by-one via SSE endpoint /rag/index/stream.
 * Shows per-stage progress: extract → chunk → embed (progress bar) → index → done.

### `_applyProgressEvent`

Updates the per-file progress block based on a pipeline SSE event.
 *

| Параметр | Тип | Описание |
|---|---|---|
| `fileId` | `string` | * @param {{stage:string, message?:string, done?:number, total?:number, chunks?:number}} ev |

### `testRAGSearch`

Тестовый поиск по активной RAG базе.
 * Читает запрос из #rag-test-query.

### `clearRAGChunks`

Очищает активный RAG индекс (кнопка в Settings)

### `handleRAGToggle`

Уведомление при переключении чекбокса Enable RAG

### `showExtractionPreview`

Renders extraction results into the preview textarea.
 *

| Параметр | Тип | Описание |
|---|---|---|
| `files` | `Array` | array of {filename, text, size, type} objects |
| `sourceName` | `string` | display name (filename or URL) |

### `extractFromFile`

Extracts text from the selected file via POST /api/v1/rag/extract/file.

### `extractFromURL`

Extracts text from a URL via POST /api/v1/rag/extract/url.

### `copyExtractedText`

Copies extracted text to clipboard.

### `ragLoadDocuments`

Load and render the document list from /api/v1/rag/documents.

### `ragShowAddModal`

Open the Add Document modal.

### `ragEditDocument`

Load document data into the modal for editing.

### `ragSaveDocument`

Save (add or update) document from modal.

### `ragReindexDocument`

Force reindex a single document.

### `ragDeleteDocument`

Delete a document after confirmation.

### `ragCompactIndex`

Compact FAISS index (remove dead vectors).

### `_esc`

### `_fmtDate`


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
