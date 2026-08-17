---
name: db-inspector
description: Инструментарий для анализа, проверки и модификации SQLite базы данных медиатеки. Используйте для получения схемы, проверки целостности данных, поиска неполных записей и отладки RAG.
---

# DB Inspector

## 🚀 Быстрый старт

Используйте этот навык для работы с `media.db`.

- **Проверка структуры БД:**
  `python plugins/media_organizer/tools/get_schema.py`
- **Проверка данных:**
  `python plugins/media_organizer/tools/check_db.py`
- **Поиск неполных записей:**
  `python plugins/media_organizer/tools/find_incomplete_records.py`
- **Инспекция RAG:**
  `python plugins/rag/tools/inspect_user_rags.py`

## 📂 Справочные материалы

- **Структура БД:** См. описание в `knowledge/media_organizer_workflow.md` в `.ai_instructions`.
