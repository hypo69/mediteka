# Config

**Файл:** `src/api/endpoints/config.py`  
**Тип:** `.py`

---

### `get_config` — Функция

```python
@router.get('/config')
```

Получить конфигурацию для веб-интерфейса

### `ConfigUpdateRequest` — Класс

```python
class ConfigUpdateRequest(BaseModel)
```

### `patch_config` — Функция

```python
@router.patch('/config')
```

Частичное обновление конфигурации. Поддерживает dot-notation: 'foundry_ai.default_model'

### `save_config` — Функция

```python
@router.post('/config')
```

Сохранить конфигурацию

### `_read_env_file` — Функция

```python
def _read_env_file(path: str) -> Dict[str, str]
```

Читает .env файл и возвращает словарь ключ-значение (без комментариев)

### `_write_env_file` — Функция

```python
def _write_env_file(path: str, data: Dict[str, str]) -> None
```

Записывает словарь обратно в .env файл

### `_read_json_file` — Функция

```python
def _read_json_file(path: str) -> Optional[Dict[str, Any]]
```

Читает JSON файл, возвращает None если не существует

### `_read_text_file` — Функция

```python
def _read_text_file(path: str) -> Optional[str]
```

Читает текстовый файл, возвращает None если не существует

### `RawContentRequest` — Класс

```python
class RawContentRequest(BaseModel)
```

### `get_env_raw` — Функция

```python
@router.get('/config/env-raw')
```

Чтение .env файла как сырой текст для редактора

### `save_env_raw` — Функция

```python
@router.post('/config/env-raw')
```

Запись .env файла из редактора (сырой текст)

### `get_config_raw` — Функция

```python
@router.get('/config/raw')
```

Чтение config.json как сырой текст для редактора

### `save_config_raw` — Функция

```python
@router.post('/config/raw')
```

Запись config.json из редактора (сырой текст).
Валидация JSON на стороне клиента, но проверяем и здесь.

### `EnvUpdateRequest` — Класс

```python
class EnvUpdateRequest(BaseModel)
```

### `save_env_variable` — Функция

```python
@router.post('/config/env')
```

Сохранение одной переменной окружения в .env файл.

Используется для сохранения секретов (токены, ключи) из веб-интерфейса.
Переменная обновляется если существует, добавляется если нет.

### `export_config` — Функция

```python
@router.get('/config/export')
```

Экспорт ВСЕХ настроек проекта в один JSON: config.json + .env + MCP конфиги

### `get_provider_keys` — Функция

```python
@router.get('/config/provider-keys')
```

Читает ключи провайдеров из .env. Возвращает замаскированные значения.

### `ProviderKeysRequest` — Класс

```python
class ProviderKeysRequest(BaseModel)
```

### `save_provider_keys` — Функция

```python
@router.post('/config/provider-keys')
```

Сохраняет ключи провайдеров в .env.

### `ExtensionSyncRequest` — Класс

```python
class ExtensionSyncRequest(BaseModel)
```

### `extension_export` — Функция

```python
@router.get('/config/extension-export')
```

Экспортирует ключи провайдеров в формат расширения (chrome.storage.sync).

### `extension_import` — Функция

```python
@router.post('/config/extension-import')
```

Импортирует ключи из формата расширения (v1/v2) в .env.
providerKeys может содержать строки (app) или массивы (extension).
Неизвестные поля (summaryLang, providerModels и т.д.) игнорируются.

### `get_provider_models` — Функция

```python
@router.get('/config/provider-models/{provider}')
```

Proxy: fetch model list from external provider API server-side to avoid CORS.

### `ConfigImportRequest` — Класс

```python
class ConfigImportRequest(BaseModel)
```

### `import_config` — Функция

```python
@router.post('/config/import')
```

Импорт полного бэкапа настроек. merge=True — слияние, False — полная замена


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
