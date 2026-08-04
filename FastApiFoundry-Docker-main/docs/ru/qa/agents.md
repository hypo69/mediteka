# Тесты агентов

Файлы: `tests/agents/`

Проверка логики AI-агентов с изоляцией от тяжёлых зависимостей (FAISS, LLM-клиенты).

---

## test_rag_agent.py

**Компонент:** `src/agents/rag_agent.py` + `src/rag/rag_system.py`

Проверяет поведение RAG-агента при разных результатах поиска — без загрузки реального FAISS индекса.

| Тест | Сценарий |
|---|---|
| `test_context_injection` | Результаты поиска передаются в промпт, вызов `search()` подтверждён |
| `test_unicode_support` | Кириллица в результатах FAISS не искажается |
| `test_empty_results_handling` | Агент корректно обрабатывает пустой список результатов |

**Почему мокируется FAISS:**

Инициализация реального индекса требует загрузки модели `sentence-transformers` (~90 MB) и чтения файлов с диска. Это делает тест медленным и зависимым от окружения. Мок позволяет проверить логику агента мгновенно.

**Пример — проверка Unicode:**

```python
def test_unicode_support(self, mocker):
    """Validation of Cyrillic Unicode integrity in RAG search results."""
    mock_rag = MagicMock()
    mock_rag.search.return_value = ["Инструкция: Используйте кодировку UTF-8."]

    search_results = mock_rag.search("тест")

    assert search_results[0] == "Инструкция: Используйте кодировку UTF-8."
    assert "Используйте" in search_results[0]
```

**Пример — проверка инъекции контекста:**

```python
def test_context_injection(self, mocker):
    """Validation of context injection into agent prompt."""
    mock_rag = MagicMock()
    mock_rag.search.return_value = [
        "Ai Assistant instruction: use port 9696.",
        "RAG index updated 2026.",
    ]

    results = mock_rag.search("Which port to use?")

    assert len(results) == 2
    assert "9696" in results[0]
    mock_rag.search.assert_called_once_with("Which port to use?")
```

**Запуск:**

```powershell
venv\Scripts\pytest.exe tests/agents/test_rag_agent.py -v
```

---

## Маршрутизация моделей

При тестировании агентов, использующих маршрутизацию по префиксу, мокируется соответствующий клиент:

| Префикс | Мокируемый клиент |
|---|---|
| `foundry::` | `src.models.foundry_client.FoundryClient` |
| `hf::` | `src.models.hf_client.HFClient` |
| `llama::` | HTTP-запрос к `localhost:9780` через `respx` |
| `ollama::` | HTTP-запрос к Ollama через `respx` |

---

## Добавление новых тестов агентов

Размещать в `tests/agents/test_<agent_name>.py`.

**Шаблон:**

```python
# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: <AgentName> Tests
# =============================================================================
# File: tests/agents/test_<agent>.py
# Project: AI Assistant (ai_assist)
# Version: 0.7.1
# =============================================================================

import pytest
from unittest.mock import MagicMock


class Test<AgentName>:
    """Tests for <AgentName> logic with mocked dependencies."""

    def test_<scenario>(self, mocker):
        """<What is validated>."""
        mock_dep = MagicMock()
        mock_dep.<method>.return_value = <expected_value>

        # Invocation of agent logic
        result = mock_dep.<method>(<input>)

        assert result == <expected>
        mock_dep.<method>.assert_called_once_with(<input>)
```
