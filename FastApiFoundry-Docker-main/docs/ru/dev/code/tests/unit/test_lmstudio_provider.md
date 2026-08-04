# Test Lmstudio Provider

**Файл:** `tests/unit/test_lmstudio_provider.py`  
**Тип:** `.py`

---

### `test_detect_backend_lmstudio_prefix` — Функция

```python
def test_detect_backend_lmstudio_prefix()
```

### `test_detect_backend_existing_prefixes_still_work` — Функция

```python
@pytest.mark.parametrize(('model', 'expected'), [('foundry::qwen3', ('foundry', 'qwen3')), ('hf::Qwen/Qwen2.5', ('hf', 'Qwen/Qwen2.5')), ('llama::D:/models/model.gguf', ('llama', 'D:/models/model.gguf')), ('ollama::mistral', ('ollama', 'mistral'))])
```

### `test_extract_message_content_joins_message_outputs_only` — Функция

```python
def test_extract_message_content_joins_message_outputs_only()
```

### `test_lmstudio_client_list_models` — Функция

```python
@pytest.mark.asyncio
```

### `test_lmstudio_client_model_management` — Функция

```python
@pytest.mark.asyncio
```

### `test_lmstudio_client_generate_parses_native_chat` — Функция

```python
@pytest.mark.asyncio
```

### `test_lmstudio_client_http_error_returns_failure` — Функция

```python
@pytest.mark.asyncio
```

### `test_route_generate_dispatches_to_lmstudio` — Функция

```python
@pytest.mark.asyncio
```

### `test_lmstudio_generate_endpoint` — Функция

```python
@pytest.mark.asyncio
```

### `test_lmstudio_models_endpoint` — Функция

```python
@pytest.mark.asyncio
```

### `fake_request` — Функция

```python
async def fake_request(method, path, **kwargs)
```

### `fake_request` — Функция

```python
async def fake_request(method, path, **kwargs)
```

### `fake_request` — Функция

```python
async def fake_request(method, path, **kwargs)
```

### `fake_request` — Функция

```python
async def fake_request(method, path, **kwargs)
```

### `fake_generate_lmstudio` — Функция

```python
async def fake_generate_lmstudio(prompt, model, temperature, max_tokens)
```

### `fake_generate` — Функция

```python
async def fake_generate(**kwargs)
```

### `fake_list_models` — Функция

```python
async def fake_list_models()
```


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
