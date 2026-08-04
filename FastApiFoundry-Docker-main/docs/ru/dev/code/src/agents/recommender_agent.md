# Recommender Agent

**Файл:** `src/agents/recommender_agent.py`  
**Тип:** `.py`

---

### `record_page_view` — Функция

```python
def record_page_view(user_id: str, url: str, title: str, time_spent: int, timestamp: Optional[str]=None) -> None
```

Store a page view event for a user.

Args:
    user_id: Unique identifier for the browser session / user.
    url: Full URL of the visited page.
    title: Page title extracted by the extension.
    time_spent: Seconds the user spent on the page.
    timestamp: ISO-8601 timestamp; defaults to now.

### `get_page_views` — Функция

```python
def get_page_views(user_id: str, min_time: int=_MIN_TIME_SECONDS) -> List[Dict]
```

Return filtered page views for a user.

Args:
    user_id: User identifier.
    min_time: Minimum seconds on page to include.

Returns:
    List[Dict]: Filtered and sorted page view records.

### `RecommenderAgent` — Класс

```python
class RecommenderAgent(BaseAgent)
```

Персональный рекомендательный агент на основе истории просмотров.

Анализирует, какие страницы пользователь читал дольше всего,
определяет топики интересов и генерирует рекомендации.

Tools:
    analyze_interests: Извлекает топики из истории просмотров.
    generate_recommendations: Формирует список рекомендаций.

Example:
    >>> agent = RecommenderAgent(foundry_client)
    >>> result = await agent.run(
    ...     user_message=json.dumps({"user_id": "u1", "top_k": 5}),
    ...     model="foundry::qwen3-0.6b",
    ... )
    >>> print(result.answer)

### `tools` — Функция

```python
@property
```

### `_execute_tool` — Функция

```python
async def _execute_tool(self, name: str, arguments: Dict[str, Any]) -> str
```

Execute a recommender tool.

Args:
    name: Tool name ('analyze_interests' or 'generate_recommendations').
    arguments: Tool arguments dict.

Returns:
    str: JSON-encoded tool result.

### `_analyze_interests` — Функция

```python
def _analyze_interests(self, args: Dict) -> str
```

Extract interest topics from page view history.

Args:
    args: Dict with user_id (str) and optional top_n (int).

Returns:
    str: JSON with interests list and page view summary.

### `_generate_recommendations` — Функция

```python
def _generate_recommendations(self, args: Dict) -> str
```

Format interests for the AI recommendation step.

Args:
    args: Dict with interests (list) and optional top_k (int).

Returns:
    str: JSON with interests and requested count.


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
