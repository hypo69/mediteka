# 📦 Директория исходного кода (src)

## Описание
Центральное хранилище исходного кода проекта **FastApiFoundry (Docker)**. Здесь сосредоточена основная бизнес-логика, API-интерфейсы, механизмы интеграции с AI-бэкендами и вспомогательные инструменты.

## Структура и назначение

| Директория | Назначение |
|---|---|
| `api/` | FastAPI приложение: фабрика (`app.py`), точка входа (`main.py`), все endpoints |
| `agents/` | Базовый класс агентов и реализации (PowerShellAgent) |
| `converter/` | Конвертер GGUF → ONNX |
| `core/` | Реэкспорт `config` из `config_manager.py` |
| `logger/` | Настройка системы логирования |
| `models/` | Клиенты AI-бэкендов: Foundry, HuggingFace, model_manager |
| `rag/` | RAG система: индексатор и `RAGSystem` |
| `translator/` | Модуль перевода текста |
| `utils/` | Утилиты: env_processor, foundry_finder, logging_config, log_analyzer |

## Принципы разработки

1. **Импорты**: Все внутренние модули импортируются через `from src...` относительно корня проекта.
2. **Конфигурация**: Только через `config_manager.Config` singleton — никогда напрямую из `config.json`.
3. **Логирование**: Через `logging.getLogger(__name__)`, с emoji-префиксами (`✅`, `❌`, `⚠️`).
4. **Async**: Все операции с AI-бэкендами и FAISS — асинхронные через `aiohttp` / `run_in_executor`.

---
**Версия:** 0.6.0
**Язык:** Python 3.11+
**Проект:** FastApiFoundry (Docker)
