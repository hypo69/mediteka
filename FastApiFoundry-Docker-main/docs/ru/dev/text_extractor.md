# Text Extractor — Документация для разработчиков

Модуль `src/rag/text_extractors/` — набор движков извлечения текста для RAG-пайплайна.
Каждый бэкенд — отдельный пакет с единым интерфейсом.

## Архитектура модуля

```
src/rag/text_extractors/
├── __init__.py                  # Публичный API: TextExtractor, MarkItDownExtractor, WhisperExtractor
├── text_extractor_4_rag/        # Мульти-форматный экстрактор (40+ форматов)
│   ├── __init__.py
│   ├── config.py
│   ├── extractors.py
│   ├── utils.py
│   └── main.py
├── markitdown/                  # Microsoft MarkItDown (Markdown-ориентированный)
│   ├── __init__.py
│   └── extractor.py
└── whisper/                     # Локальная транскрипция аудио (faster-whisper)
    ├── __init__.py
    └── extractor.py
```

## Роль `config.py` в `text_extractor_4_rag`

`config.py` — это не дублирование глобального `config_manager.py`, а **адаптер** между ним и модулем.

| | `config_manager.Config` | `text_extractor_4_rag/config.py` |
|---|---|---|
| Назначение | Глобальные настройки проекта | Адаптер для секции `text_extractor` |
| Доступ | `config.api_port`, `config.rag_enabled` | `settings.MAX_FILE_SIZE`, `settings.OCR_LANGUAGES` |
| Источник данных | `config.json` напрямую | Через `config.get_section("text_extractor")` |
| Статические данные | Нет | `SUPPORTED_FORMATS`, `MIME_TO_EXTENSION` |
| Standalone-режим | Нет | `VERSION`, `API_PORT`, `DEBUG` для `main.py` |

Цепочка чтения настроек:

```
config.json
    ↓
config_manager.Config.get_section("text_extractor")
    ↓
text_extractor_4_rag/config.py — Settings (env var > config.json > default)
    ↓
extractors.py, utils.py — settings.MAX_FILE_SIZE, settings.OCR_LANGUAGES, ...
```

`settings` — прокси-объект: значения не замораживаются при импорте. После `config.reload_config()` можно обновить:

```python
from src.rag.text_extractors.text_extractor_4_rag.config import settings

config.reload_config()   # перечитывает config.json
settings.reload()        # пересоздаёт Settings из обновлённых значений
```

## Класс `TextExtractor`

```python
from src.rag.text_extractors.text_extractor_4_rag import TextExtractor

extractor = TextExtractor()
```

### Методы

#### `extract_text(file_content: bytes, filename: str) -> List[Dict]`

Извлекает текст из файла. Определяет формат по расширению.
Для архивов возвращает список результатов (по одному на каждый файл внутри).

```python
with open("document.pdf", "rb") as f:
    content = f.read()

results = extractor.extract_text(content, "document.pdf")
# [{"filename": "document.pdf", "path": "document.pdf",
#   "size": 204800, "type": "pdf", "text": "..."}]
```

#### `extract_from_url(url: str, user_agent: Optional[str], extraction_options) -> List[Dict]`

Извлекает текст с веб-страницы или файла по URL.
Автоматически определяет тип контента через HEAD-запрос:
- HTML-страница → парсинг через BeautifulSoup
- Файл → скачивание + `extract_text()`

```python
results = extractor.extract_from_url("https://example.com/doc.pdf")
```

### Формат результата

Каждый элемент возвращаемого списка:

```python
{
    "filename": "document.pdf",   # имя файла
    "path": "document.pdf",       # путь (или URL для веб)
    "size": 204800,               # размер в байтах
    "type": "pdf",                # расширение
    "text": "Извлечённый текст"   # чистый текст
}
```

## Класс `Settings`

Все настройки читаются в следующем порядке приоритета (высший побеждает):

1. **Переменная окружения** (`.env` или системная)
2. **`config.json` → секция `text_extractor`**
3. **Встроенное значение по умолчанию**

```python
from src.rag.text_extractors.text_extractor_4_rag.config import settings

print(settings.MAX_FILE_SIZE)       # 20971520 (20 MB)
print(settings.OCR_LANGUAGES)       # "rus+eng"
print(settings.ENABLE_JAVASCRIPT)   # False
```

### Секция `text_extractor` в `config.json`

