import pytest
from unittest.mock import AsyncMock, patch
from src.agents.rag_agent import RagAgent
from src.agents.base import AgentResult
# from src.rag.rag_system import RAGSystem # RAGSystem is a singleton, mocked directly

@pytest.fixture
def mock_rag_system():
    """Фикстура для мокирования синглтона rag_system."""
    with patch('src.agents.rag_agent.rag_system', new_callable=AsyncMock) as mock_system:
        # Мокируем атрибут index, так как он проверяется
        mock_system.index = True # Симулируем загруженный индекс
        yield mock_system

@pytest.mark.asyncio
async def test_rag_agent_rag_search_with_markdown_tables(mock_rag_system):
    """
    Тестирование инструмента rag_search RagAgent'а с контентом, симулирующим
    вывод MarkItDown, включая таблицы.
    """
    agent = RagAgent(foundry_client=None) # foundry_client не используется в _execute_tool для rag_search

    # Симулируем вывод MarkItDown для PDF с таблицей
    mock_markdown_content = """
# Отчет о продажах за Q1 2024

## Обзор
Это обзор продаж за первый квартал 2024 года.

## Детали продаж по регионам

| Регион    | Продажи (USD) | Прибыль (USD) |
|-----------|---------------|---------------|
| Север     | 150000        | 30000         |
| Юг        | 120000        | 25000         |
| Восток    | 180000        | 40000         |
| Запад     | 100000        | 20000         |

## Выводы
Общие продажи составили 550,000 USD.
"""
    
    # Мокируем rag_system.search, чтобы он возвращал результаты, содержащие этот markdown
    mock_rag_system.search.return_value = [
        {"content": mock_markdown_content, "score": 0.95, "metadata": {"source": "report_q1_2024.pdf"}},
        {"content": "Дополнительная информация о продуктах.", "score": 0.80, "metadata": {"source": "products.docx"}}
    ]
    
    # Мокируем rag_system.format_context, чтобы он возвращал отформатированный markdown
    mock_rag_system.format_context.return_value = (
        "Контекст из report_q1_2024.pdf:\n" + mock_markdown_content +
        "\n\nКонтекст из products.docx:\nДополнительная информация о продуктах."
    )

    # Вызываем метод _execute_tool для rag_search
    tool_output = await agent._execute_tool(
        name="rag_search",
        arguments={"query": "продажи за Q1 2024", "top_k": 2}
    )

    # Проверки
    assert "Найдено фрагментов: 2" in tool_output
    assert "Источники: report_q1_2024.pdf, products.docx" in tool_output
    assert "Отчет о продажах за Q1 2024" in tool_output
    assert "| Регион    | Продажи (USD) | Прибыль (USD) |" in tool_output
    assert "Общие продажи составили 550,000 USD." in tool_output
    
    mock_rag_system.search.assert_called_once_with("продажи за Q1 2024", top_k=2)
    mock_rag_system.format_context.assert_called_once()

@pytest.mark.asyncio
async def test_rag_agent_generate_answer_tool():
    """Тестирование инструмента generate_answer RagAgent'а."""
    agent = RagAgent(foundry_client=None)
    
    question = "Как дела с продажами?"
    context = "Продажи в Q1 составили 550,000 USD. Это хороший результат."
    
    tool_output = await agent._execute_tool(
        name="generate_answer",
        arguments={"question": question, "context": context}
    )
    
    assert "Вопрос: Как дела с продажами?" in tool_output
    assert "Контекст из базы знаний:\nПродажи в Q1 составили 550,000 USD. Это хороший результат." in tool_output
    assert "Ответь на вопрос, опираясь только на предоставленный контекст." in tool_output

@pytest.mark.asyncio
async def test_rag_agent_rag_search_no_index(mock_rag_system):
    """Тестирование rag_search, когда RAG-индекс не загружен."""
    mock_rag_system.index = None # Симулируем отсутствие загруженного индекса
    agent = RagAgent(foundry_client=None)
    
    tool_output = await agent._execute_tool(
        name="rag_search",
        arguments={"query": "что-то"}
    )
    
    assert "⚠️ RAG-индекс не загружен." in tool_output
    mock_rag_system.search.assert_not_called()

@pytest.mark.asyncio
async def test_rag_agent_rag_search_no_results(mock_rag_system):
    """Тестирование rag_search, когда релевантные фрагменты не найдены."""
    mock_rag_system.search.return_value = []
    agent = RagAgent(foundry_client=None)
    
    tool_output = await agent._execute_tool(
        name="rag_search",
        arguments={"query": "несуществующий запрос"}
    )
    
    assert "Релевантные фрагменты не найдены" in tool_output
    mock_rag_system.search.assert_called_once_with("несуществующий запрос", top_k=5)