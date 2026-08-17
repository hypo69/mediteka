# Модуль `plugins.web_search` — Интеллектуальный веб-поиск

## Назначение
Плагин выполняет поиск информации в интернете по запросу пользователя с последующим анализом и суммаризацией результатов с помощью AI.

### Поддерживаемые движки поиска (выбираются в `config.json` -> `web_search.engine` или через UI):
1. **🎭 `playwright` (Playwright MCP)** — браузерный поиск через Playwright (DuckDuckGo, Bing, Google) с извлечением текста страниц (`playwright_searcher.py`).
2. **🦜 `langchain` (LangChain MCP)** — поиск и сбор медиа-данных через автономного ReAct-агента (`src/ai/langchain_agent.py`).
3. **♊ `gemini` (Google Gemini Grounding)** — официальный SDK `google-genai` со встроенным поиском Google Search Grounding и пулом ротации API-ключей (`gemini_searcher.py`).
4. **🚀 `agy` (Antigravity AGY)** — агентный поиск через встроенные инструменты `google.antigravity` (`BuiltinTools.SEARCH_WEB`, `READ_URL_CONTENT`) (`agy_searcher.py`).

### Структура модуля:
- `__init__.py`: основной класс плагина `WebSearchPlugin` с маршрутизацией между провайдерами.
- `playwright_searcher.py`: модуль браузерного парсинга Playwright.
- `gemini_searcher.py`: модуль поиска Google Gemini с классом `GeminiKeyPool` и `GeminiWebSearcher`.
- `agy_searcher.py`: модуль поиска Google Antigravity `AgyWebSearcher`.
- `triggers.py`: триггерные фразы и регулярные выражения для распознавания поисковых запросов в чате.