```json
{
  "text_extractor": {
    "max_file_size_mb": 20,
    "processing_timeout_seconds": 300,
    "ocr_languages": "rus+eng",
    "tesseract_cmd": "",
    "enable_javascript": false,
    "max_images_per_page": 20,
    "web_page_timeout": 30,
    "enable_resource_limits": true,
    "max_archive_nesting": 3,
    "max_extracted_size_mb": 100,
    "max_libreoffice_memory_mb": 1536,
    "max_tesseract_memory_mb": 512
  }
}
```

Эти значения редактируются через вкладку **Settings → Text Extractor** в веб-интерфейсе.

### Полная таблица настроек

| Параметр | config.json ключ | Env var | По умолчанию | Описание |
|---|---|---|---|---|
| Макс. размер файла | `max_file_size_mb` | `MAX_FILE_SIZE` | 20 МБ | Максимальный размер загружаемого файла |
| Таймаут обработки | `processing_timeout_seconds` | `PROCESSING_TIMEOUT_SECONDS` | 300 с | Максимальное время обработки файла |
| Языки OCR | `ocr_languages` | `OCR_LANGUAGES` | `rus+eng` | Языки Tesseract через `+` |
| JavaScript | `enable_javascript` | `ENABLE_JAVASCRIPT` | `false` | JS-рендеринг через Playwright |
| Таймаут веб-запроса | `web_page_timeout` | `WEB_PAGE_TIMEOUT` | 30 с | Таймаут загрузки веб-страницы |
| Макс. изображений | `max_images_per_page` | `MAX_IMAGES_PER_PAGE` | 20 | Максимум изображений для OCR на странице |
| Ограничения ресурсов | `enable_resource_limits` | `ENABLE_RESOURCE_LIMITS` | `true` | Лимиты памяти для subprocess (Unix) |
| Вложенность архивов | `max_archive_nesting` | `MAX_ARCHIVE_NESTING` | 3 | Глубина вложенности архивов |
| Макс. распакованный | `max_extracted_size_mb` | `MAX_EXTRACTED_SIZE` | 100 МБ | Лимит распакованного содержимого |
| Лимит LibreOffice | `max_libreoffice_memory_mb` | `MAX_LIBREOFFICE_MEMORY` | 1.5 ГБ | Лимит памяти для конвертации DOC/PPT |
| Лимит Tesseract | `max_tesseract_memory_mb` | `MAX_TESSERACT_MEMORY` | 512 МБ | Лимит памяти для OCR |

## API Endpoints

Эндпоинты добавлены в `src/api/endpoints/rag.py` с префиксом `/api/v1/rag/`:

### `POST /api/v1/rag/extract/file`

Извлечение текста из загруженного файла.

**Request:** `multipart/form-data`, поле `file`

**Response:**
```json
{
  "success": true,
  "filename": "report.pdf",
  "count": 1,
  "total_chars": 8420,
  "files": [{"filename": "...", "path": "...", "size": 0, "type": "pdf", "text": "..."}]
}
```

### `POST /api/v1/rag/extract/url`

Извлечение текста с веб-страницы или файла по URL.

**Request body:**
```json
{
  "url": "https://example.com/page",
  "enable_javascript": false,
  "process_images": false,
  "web_page_timeout": 30
}
```

### `GET /api/v1/rag/extract/formats`

Возвращает словарь поддерживаемых форматов из `Settings.SUPPORTED_FORMATS`.

## Интеграция с RAG индексатором

Для использования TextExtractor при построении RAG индекса:

```python
from src.rag.text_extractors.text_extractor_4_rag import TextExtractor
from src.rag.indexer import RAGIndexer

extractor = TextExtractor()
indexer = RAGIndexer()

# Извлечь текст из файла
with open("manual.pdf", "rb") as f:
    results = extractor.extract_text(f.read(), "manual.pdf")

# Добавить в индекс
for result in results:
    if result["text"]:
        indexer.add_text(result["text"], metadata={"source": result["filename"]})
```

## Опциональные зависимости

Модуль работает с частично установленными зависимостями — недоступные форматы
просто не поддерживаются, остальные работают нормально.

