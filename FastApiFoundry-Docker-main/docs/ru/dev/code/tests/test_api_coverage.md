# Test Api Coverage

**Файл:** `tests/test_api_coverage.py`  
**Тип:** `.py`

---

### `pytest_addoption` — Функция

```python
def pytest_addoption(parser)
```

### `base_url` — Функция

```python
@pytest.fixture(scope='session')
```

### `model` — Функция

```python
@pytest.fixture(scope='session')
```

Auto-detect first working model from /api/v1/models.

### `session_id` — Функция

```python
@pytest.fixture(scope='session')
```

Create a chat session for session-dependent tests.

### `get` — Функция

```python
def get(base_url, path, timeout=15)
```

### `post` — Функция

```python
def post(base_url, path, body, timeout=15)
```

### `patch` — Функция

```python
def patch(base_url, path, body, timeout=15)
```

### `delete` — Функция

```python
def delete(base_url, path, timeout=15)
```

### `test_health` — Функция

```python
def test_health(base_url)
```

### `test_system_stats` — Функция

```python
def test_system_stats(base_url)
```

### `test_models` — Функция

```python
def test_models(base_url)
```

### `test_models_connected` — Функция

```python
def test_models_connected(base_url)
```

### `test_ai_models` — Функция

```python
def test_ai_models(base_url)
```

### `test_ai_models_recommended` — Функция

```python
def test_ai_models_recommended(base_url)
```

### `test_ai_health` — Функция

```python
def test_ai_health(base_url)
```

### `test_foundry_status` — Функция

```python
def test_foundry_status(base_url)
```

### `test_foundry_models_list` — Функция

```python
def test_foundry_models_list(base_url)
```

### `test_generate_all_fields` — Функция

```python
def test_generate_all_fields(base_url, model)
```

### `test_generate_with_rag` — Функция

```python
def test_generate_with_rag(base_url, model)
```

### `test_ai_generate_all_fields` — Функция

```python
def test_ai_generate_all_fields(base_url, model)
```

### `test_ai_chat_all_fields` — Функция

```python
def test_ai_chat_all_fields(base_url, model)
```

### `test_ai_optimize` — Функция

```python
def test_ai_optimize(base_url)
```

### `test_chat_start` — Функция

```python
def test_chat_start(base_url, model)
```

### `test_chat_message` — Функция

```python
def test_chat_message(base_url, model, session_id)
```

### `test_chat_history_get` — Функция

```python
def test_chat_history_get(base_url, session_id)
```

### `test_chat_models` — Функция

```python
def test_chat_models(base_url)
```

### `test_chat_history_list` — Функция

```python
def test_chat_history_list(base_url)
```

### `test_chat_history_save` — Функция

```python
def test_chat_history_save(base_url, model, session_id)
```

### `test_chat_history_cleanup` — Функция

```python
def test_chat_history_cleanup(base_url)
```

### `test_chat_session_delete` — Функция

```python
def test_chat_session_delete(base_url, session_id)
```

### `test_rag_status` — Функция

```python
def test_rag_status(base_url)
```

### `test_rag_dirs` — Функция

```python
def test_rag_dirs(base_url)
```

### `test_rag_cwd` — Функция

```python
def test_rag_cwd(base_url)
```

### `test_rag_profiles` — Функция

```python
def test_rag_profiles(base_url)
```

### `test_rag_browse` — Функция

```python
def test_rag_browse(base_url)
```

### `test_rag_search` — Функция

```python
def test_rag_search(base_url)
```

### `test_rag_extract_formats` — Функция

```python
def test_rag_extract_formats(base_url)
```

### `test_rag_documents_list` — Функция

```python
def test_rag_documents_list(base_url)
```

### `test_rag_documents_stats` — Функция

```python
def test_rag_documents_stats(base_url)
```

### `test_config_get` — Функция

```python
def test_config_get(base_url)
```

### `test_config_raw_get` — Функция

```python
def test_config_raw_get(base_url)
```

### `test_config_env_raw_get` — Функция

```python
def test_config_env_raw_get(base_url)
```

### `test_config_export` — Функция

```python
def test_config_export(base_url)
```

### `test_config_provider_keys` — Функция

```python
def test_config_provider_keys(base_url)
```

### `test_config_extension_export` — Функция

```python
def test_config_extension_export(base_url)
```

### `test_config_patch_noop` — Функция

```python
def test_config_patch_noop(base_url)
```

### `test_translator_config` — Функция

```python
def test_translator_config(base_url)
```

### `test_translate_detect` — Функция

```python
def test_translate_detect(base_url)
```

### `test_translate_text` — Функция

```python
def test_translate_text(base_url)
```

### `test_logs_get` — Функция

```python
def test_logs_get(base_url)
```

### `test_hf_status` — Функция

```python
def test_hf_status(base_url)
```

### `test_hf_models` — Функция

```python
def test_hf_models(base_url)
```

### `test_llama_status` — Функция

```python
def test_llama_status(base_url)
```

### `test_llama_models` — Функция

```python
def test_llama_models(base_url)
```

### `test_ollama_status` — Функция

```python
def test_ollama_status(base_url)
```

### `test_ollama_models` — Функция

```python
def test_ollama_models(base_url)
```


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
