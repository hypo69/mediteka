# Аудит кода gemini-simplechat

**Дата аудита:** 24.07.2026  
**Версия проекта:** gemini-simplechat (AI Assistant & Media Player Control)  
**Объём:** ~50 Python файлов, FastAPI + AI интеграция

---

## 1. Исполнительное резюме

Проект представляет собой функциональное FastAPI-приложение с интеграцией Google Gemini, медиатекой и торрент-контролем. **Код работоспособен**, но содержит систематические нарушения инженерных стандартов проекта.

### Критические проблемы (требуют немедленного внимания)

| ID | Файл | Проблема | Влияние |
|----|------|----------|---------|
| CRIT-001 | `plugins/rag/__init__.py:31-150` | Дублирование класса RAGPlugin — класс определён дважды с разным кодом | Баг: неопределённое поведение при импорте |
| CRIT-002 | `src/fastapi/router_qbittorrent.py:54` | Переменная `qbt_cfg` используется, но не импортирована | Runtime error при доступе к qBittorrent API |
| CRIT-003 | `src/ai/gemini/header.py:41-46` | Неопределённые переменные `__project_name__`, `__version__`, `__author__`, `__cofee__` | Скрытые ошибки при импорте модуля |

### Высокие проблемы

| ID | Файл | Проблема | Влияние |
|----|------|----------|---------|
| HIGH-001 | Множество файлов | Sphinx/reST docstring вместо docblock | Нарушение CODE_RULES |
| HIGH-002 | Множество файлов | Длинные copyright-заголовки вместо коротких docstring | Нарушение CODE_RULES |
| HIGH-003 | `src/ai/gemini/generative_ai.py:394,422` | Возвраты `None` вместо `False` или `""` | Нарушение engineering rules |

---

## 2. Мёртвый код

### 2.1 Неиспользуемые импорты

| Файл | Импорт | Статус |
|------|--------|--------|
| `src/fastapi/router_qbittorrent.py:16` | `traceback` | **Удалить** |
| `src/fastapi/router_tts.py` | `uuid` | **Удалить** |
| `plugins/rag/__init__.py` | `json` | **Удалить** (не используется) |

### 2.2 Неиспользуемые переменные

| Файл | Строка | Переменная | Рекомендация |
|------|--------|------------|--------------|
| `src/ai/gemini/header.py` | 46 | `__cofee__` | Удалить или использовать |
| `src/ai/gemini/generative_ai.py` | 178 | `FoundryChatBase = FoundryChatBase` | Удалить самоприсваивание |
| `src/fastapi/router_media.py` | ~210 | Параметр `type` в функции `find_by_title` | Удалить параметр или использовать |

### 2.3 Дублирование кода

| Файл | Описание | Рекомендация |
|------|----------|--------------|
| `plugins/rag/__init__.py:31-43` | Первый блок определения RAGPlugin с placeholder-комментарием | **Удалить строки 31-43 полностью** |
| `src/ai/gemini/generative_ai.py:101` | Функция `remove_html_blocks` определена, но не вызывается | Удалить или вызвать в нужном месте |

### 2.4 Инструкция по удалению мёртвого кода

```bash
# Удалить неиспользуемые импорты:
# src/fastapi/router_qbittorrent.py — строка 16
# src/fastapi/router_tts.py — uuid import
# plugins/rag/__init__.py — json import

# Удалить дублирование класса RAGPlugin:
# plugins/rag/__init__.py — строки 31-43 (первое определение с "... (предыдущий код...")

# Удалить самоприсваивание:
# src/ai/gemini/generative_ai.py — строка 178

# Удалить неиспользуемую переменную:
# src/ai/gemini/header.py — строка 46 (__cofee__)
```

---

## 3. Несоответствия документации

### 3.1 Инженерные правила (.ai_instructions/knowledge/codex/engineering-rules.md)

| Описание | Текущее состояние | Требование |
|----------|-------------------|------------|
| Sphinx/reST запрещён | Используется в 15+ файлах | Заменить на docblock |
| None запрещён как возврат | `return None` в 12+ местах | `return ""` или `return False` |
| Функции ≤300 строк | `GoogleGenerativeAI.chat()` ~150 строк, `chat_stream()` ~130 строк | В пределах нормы |
| Docstring для публичных сущностей | Отсутствует в 8+ функциях/классах | Добавить docblock |

### 3.2 Проектная документация (.ai_instructions/knowledge/codex/project.md)