| Зависимость | Форматы | Установка |
|---|---|---|
| `pdfplumber` | PDF | `pip install pdfplumber` |
| `python-docx` | DOCX, DOC | `pip install python-docx` |
| `pandas` | XLSX, XLS, CSV | `pip install pandas openpyxl` |
| `python-pptx` | PPTX, PPT | `pip install python-pptx` |
| `pytesseract` + Tesseract | Изображения OCR | `pip install pytesseract` + Tesseract |
| `beautifulsoup4` | HTML, EPUB | `pip install beautifulsoup4 lxml` |
| `odfpy` | ODT | `pip install odfpy` |
| `striprtf` | RTF | `pip install striprtf` |
| `PyYAML` | YAML | `pip install pyyaml` |
| `requests` | URL извлечение | `pip install requests` |
| `playwright` | JS-рендеринг | `pip install playwright && playwright install chromium` |
| `rarfile` | RAR архивы | `pip install rarfile` |
| `py7zr` | 7Z архивы | `pip install py7zr` |
| `python-magic` | MIME валидация | `pip install python-magic` |
| `faster-whisper` | MP3, WAV, M4A, OGG, FLAC, WEBM | `pip install faster-whisper` |

## Класс `WhisperExtractor`

Локальная транскрипция аудиофайлов через [faster-whisper](https://github.com/SYSTRAN/faster-whisper).
Работает полностью оффлайн — никаких облачных API не требуется.

```python
from src.rag.text_extractors.whisper import WhisperExtractor

extractor = WhisperExtractor(
    model_size="base",    # tiny | base | small | medium | large-v2 | large-v3
    device="cpu",         # cpu | cuda
    compute_type="int8",  # int8 (для CPU) | float16 (для GPU)
    language=None,        # None = автоопределение, "ru" / "en" = принудительно
)
```

Модель загружается лениво при первом вызове и кэшируется для последующих.
При первом запуске модель скачивается в `~/.cache/huggingface/hub`.

### Поддерживаемые форматы

`.mp3`, `.wav`, `.m4a`, `.ogg`, `.flac`, `.webm`

### Модели и требования к железу

| Модель | Размер | RAM | Рекомендация |
|---|---|---|---|
| `tiny` | 75 MB | ~1 GB | Быстрый прототип |
| `base` | 145 MB | ~1 GB | Баланс скорость/качество (**по умолчанию**) |
| `small` | 465 MB | ~2 GB | Хорошее качество |
| `medium` | 1.5 GB | ~5 GB | Высокое качество |
| `large-v3` | 3 GB | ~10 GB | Максимальное качество |

### Методы

#### `extract_from_file(file_path) -> dict`

```python
result = extractor.extract_from_file("interview.mp3")
# {
#   "text": "Полный текст транскрипции...",
#   "filename": "interview.mp3",
#   "language": "ru",
#   "segments": [
#     {"start": 0.0, "end": 3.5, "text": "Первый сегмент"},
#     ...
#   ]
# }
```

#### `extract_from_bytes(content, filename) -> dict`

```python
with open("lecture.wav", "rb") as f:
    result = extractor.extract_from_bytes(f.read(), "lecture.wav")
```

#### `is_supported(filename) -> bool`

```python
extractor.is_supported("audio.mp3")   # True
extractor.is_supported("report.pdf")  # False
```

### Интеграция с RAG индексатором

```python
from src.rag.text_extractors.whisper import WhisperExtractor
from src.rag.indexer import RAGIndexer

extractor = WhisperExtractor(model_size="small", language="ru")
indexer = RAGIndexer()

result = extractor.extract_from_file("meeting_recording.mp3")
if result["text"]:
    indexer.add_text(
        result["text"],
        metadata={"source": result["filename"], "language": result["language"]}
    )
```

!!! tip "Совет по выбору модели"
    Для русскоязычных записей рекомендуется `small` или `medium` — `base` на русском даёт заметно хуже.
    Укажите `language="ru"` явно, чтобы избежать ошибок автоопределения.

## Безопасность

### SSRF защита

`extract_from_url()` проверяет URL перед запросом:
- Блокирует `localhost`, `127.0.0.0/8`, `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`
- Блокирует metadata service `169.254.169.254`
- Блокирует Docker bridge gateway
- Настраивается через `BLOCKED_IP_RANGES` и `BLOCKED_HOSTNAMES`

### Zip Bomb защита

При обработке архивов:
- Проверяется суммарный размер распакованных файлов до извлечения
- Ограничение: `MAX_EXTRACTED_SIZE` (100 МБ по умолчанию)
- Ограничение глубины вложенности: `MAX_ARCHIVE_NESTING` (3)

### MIME валидация

Расширение файла проверяется на соответствие реальному содержимому через `python-magic`.
При несоответствии файл отклоняется.

## Ограничения на Windows

Модуль `resource` (Unix) недоступен на Windows — ограничения памяти для subprocess
автоматически отключаются. Функциональность извлечения текста при этом не затрагивается.

LibreOffice (для DOC/PPT конвертации) должен быть установлен отдельно.
