# Main

**Файл:** `src/rag/text_extractors/text_extractor_4_rag/main.py`  
**Тип:** `.py`

---

### `Base64FileRequest` — Класс

```python
class Base64FileRequest(BaseModel)
```

Модель для запроса обработки base64-файла.

### `ExtractionOptions` — Класс

```python
class ExtractionOptions(BaseModel)
```

Настройки извлечения текста для веб-страниц (новое в v1.10.2).

### `URLRequest` — Класс

```python
class URLRequest(BaseModel)
```

Модель для запроса обработки веб-страницы (обновлено в v1.10.2).

### `lifespan` — Функция

```python
@asynccontextmanager
```

Lifecycle manager для FastAPI приложения.

### `logging_middleware` — Функция

```python
@app.middleware('http')
```

Middleware для логирования запросов.

### `root` — Функция

```python
@app.get('/')
```

Информация о API.

### `health` — Функция

```python
@app.get('/health')
```

Проверка состояния API.

### `supported_formats` — Функция

```python
@app.get('/v1/supported-formats')
```

Поддерживаемые форматы файлов.

### `extract_text` — Функция

```python
@app.post('/v1/extract/file')
```

Извлечение текста из файла.

### `extract_text_base64` — Функция

```python
@app.post('/v1/extract/base64')
```

Извлечение текста из base64-файла.

### `extract_text_from_url` — Функция

```python
@app.post('/v1/extract/url')
```

Извлечение текста с веб-страницы (обновлено в v1.10.2).


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