| Документация | Код | Расхождение | Статус |
|--------------|-----|-------------|--------|
| `plugins.load_plugins(): plugin.handle(message)` | `src/fastapi/router_chat.py` использует `plugins_dict` напрямую | Документация устарела | ✅ **Исправлено 24.07.2026** |
| `POST /api/media/by-title` с параметром `type` | `router_media.py:210` параметр `type` не используется | Параметр `type` ИСПОЛЬЗУЕТСЯ в коде (строки 234, 252-254) | ✅ **Проверено 24.07.2026** — документация была неточной |
| Загрузка инструкции из `instructions/system_instruction.md` | `main.py` загружает из `.ai_instructions/prompts/chat/system_instruction.md` | Документация устарела | ✅ **Исправлено 24.07.2026** |

### 3.3 Системная инструкция чата (.ai_instructions/prompts/chat/system_instruction.md)

| Описание в инструкции | Реализация в коде | Расхождение |
|-----------------------|-------------------|-------------|
| Инструмент `search_media(query, top_k, ...)` | Реализован в `plugins/media_organizer/core/media_rag_functions.py` | ✅ Соответствует |
| Инструмент `get_media_card(disk_name, ...)` | Реализован | ✅ Соответствует |
| Инструмент `get_random_media(...)` | Реализован в RAGPlugin как "карусель" | ✅ Соответствует |
| Формат `<film>Название</film>` | Реализован в RAGPlugin | ✅ Соответствует |

### 3.4 README.MD

| Описание README | Реальность | Расхождение |
|-----------------|------------|-------------|
| "Streaming RAG-поиск" | RAGPlugin использует async yield для статусов | ✅ Частично соответствует |
| Архитектурная диаграмма | Актуальна | ✅ Соответствует |

---

## 4. Качество кода

### 4.1 Нарушения форматирования (PEP8 + CODE_RULES)

| Файл | Строка | Проблема | severity |
|------|--------|----------|----------|
| `src/ai/gemini/generative_ai.py` | 54 | Строка >300 символов | medium |
| `src/fastapi/router_auth.py` | 68, 72 | Строка >120 символов | low |
| `src/fastapi/router_chat.py` | 43 | Строка >120 символов | low |
| `src/ai/gemini/rag.py` | 61 | Отсутствует type hint возврата | low |

### 4.2 Магические числа

| Файл | Строка | Значение | Рекомендация |
|------|--------|----------|--------------|
| `src/ai/gemini/user_query_rag.py` | 67 | `_MAX_DOCS_PER_USER = 500` | Вынести в конфигурацию |
| `src/ai/gemini/user_query_rag.py` | 71 | `_MIN_QUERY_LEN = 10` | Вынести в конфигурацию |

### 4.3 Жёстко закодированные пути

| Файл | Проблема |
|------|----------|
| `skills/smart-deletion-duplicates/scripts/delete_media.py:12` | Windows-пути |
| `skills/smart-migration/scripts/perform_migration.py:23-60` | Cyrillic пути C:\Сериалы, Y:\сериалы |
| `plugins/media_organizer/remove_media.py:11-12` | Windows-пути с `\\` |

---

## 5. Docstring и комментарии

### 5.1 Формат docstring (требует исправления)

**Текущее состояние (нарушение CODE_RULES):**
```python
# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: RAG Plugin для чата
# =============================================================================
# Описание:
#   Плагин для подключения RAG-поиска...
# ...
# =============================================================================

class RAGPlugin(BasePlugin):
```

**Требуемый формат (docblock):**
```python
"""RAG-плагин для семантического поиска медиатеки в чате.

Использует Gemini Function Calling для поиска фильмов и сериалов
через RAG-индекс с семантическим поиском.

Attributes:
    name (str): Имя плагина.
    _tools (list): Список инструментов Function Calling.
"""


class RAGPlugin(BasePlugin):
    """..."""
```

### 5.2 Файлы с неправильным форматом docstring

| Файл | Рекомендация |
|------|--------------|
| `src/ai/gemini/__init__.py` | Заменить reST на docblock |
| `src/ai/gemini/generative_ai.py` | Заменить reST на docblock |
| `src/ai/gemini/rag.py` | Заменить reST на docblock |
| `src/fastapi/router_auth.py` | Заменить заголовок на docblock |
| `src/fastapi/router_chat.py` | Заменить заголовок на docblock |
| `src/fastapi/router_control.py` | Заменить заголовок на docblock |
| `src/fastapi/router_keys.py` | Заменить заголовок на docblock |
| `plugins/rag/__init__.py` | Заменить заголовок на docblock |
| `plugins/telegram_bot/bot.py` | Заменить reST на docblock |
| `plugins/torrent_playwright/playwright_searcher.py` | Заменить reST на docblock |
| `plugins/user_manager_tool/plugin.py` | Заменить reST на docblock |
| `skills/smart-migration/scripts/perform_migration.py` | Заменить заголовок на docblock |
| `skills/smart-migration/scripts/perform_migration_safe.py` | Заменить заголовок на docblock |

