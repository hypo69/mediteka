# Test Rag Agent

**Файл:** `tests/unit/test_rag_agent.py`  
**Тип:** `.py`

---

### `mock_rag_system` — Функция

```python
@pytest.fixture
```

Фикстура для мокирования синглтона rag_system.

### `test_rag_agent_rag_search_with_markdown_tables` — Функция

```python
@pytest.mark.asyncio
```

Тестирование инструмента rag_search RagAgent'а с контентом, симулирующим
вывод MarkItDown, включая таблицы.

### `test_rag_agent_generate_answer_tool` — Функция

```python
@pytest.mark.asyncio
```

Тестирование инструмента generate_answer RagAgent'а.

### `test_rag_agent_rag_search_no_index` — Функция

```python
@pytest.mark.asyncio
```

Тестирование rag_search, когда RAG-индекс не загружен.

### `test_rag_agent_rag_search_no_results` — Функция

```python
@pytest.mark.asyncio
```

Тестирование rag_search, когда релевантные фрагменты не найдены.


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
