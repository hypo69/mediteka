# markitdown

Экстрактор текста на основе [Microsoft MarkItDown](https://github.com/microsoft/markitdown).

Конвертирует файлы и URL в Markdown с сохранением структуры документа:
заголовки, списки, таблицы, ссылки.

## Установка

```bash
pip install 'markitdown[all]'
```

## Поддерживаемые форматы

PDF, DOCX, PPTX, XLSX, HTML, CSV, JSON, XML, ZIP, изображения (OCR/EXIF),
аудио (транскрипция), YouTube URL, EPub и другие.

## Использование

```python
from src.rag.text_extractors.markitdown import MarkItDownExtractor

extractor = MarkItDownExtractor()

# Из файла
result = extractor.extract_from_file("report.docx")
print(result["text"])   # Markdown-текст

# Из байтов
with open("data.xlsx", "rb") as f:
    result = extractor.extract_from_bytes(f.read(), "data.xlsx")

# С URL (веб-страница, YouTube, удалённый файл)
result = extractor.extract_from_url("https://example.com/page")

# Из потока
with open("doc.pdf", "rb") as f:
    result = extractor.extract_from_stream(f, "doc.pdf")
```

## С LLM для описания изображений

```python
from openai import OpenAI

extractor = MarkItDownExtractor(
    llm_client=OpenAI(),
    llm_model="gpt-4o",
)
result = extractor.extract_from_file("presentation.pptx")
```

## С Azure Document Intelligence

```python
extractor = MarkItDownExtractor(
    docintel_endpoint="https://<resource>.cognitiveservices.azure.com/"
)
result = extractor.extract_from_file("scanned.pdf")
```

## Формат результата

```python
{
    "text": "# Заголовок\n\nТекст документа...",
    "filename": "report.docx"   # или "url" для URL-источников
}
```

## Отличие от text_extractor_4_rag

| | text_extractor_4_rag | markitdown |
|---|---|---|
| Фокус | Максимум форматов, чистый текст | Markdown с сохранением структуры |
| OCR | Tesseract | Встроенный / LLM Vision |
| Архивы | ZIP, RAR, 7Z, TAR | ZIP |
| Аудио | faster-whisper | Встроенная транскрипция |
| YouTube | ✗ | ✓ |
| Результат | `List[Dict]` | `Dict` |
