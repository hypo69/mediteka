# text_extractor_4_rag

Мульти-форматный экстрактор текста. Поддерживает 40+ форматов файлов.

## Поддерживаемые форматы

| Группа | Форматы |
|---|---|
| Документы | PDF, DOCX, DOC, ODT, RTF |
| Таблицы | XLSX, XLS, CSV, ODS |
| Презентации | PPTX, PPT |
| Изображения (OCR) | JPG, PNG, TIFF, BMP, GIF, WEBP |
| Веб | HTML, HTM, EPUB |
| Данные | JSON, XML, YAML, YML |
| Архивы | ZIP, RAR, 7Z, TAR, GZ, BZ2, XZ |
| Текст | TXT, MD, RST |
| Исходный код | PY, JS, TS, PHP, GO, RS, CS, JAVA, и др. |
| Аудио | MP3, WAV, M4A, OGG, FLAC, WEBM (через faster-whisper) |

## Использование

```python
from src.rag.text_extractors.text_extractor_4_rag import TextExtractor

extractor = TextExtractor()

# Из байтов
with open("document.pdf", "rb") as f:
    results = extractor.extract_text(f.read(), "document.pdf")
# [{"filename": "document.pdf", "path": "document.pdf", "size": 204800, "type": "pdf", "text": "..."}]

# С URL
results = extractor.extract_from_url("https://example.com/doc.pdf")
```

## Настройки

```python
from src.rag.text_extractors.text_extractor_4_rag.config import settings

print(settings.MAX_FILE_SIZE)       # 20971520 (20 MB)
print(settings.OCR_LANGUAGES)       # "rus+eng"
print(settings.ENABLE_JAVASCRIPT)   # False
```

Все значения читаются из `config.json` → `text_extractor`. См. [README родительского пакета](../README.md).

## Файлы

| Файл | Назначение |
|---|---|
| `config.py` | Класс `Settings` — все настройки через Config singleton |
| `extractors.py` | Класс `TextExtractor` — основная логика |
| `utils.py` | Вспомогательные функции (sanitize, validate, cleanup) |
| `main.py` | Standalone FastAPI приложение (микросервис) |
