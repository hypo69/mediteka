# Code Reference

Полный справочник по исходному коду проекта **AI Assistant (ai_assist)**.

Документация организована по структуре `src/` — каждый раздел соответствует Python-модулю в исходном коде.

На страницах модулей `mkdocstrings` показывает:

- имя функции или класса;
- сигнатуру;
- docstring;
- `Args`, `Returns`, `Raises`;
- раскрываемый блок `Source code in ...` с кодом функции.

---

## Структура `src/`

```
src/
├── agents/          # AI агенты (RAG, PowerShell, MCP, Google, ...)
├── api/             # FastAPI приложение
│   └── endpoints/   # Все REST endpoints
├── converter/       # GGUF → ONNX конвертер
├── core/            # Config singleton
├── db/              # SQLite: история чата
├── models/          # AI клиенты (Foundry, HF, Ollama, llama.cpp, router)
├── rag/             # RAG система (FAISS + text extractors)
│   └── text_extractors/
├── training/        # Дообучение моделей
└── utils/           # Утилиты (api_utils, translator, logging, ...)
```

Документация генерируется автоматически из docstrings через `mkdocstrings`.
Для регенерации запустите:

```powershell
venv\Scripts\python.exe scripts\Create-Doc\Generate-CodeReference.py
```

## Быстрые ссылки

- [FastAPI endpoints](src/api/endpoints/models.md)
- [AI clients](src/models/model_manager.md)
- [RAG system](src/rag/rag_system.md)
- [Agents](src/agents/base.md)
- [Utilities](src/utils/api_utils.md)

## Требуемый формат docstring

Используйте Google style. Для исключений пишите `Raises:`, а не `Exceptions:`. Для параметров функции пишите `Args:`, а не `Attrs:`.

```python
async def get_all_models() -> dict:
    """Get all local models from all providers.

    Returns:
        dict: Response payload with success flag, models, count, and provider counters.

    Raises:
        RuntimeError: If model discovery cannot be initialized.
    """
```

---

*Проект: AI Assistant (ai_assist) · v0.8.0*
