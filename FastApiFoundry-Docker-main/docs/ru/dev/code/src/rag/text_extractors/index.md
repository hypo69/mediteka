# text_extractors

Пакет экстракторов текста для RAG-пайплайна.

Каждый бэкенд — отдельный подпакет с единым интерфейсом.

## Структура

```
text_extractors/
├── text_extractor_4_rag/   # Мульти-форматный экстрактор (40+ форматов)
├── markitdown/             # Microsoft MarkItDown (Markdown-ориентированный)
└── whisper/                # Локальная транскрипция аудио (faster-whisper)
```

## Быстрый старт

```python
# Мульти-форматный экстрактор
from src.rag.text_extractors.text_extractor_4_rag import TextExtractor

extractor = TextExtractor()
with open("document.pdf", "rb") as f:
    results = extractor.extract_text(f.read(), "document.pdf")

# MarkItDown
from src.rag.text_extractors.markitdown import MarkItDownExtractor

md = MarkItDownExtractor()
result = md.extract_from_file("report.docx")
print(result["text"])
```

## Настройки

Все настройки берутся из `config.json` → секция `text_extractor` через синглтон `config`.

```json
{
  "text_extractor": {
    "max_file_size_mb": 20,
    "processing_timeout_seconds": 300,
    "ocr_languages": "rus+eng",
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

Приоритет: `env var` > `config.json` > встроенный default.

## API эндпоинты

| Метод | Путь | Описание |
|---|---|---|
| `POST` | `/v1/rag/extract/file` | Извлечь текст из файла |
| `POST` | `/v1/rag/extract/url` | Извлечь текст с URL |
| `GET` | `/v1/rag/extract/formats` | Список поддерживаемых форматов |
