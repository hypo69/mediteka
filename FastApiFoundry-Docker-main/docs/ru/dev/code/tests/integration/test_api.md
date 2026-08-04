# Test Api

**Файл:** `tests/integration/test_api.py`  
**Тип:** `.py`

---

### `test_api_info_endpoint` — Функция

```python
@pytest.mark.asyncio
```

Проверка эндпоинта основной информации об API.

### `test_api_v1_health` — Функция

```python
@pytest.mark.asyncio
```

Проверка работоспособности системы (Health Check).

### `test_api_v1_models_list` — Функция

```python
@pytest.mark.asyncio
```

Проверка получения списка доступных моделей.

### `test_api_docs_availability` — Функция

```python
@pytest.mark.asyncio
```

Проверка доступности Swagger UI и Redoc.

### `test_api_v1_generate_mocked` — Функция

```python
@pytest.mark.asyncio
```

Тестирование генерации с моком бэкенда LLM.

Используется respx для перехвата запросов к Foundry/llama.cpp 
внутри тестового окружения.

### `test_api_v1_404_not_found` — Функция

```python
@pytest.mark.asyncio
```

Проверка обработки запроса к несуществующему ресурсу.

ПОЧЕМУ ЭТО ВАЖНО:
    Гарантия того, что сервер возвращает стандартный код 404 и 
    структурированное описание ошибки вместо падения или возврата HTML.

### `test_api_v1_422_validation_error` — Функция

```python
@pytest.mark.asyncio
```

Проверка валидации входящих данных (отсутствие обязательных полей).

ПОЧЕМУ ЭТО ВАЖНО:
    Проверка корректности работы Pydantic-схем. Запрос на генерацию 
    без поля 'prompt' должен быть отклонен на уровне валидации.

### `test_api_v1_401_unauthorized_mocked` — Функция

```python
@pytest.mark.asyncio
```

Имитация ситуации отсутствия авторизации при защищенном доступе.

ПОЧЕМУ ЭТО ВАЖНО:
    Проверка готовности тестовой среды к обработке кодов безопасности.

### `test_api_v1_504_timeout_mocked` — Функция

```python
@pytest.mark.asyncio
```

Проверка обработки таймаута (504 Gateway Timeout).

ПОЧЕМУ ЭТО ВАЖНО:
    Проверка реакции API сервера на задержки или "зависания" 
    внутренних бэкендов (Foundry/llama.cpp).

### `test_api_v1_generate_stream_mocked` — Функция

```python
@pytest.mark.asyncio
```

Проверка корректности формирования SSE при потоковой генерации.
    
    ПОЧЕМУ ЭТО ВАЖНО:
        Интерфейсы чатов требуют немедленного отображения токенов. 
        Тест проверяет соблюдение протокола SSE (data: ...

).

### `stream_generator` — Функция

```python
async def stream_generator()
```


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
