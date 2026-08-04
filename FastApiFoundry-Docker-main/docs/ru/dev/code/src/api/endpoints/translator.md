# Translator

**Файл:** `src/api/endpoints/translator.py`  
**Тип:** `.py`

---

### `translate_text` — Функция

```python
@router.post('/translate')
```

Translate text using the configured provider.

Args:
    request: JSON body with fields:
        text (str):          Source text (required).
        source_lang (str):   ISO 639-1 code or 'auto' (default: 'auto').
        target_lang (str):   ISO 639-1 target code (default: 'en').
        provider (str):      Override provider (default: from config).
        api_key (str):       Optional API key override.

Returns:
    dict: success, translated, provider, source_lang, target_lang,
          elapsed_ms, error.

### `detect_language` — Функция

```python
@router.post('/translate/detect')
```

Detect language of the given text.

Args:
    request: JSON body with fields:
        text (str): Text to detect language for (required).

Returns:
    dict: success, language (ISO 639-1), language_name, error.

### `get_translator_config` — Функция

```python
@router.get('/translate/config')
```

Return current translator configuration (no secrets).

Returns:
    dict: enabled, default_provider, available_providers.


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
