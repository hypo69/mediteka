# Модуль `src.ai` — Интеграция с AI-моделями

## Назначение
Пакет `src.ai` инкапсулирует логику взаимодействия с нейросетевыми моделями и агентами:
- `unified_chat.py`: единый роутер и фасад (`UnifiedChatModel`) для диспетчеризации запросов к Gemini, Foundry, AGY, Ollama.
- `gemini/`: модуль работы с Google Gemini API, локальным кэшем и пользовательскими RAG-индексами.
- `foundry_chat.py`: клиент Microsoft AI Foundry.
- `agy_chat.py`: интеграция с AGY SDK.
- `ollama_chat.py`: интеграция с локальными моделями Ollama.
- `langchain_agent.py`, `langchain_tools.py`, `langchain_prompts.py`: агентная оркестрация медиатеки на базе LangChain.
- `mcp_client.py`: интеграция с серверами протокола Model Context Protocol (MCP).
- `voice_pipeline.py`: конвейер обработки голосовых запросов и управления воспроизведением.\n