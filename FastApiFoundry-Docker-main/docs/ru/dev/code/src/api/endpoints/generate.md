# Generate

**Файл:** `src/api/endpoints/generate.py`  
**Тип:** `.py`

---

### `generate_text` — Функция

```python
@router.post('/generate')
```

Generate text via the AI Assistant orchestrator.

Routes to the correct backend based on model prefix:
foundry:: / hf:: / llama:: / ollama:: / lmstudio::

Args:
    request: JSON body with fields:
        prompt (str):                 Input text (required).
        model (str):                  Model ID with prefix, e.g. 'foundry::qwen3-0.6b'.
        temperature (float):          Generation temperature (default: 0.7).
        max_tokens (int):             Max tokens (default: 1000).
        use_rag (bool):               Inject RAG context (default: False).
        top_k (int):                  RAG results count (default: from config).
        translate_model_dialog (bool): Translate prompt→EN and response→user lang.
        user_language (str|null):     User language ISO 639-1. null = auto-detect.

Returns:
    dict: success, content, model, usage, user_language, translated (bool)


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
