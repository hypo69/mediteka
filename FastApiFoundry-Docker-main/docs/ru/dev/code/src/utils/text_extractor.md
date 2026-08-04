# Text Extractor

**Файл:** `src/utils/text_extractor.py`  
**Тип:** `.py`

---

### `TextExtractor` — Класс

```python
class TextExtractor
```

!
Кастомный экстрактор для специфических задач: OCR и Web-scraping с JS.

### `__init__` — Функция

```python
def __init__(self, settings: dict=None)
```

### `extract_from_file` — Функция

```python
async def extract_from_file(self, file_path: str) -> str
```

Извлечение текста с поддержкой OCR для изображений.

### `extract_from_url` — Функция

```python
async def extract_from_url(self, url: str) -> str
```

Извлечение контента из URL с поддержкой JavaScript.

### `extract_text_from_image` — Функция

```python
async def extract_text_from_image(self, image_path: str) -> str
```

Public OCR API for callers that already extracted an image file.

### `_run_ocr` — Функция

```python
async def _run_ocr(self, image_path: str) -> str
```

Выполнение оптического распознавания символов.

### `_extract_with_playwright` — Функция

```python
async def _extract_with_playwright(self, url: str) -> str
```

Рендеринг страницы через Playwright.

### `_extract_simple_html` — Функция

```python
async def _extract_simple_html(self, url: str) -> str
```

Простой захват HTML (без JS).

### `_run_ocr_on_pdf` — Функция

```python
async def _run_ocr_on_pdf(self, pdf_path: str) -> str
```

Выполнение OCR на PDF-файле, постранично.


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
