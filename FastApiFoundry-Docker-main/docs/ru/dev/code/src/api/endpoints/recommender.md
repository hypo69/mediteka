# Recommender

**Файл:** `src/api/endpoints/recommender.py`  
**Тип:** `.py`

---

### `_get_agent` — Функция

```python
def _get_agent() -> RecommenderAgent
```

### `PageViewEvent` — Класс

```python
class PageViewEvent(BaseModel)
```

### `RecommendRequest` — Класс

```python
class RecommendRequest(BaseModel)
```

### `track_page_view` — Функция

```python
@router.post('/recommender/track')
```

Record a page view event from the browser extension.

Args:
    event: PageViewEvent with user_id, url, title, time_spent, timestamp.

Returns:
    dict: success status and total views count for the user.

### `get_recommendations` — Функция

```python
@router.post('/recommender/recommendations')
```

Generate AI-powered recommendations based on browsing history.

Args:
    request: RecommendRequest with user_id, optional model, top_k.

Returns:
    dict: success, answer (recommendations text), tool_calls log.

### `get_history` — Функция

```python
@router.get('/recommender/history')
```

Return filtered browsing history for a user.

Args:
    user_id: User identifier.
    min_time: Minimum seconds on page to include (default 10).

Returns:
    dict: success, user_id, views list, count.


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
