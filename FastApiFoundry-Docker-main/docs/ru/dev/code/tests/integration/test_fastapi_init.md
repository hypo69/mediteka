# Test Fastapi Init

**Файл:** `tests/integration/test_fastapi_init.py`  
**Тип:** `.py`

---

### `temp_config` — Функция

```python
@pytest.fixture
```

Создание временного файла конфигурации для теста.

### `test_config_loading_logic` — Функция

```python
def test_config_loading_logic(temp_config)
```

Проверка логики чтения параметров из JSON.

### `test_env_substitution_in_config` — Функция

```python
def test_env_substitution_in_config(tmp_path)
```

Проверка подстановки переменных окружения в конфиг.

### `test_fastapi_app_initialization` — Функция

```python
@pytest.mark.asyncio
```

Проверка базовой готовности объекта FastAPI.

### `process_val` — Функция

```python
def process_val(val)
```


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
