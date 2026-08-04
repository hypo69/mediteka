# src/utils

Utility modules for FastAPI Foundry — config loading, logging helpers, and text translation.

## Files

| File | Description |
|---|---|
| `translator.py` | `Translator` class + `translator` singleton — free online translation |
| `env_processor.py` | `.env` loading, config validation |
| `foundry_finder.py` | Auto-discover Foundry Local port |
| `logging_config.py` | Logging setup helpers |
| `logging_system.py` | Structured logging system |
| `log_analyzer.py` | Log file analysis utilities |

## Translator

Translates **incoming** text to English before sending to an AI model, and **outgoing** responses back to the user's original language. Uses free online services — no API keys required by default.

### Providers

| ID | Service | Key required |
|---|---|---|
| `mymemory` | [MyMemory](https://mymemory.translated.net/) free API | No (500 words/day; set `MYMEMORY_EMAIL` for 50K) |
| `libretranslate` | [LibreTranslate](https://libretranslate.com/) public instances | No |
| `deepl` | DeepL free tier | `DEEPL_API_KEY` in `.env` |
| `google` | Google Cloud Translation | `GOOGLE_TRANSLATE_API_KEY` in `.env` |

### Usage

```python
from src.utils.translator import translator

# Translate user input → English for AI model
result = await translator.translate_for_model("Как дела?", source_lang="auto")
# result["translated"] == "How are you?"
# result["was_translated"] == True

# Translate AI response → user's language
result = await translator.translate_response("I am fine", target_lang="ru")
# result["translated"] == "Я в порядке"

# General translation
result = await translator.translate("Bonjour", source_lang="fr", target_lang="en")
# result["translated"] == "Hello"

# Detect language
result = await translator.detect_language("Привет мир")
# result["language"] == "ru"

# Batch
result = await translator.batch_translate(["Hello", "Goodbye"], target_lang="ru")
```

### Environment variables

```env
MYMEMORY_EMAIL=your@email.com        # Optional: raises MyMemory limit to 50K words/day
LIBRETRANSLATE_API_KEY=...           # Optional: for private LibreTranslate instances
DEEPL_API_KEY=...                    # Required only for deepl provider
GOOGLE_TRANSLATE_API_KEY=...         # Required only for google provider
```
