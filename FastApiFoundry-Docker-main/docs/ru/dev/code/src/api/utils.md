# Utils

**Файл:** `src/api/utils.py`  
**Тип:** `.py`

---

### `_send_telegram_alert` — Функция

```python
async def _send_telegram_alert(message: str)
```

Отправка уведомления в Telegram о критической задержке.

ОБОСНОВАНИЕ:
  Оперативное реагирование на деградацию производительности LLM-бэкенда.

### `api_response_handler` — Функция

```python
def api_response_handler(func)
```

Декоратор для автоматической инъекции статуса успеха и времени выполнения в JSON ответы.

### `wrapper` — Функция

```python
@wraps(func)
```


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
