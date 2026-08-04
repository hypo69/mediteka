# Translator

**Файл:** `src/utils/translator.py`  
**Тип:** `.py`

---

### `_cfg` — Функция

```python
def _cfg() -> dict
```

Return translator section from config.json (lazy import to avoid circular deps).

### `Translator` — Класс

```python
class Translator
```

Translate text using configurable online services.

All provider URLs, keys and defaults are read from config.json
section "translator" at call time — no restart required after settings change.

### `__init__` — Функция

```python
def __init__(self) -> None
```

### `_timeout` — Функция

```python
def _timeout(self) -> aiohttp.ClientTimeout
```

### `_get_session` — Функция

```python
async def _get_session(self) -> aiohttp.ClientSession
```

### `close` — Функция

```python
async def close(self) -> None
```

### `should_translate` — Функция

```python
async def should_translate(self, request: dict) -> bool
```

Determine whether translation is active for this request.

Per-request field ``translate_model_dialog`` takes priority over global
config ``translator.enabled``. Default when neither is set: False.

Args:
    request: Raw request dict from the API endpoint.

Returns:
    bool: True if translation pipeline should run for this request.

Example:
    >>> translator.should_translate({"translate_model_dialog": True})
    True
    >>> translator.should_translate({})  # falls back to config
    False

### `resolve_user_lang` — Функция

```python
async def resolve_user_lang(self, prompt: str, user_language: str | None) -> str
```

Return user language code, auto-detecting from prompt when not provided.

Args:
    prompt: User input text used for detection.
    user_language: Explicit ISO 639-1 code or None for auto-detect.

Returns:
    str: ISO 639-1 language code, e.g. 'ru', 'en', 'he'.

Example:
    >>> await translator.resolve_user_lang("Привет", None)
    'ru'

### `translate` — Функция

```python
async def translate(self, text: str, *, provider: str='', source_lang: str='auto', target_lang: str='en', api_key: str='') -> dict
```

Translate text to target language.

Args:
    text: Source text.
    provider: Override provider. Empty = use config default_provider.
    source_lang: ISO 639-1 code or "auto".
    target_lang: ISO 639-1 code.
    api_key: Optional key override for deepl/google/libretranslate.

Returns:
    dict: success, translated, provider, source_lang, target_lang,
          elapsed_ms, error.

### `translate_for_model` — Функция

```python
async def translate_for_model(self, text: str, *, provider: str='', source_lang: str='auto', api_key: str='') -> dict
```

Translate text to English for AI model input.

Returns original unchanged if source_lang is already 'en'.

Args:
    text: Source text to translate.
    provider: Override provider. Empty = use config default_provider.
    source_lang: ISO 639-1 code or "auto".
    api_key: Optional key override for deepl/google/libretranslate.

Returns:
    dict: success, translated, original, was_translated, provider,
          source_lang, target_lang, elapsed_ms, error.

### `translate_response` — Функция

```python
async def translate_response(self, text: str, target_lang: str, *, provider: str='', api_key: str='') -> dict
```

Translate AI response back to the user's original language.

Args:
    text: English text from AI model.
    target_lang: User's original language code.
    provider: Override provider. Empty = use config default_provider.
    api_key: Optional key override.

Returns:
    dict: same structure as translate().

### `detect_language` — Функция

```python
async def detect_language(self, text: str) -> dict
```

Detect language using MyMemory (free, no key required).

Returns:
    dict: success, language (ISO 639-1), language_name, error.

### `batch_translate` — Функция

```python
async def batch_translate(self, texts: list[str], *, provider: str='', source_lang: str='auto', target_lang: str='en', api_key: str='') -> dict
```

Translate a list of texts.

Args:
    texts: List of source strings to translate.
    provider: Override provider. Empty = use config default_provider.
    source_lang: ISO 639-1 code or "auto".
    target_lang: ISO 639-1 target language code.
    api_key: Optional key override for deepl/google/libretranslate.

Returns:
    dict: success, results (list of translate() dicts), total, failed, elapsed_ms.

### `_via_mymemory` — Функция

```python
async def _via_mymemory(self, text: str, source_lang: str, target_lang: str) -> str
```

MyMemory free API — 500 words/day anonymous; set mymemory_email for 50K/day.

Args:
    text: Source text.
    source_lang: ISO 639-1 code or "auto".
    target_lang: ISO 639-1 target language code.

Returns:
    str: Translated text.

Raises:
    RuntimeError: On non-200 HTTP response or API error status.

### `_via_libretranslate` — Функция

```python
async def _via_libretranslate(self, text: str, source_lang: str, target_lang: str, api_key: str) -> str
```

LibreTranslate — primary and fallback URLs from config.

Args:
    text: Source text.
    source_lang: ISO 639-1 code or "auto".
    target_lang: ISO 639-1 target language code.
    api_key: Optional API key for the LibreTranslate instance.

Returns:
    str: Translated text.

Raises:
    RuntimeError: If all configured hosts are unavailable.

### `_via_deepl` — Функция

```python
async def _via_deepl(self, text: str, target_lang: str, api_key: str) -> str
```

Translate via DeepL free tier API.

Args:
    text: Source text.
    target_lang: ISO 639-1 target language code.
    api_key: DeepL API key (overrides DEEPL_API_KEY env var).

Returns:
    str: Translated text.

Raises:
    ValueError: If no API key is available.
    RuntimeError: On non-200 HTTP response.

### `_via_google` — Функция

```python
async def _via_google(self, text: str, source_lang: str, target_lang: str, api_key: str) -> str
```

Translate via Google Cloud Translation API.

Args:
    text: Source text.
    source_lang: ISO 639-1 code or "auto".
    target_lang: ISO 639-1 target language code.
    api_key: Google Cloud API key (overrides GOOGLE_TRANSLATE_API_KEY env var).

Returns:
    str: Translated text.

Raises:
    ValueError: If no API key is available.
    RuntimeError: On non-200 HTTP response.

### `_err` — Функция

```python
@staticmethod
```

Build a standard error response dict.

Args:
    msg: Error message.
    provider: Provider name that caused the error.

Returns:
    dict: success=False with all standard fields set to None/0.


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
