# Test Translation Pipeline

**Файл:** `tests/unit/test_translation_pipeline.py`  
**Тип:** `.py`

---

### `TestShouldTranslate` — Класс

```python
class TestShouldTranslate
```

Tests for Translator.should_translate() priority logic.

### `TestResolveUserLang` — Класс

```python
class TestResolveUserLang
```

Tests for Translator.resolve_user_lang().

### `TestGenerateTranslationPipeline` — Класс

```python
class TestGenerateTranslationPipeline
```

Tests for translate_model_dialog in POST /api/v1/generate.

### `TestTranslatorMethods` — Класс

```python
class TestTranslatorMethods
```

Unit tests for translate_for_model and translate_response.

### `translator` — Функция

```python
@pytest.fixture
```

### `test_per_request_true_overrides_config` — Функция

```python
@pytest.mark.asyncio
```

translate_model_dialog=True activates translation regardless of config.

### `test_per_request_false_overrides_config` — Функция

```python
@pytest.mark.asyncio
```

translate_model_dialog=False disables translation regardless of config.

### `test_falls_back_to_config_enabled` — Функция

```python
@pytest.mark.asyncio
```

When translate_model_dialog absent, uses config translator.enabled=True.

### `test_falls_back_to_config_disabled` — Функция

```python
@pytest.mark.asyncio
```

When translate_model_dialog absent, uses config translator.enabled=False.

### `test_default_is_false_when_no_config` — Функция

```python
@pytest.mark.asyncio
```

Default is False when config section is missing.

### `translator` — Функция

```python
@pytest.fixture
```

### `test_explicit_lang_returned_as_is` — Функция

```python
@pytest.mark.asyncio
```

Explicit user_language is returned lowercased without detection.

### `test_auto_detect_called_when_no_lang` — Функция

```python
@pytest.mark.asyncio
```

detect_language is called when user_language is None.

### `test_fallback_to_en_on_detection_failure` — Функция

```python
@pytest.mark.asyncio
```

Falls back to 'en' when detection returns no language.

### `test_prompt_translated_to_en_before_model` — Функция

```python
@pytest.mark.asyncio
```

When translate_model_dialog=True, prompt is translated to EN before routing.

### `test_no_translation_when_flag_false` — Функция

```python
@pytest.mark.asyncio
```

When translate_model_dialog=False, prompt goes to model unchanged.

### `test_english_prompt_not_translated` — Функция

```python
@pytest.mark.asyncio
```

English prompt is passed through without translation even when flag=True.

### `test_missing_prompt_returns_error` — Функция

```python
@pytest.mark.asyncio
```

Empty prompt returns success=False without calling translator.

### `translator` — Функция

```python
@pytest.fixture
```

### `test_translate_for_model_skips_english` — Функция

```python
@pytest.mark.asyncio
```

translate_for_model returns original unchanged for source_lang='en'.

### `test_translate_response_skips_english_target` — Функция

```python
@pytest.mark.asyncio
```

translate_response returns original unchanged when target_lang='en'.

### `test_translate_for_model_calls_provider` — Функция

```python
@pytest.mark.asyncio
```

translate_for_model calls underlying translate() for non-English input.

### `test_translate_response_calls_provider` — Функция

```python
@pytest.mark.asyncio
```

translate_response calls underlying translate() for non-English target.


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
