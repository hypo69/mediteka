# Foundry Management

**Файл:** `src/api/endpoints/foundry_management.py`  
**Тип:** `.py`

---

### `FoundryStatus` — Класс

```python
class FoundryStatus(BaseModel)
```

### `_poll_foundry_status_task` — Функция

```python
async def _poll_foundry_status_task(max_attempts: int=12, interval: int=5)
```

Фоновая задача для периодического опроса статуса Foundry после запуска.

Обоснование:
  - Уведомление в логах о фактической готовности сервиса.
  - Предоставление актуальной информации без необходимости ручного обновления.

### `get_foundry_status` — Функция

```python
@router.get('/status', response_model=FoundryStatus)
```

Получение статуса службы Foundry через системный агент.

Returns:
    FoundryStatus: Объект со статусом работы, портом и URL.

### `start_foundry` — Функция

```python
@router.post('/start')
```

Запуск службы Foundry через системный агент.

Args:
    background_tasks (BackgroundTasks): Фоновые задачи FastAPI.

Returns:
    dict: Статус выполнения и сообщение.

### `stop_foundry` — Функция

```python
@router.post('/stop')
```

Остановка службы Foundry через системный агент.

Returns:
    dict: Сообщение о результате операции.

### `reset_foundry_breaker` — Функция

```python
@router.post('/reset-breaker')
```

Ручной сброс предохранителя для команд Foundry.


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