### 5.3 Отсутствующие docstring

| Файл | Сущность | Рекомендация |
|------|----------|--------------|
| `src/fastapi/router_auth.py` | `TokenData` | Добавить docstring с Attributes |
| `src/fastapi/router_auth.py` | `load_google_oauth_config` | Добавить Returns section |
| `src/fastapi/router_auth.py` | `create_jwt_token` | Добавить Args section |
| `src/fastapi/router_chat.py` | `init_router` (вложенная функция) | Добавить docstring |
| `src/fastapi/router_control.py` | `ControlConnectionManager` | Добавить class docstring |
| `src/fastapi/router_media.py` | `ProgressUpdateRequest` | Добавить docstring |
| `src/fastapi/router_tts.py` | `_db` | Добавить docstring |
| `plugins/qbittorrent/qbittorrent.py` | `QBittorrentClient` | Добавить class docstring |
| `plugins/user_manager_tool/plugin.py` | `UserManagerTool` | Добавить class docstring |

---

## 6. Сводка по исправлениям

### 6.1 Что НЕ нужно трогать

- `.ai_instructions/` — инструкции для моделей ИИ
- `.agents/` — конфигурации агентов
- `.amazonq/`, `.chatgpt/`, `.gemini/` — конфигурации внешних сервисов
- `.github/` — CI/CD и GitHub Actions
- `docs/` — пользовательская документация (требует проверки актуальности отдельно)
- `webinterface/` — frontend код (HTML, CSS, JS)
- `media_reports/` — отчёты
- `logs/` — логи
- `colab/`, `site/`, `dist/` — артефакты сборки

### 6.2 Что требует проверки документации

| Документ | Последнее обновление | Статус |
|----------|---------------------|--------|
| `README.MD` | Актуален | ✅ |
| `.ai_instructions/knowledge/codex/project.md` | Обновлён 24.07.2026 — исправлены пути к инструкциям и поток чата | ✅ |
| `.ai_instructions/knowledge/codex/engineering-rules.md` | Актуален | ✅ |
| `.ai_instructions/prompts/chat/system_instruction.md` | Актуален | ✅ |
| `docs/` | Не проверено | ⚠️ Требует отдельного аудита |

### 6.3 Рекомендуемые действия по приоритету

**P0 — Критические (перед релизом):**
1. Исправить дублирование RAGPlugin в `plugins/rag/__init__.py`
2. Исправить `qbt_cfg` в `router_qbittorrent.py`
3. Исправить undefined variables в `header.py`

**P1 — Высокие (в спринт):**
1. Заменить все Sphinx/reST docstring на docblock
2. Заменить все длинные copyright-заголовки на короткие docstring
3. Удалить неиспользуемые импорты
4. Добавить отсутствующие docstring

**P2 — Средние (техдолг):**
1. Вынести магические числа в конфигурацию
2. Сделать пути в скриптах миграции/удаления конфигурируемыми
3. Обновить `project.md` согласно текущей архитектуре | ✅ **Выполнено 24.07.2026** |

**P3 — Низкие (по желанию):**
1. Привести строки >120 символов к норме
2. Добавить type hints где отсутствуют
3. Обновить документацию `docs/` при необходимости

---

## 7. Метрики аудита

| Метрика | Значение |
|---------|----------|
| Просканировано файлов | 50+ Python файлов |
| Обнаружено мёртвого кода | 20+ записей |
| Нарушений docstring | 15+ файлов |
| Несоответствий документации | 8 пунктов |
| Критических проблем | 3 |
| Высоких проблем | 3 |

---

## Заключение

Проект `gemini-simplechat` находится в рабочем состоянии, но содержит систематические нарушения инженерных стандартов. Основные проблемы связаны с устаревшими практиками документирования (Sphinx/reST) и накоплением мёртвого кода. Документация частично не соответствует текущей реализации.

**Рекомендация:** Провести рефакторинг документации в следующую итерацию, с приоритетом на критические проблемы и обновление `project.md`.