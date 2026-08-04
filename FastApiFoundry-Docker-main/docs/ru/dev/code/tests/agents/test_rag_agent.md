# Test Rag Agent

**Файл:** `tests/agents/test_rag_agent.py`  
**Тип:** `.py`

---

### `TestRagAgent` — Класс

```python
class TestRagAgent
```

Unit tests for RAG agent with mocked FAISS search.

### `test_context_injection` — Функция

```python
def test_context_injection(self, mocker)
```

Validation of context injection into agent prompt.

Why mock FAISS:
    Real FAISS index requires loading embedding models (hundreds of MB),
    which is unacceptable for fast unit tests.

### `test_unicode_support` — Функция

```python
def test_unicode_support(self, mocker)
```

Validation of Cyrillic Unicode integrity in RAG search results.

### `test_empty_results_handling` — Функция

```python
def test_empty_results_handling(self)
```

Validation of agent behavior when RAG returns no matches.


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
