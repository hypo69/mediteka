# Карта репозитория

Эта страница описывает структуру проекта и помогает понять, где искать код.

Если нужен справочник функций, классов, docstrings, `Args`, `Returns`, `Raises` и исходный код функций, откройте раздел [Code Reference](code/index.md). Он генерируется из `src/**/*.py` через `mkdocstrings`.

## Основные директории

| Путь | Назначение |
|---|---|
| `src/api/` | FastAPI приложение, роутеры и модели API. |
| `src/api/endpoints/` | REST endpoints. Для справки по функциям см. [Endpoints](code/src/api/endpoints/models.md). |
| `src/agents/` | AI агенты: RAG, MCP, Google, PowerShell и другие. |
| `src/models/` | Клиенты и маршрутизация моделей: Foundry, HuggingFace, Ollama, llama.cpp, LM Studio. |
| `src/rag/` | RAG pipeline, индексирование, хранилище документов, профили. |
| `src/utils/` | Общие утилиты: логирование, перевод, обработка окружения, API helpers. |
| `scripts/` | PowerShell/Python автоматизация разработки, QA, сборки и документации. |
| `install/` | Скрипты установки зависимостей и первичной настройки. |
| `tests/` | Тесты и тестовая инфраструктура. |
| `extensions/` | Браузерные расширения и связанные компоненты. |

## Где смотреть документацию по коду

- Python modules: [Code Reference](code/index.md)
- FastAPI endpoints: [src/api/endpoints](code/src/api/endpoints/models.md)
- AI clients: [src/models](code/src/models/model_manager.md)
- RAG: [src/rag](code/src/rag/rag_system.md)
- Utilities: [src/utils](code/src/utils/api_utils.md)
- PowerShell scripts: [PowerShell Scripts](powershell/index.md)

## Формат docstring

Для Python используется Google style:

```python
def example(name: str) -> dict:
    """Short function description.

    Args:
        name: Input name.

    Returns:
        dict: Result payload.

    Raises:
        ValueError: If name is empty.
    """
```

В сгенерированном HTML `mkdocstrings` показывает имя функции, сигнатуру, docstring-секции и раскрываемый блок `Source code in ...`.
