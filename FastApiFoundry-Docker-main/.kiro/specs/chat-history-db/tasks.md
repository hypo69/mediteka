# План реализации: Chat History DB + RAG Integration

## Обзор

Реализация постоянного хранилища истории чатов на базе SQLite (`aiosqlite`) с
конвейером RAG-индексации диалогов в существующий FAISS-индекс. Все компоненты
подключаются к существующему FastAPI-приложению без изменения клиентского кода.

## Задачи

- [x] 1. Конфигурация и схема данных
  - Добавить секцию `chat_history` в `config.json` с полями `db_path`, `retention_days`, `max_sessions`, `rag_auto_ingest`
  - Добавить четыре свойства в класс `Config` в `config_manager.py`: `chat_history_db_path`, `chat_history_retention_days`, `chat_history_max_sessions`, `chat_history_rag_auto_ingest`
  - Обновить заголовок `config_manager.py`: версия `0.8.0`
  - _Требования: 7.1, 7.2, 7.3, 7.4, 10.1_

- [x] 2. Pydantic v2 схемы (`src/db/schemas.py`)
  - [x] 2.1 Создать файл `src/db/__init__.py` (пустой пакет)
    - _Требования: 2.1–2.8_

  - [x] 2.2 Создать `src/db/schemas.py` со всеми Pydantic v2 моделями
    - Реализовать `MessageRecord`, `SessionRecord`, `StartSessionRequest`, `SaveMessageRequest` (с `field_validator` для `content` и `session_id`), `SessionListResponse`, `SessionHistoryResponse`, `IngestRequest`, `IngestStatusResponse`
    - Валидатор `content_not_empty`: отклонять пустые строки и строки из пробелов
    - Валидатор `session_id_is_uuid4`: проверять соответствие формату UUID v4
    - _Требования: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8_

  - [x] 2.3 Написать property-тест: round-trip сериализации `MessageRecord` (Свойство 1)
    - **Свойство 1: Round-trip сериализации Pydantic-схем**
    - Использовать `hypothesis`: `st.sampled_from(["user","assistant","system"])`, `st.text(min_size=1)`, `st.integers(min_value=0)`
    - **Validates: Requirements 2.1, 9.5**

  - [x] 2.4 Написать property-тест: round-trip сериализации `SessionRecord` (Свойство 2)
    - **Свойство 2: Round-trip сериализации SessionRecord**
    - **Validates: Requirements 2.2**

  - [x] 2.5 Написать property-тест: валидация пустого `content` (Свойство 3)
    - **Свойство 3: Валидация пустого content**
    - Генерировать строки из пробельных символов (`st.text(alphabet=st.characters(whitespace=True), min_size=0)`)
    - **Validates: Requirements 2.7**

  - [x] 2.6 Написать property-тест: валидация не-UUID `session_id` (Свойство 4)
    - **Свойство 4: Валидация session_id не-UUID**
    - Генерировать произвольные строки, не являющиеся UUID v4
    - **Validates: Requirements 2.8**

  - [x] 2.7 Написать юнит-тесты граничных значений схем (`tests/unit/test_schemas.py`)
    - Пустой `content` → `ValidationError`
    - `content` из пробелов → `ValidationError`
    - Неверный `role` → `ValidationError`
    - Неверный формат `session_id` → `ValidationError`
    - `content` длиной 10 000 символов → успех
    - _Требования: 9.8_

- [ ] 3. Компонент доступа к данным (`src/db/chat_db.py`)
  - [ ] 3.1 Реализовать класс `DatabaseInitError` и класс `ChatDB`
    - Конструктор принимает `db_path: str`, раскрывает `~` через `Path.expanduser()`
    - Метод `initialize()`: создаёт таблицы `chat_sessions`, `chat_messages` и индекс `idx_messages_session_id` по SQL-схеме из дизайна; при ошибке выбрасывает `DatabaseInitError`
    - Метод `create_session(session_id, model, title)` → `SessionRecord`
    - Метод `save_message(session_id, role, content, timestamp)` → `MessageRecord`; атомарно обновляет `message_count` и `updated_at` в `chat_sessions`
    - Метод `get_session_history(session_id)` → `list[MessageRecord]` (сортировка по `timestamp ASC`)
    - Метод `list_sessions(limit, offset)` → `tuple[list[SessionRecord], int]` (сортировка по `updated_at DESC`)
    - Метод `delete_session(session_id)` → `bool` (каскадное удаление через `ON DELETE CASCADE`)
    - Метод `session_exists(session_id)` → `bool`
    - Метод `get_messages_since(since_timestamp, session_ids)` → `list[dict]`
    - Метод `close()`: закрывает соединение `aiosqlite`
    - Функция-синглтон `get_chat_db()` на уровне модуля
    - Заголовок файла: `Version: 0.8.0`, docstring Google Style для всех публичных методов
    - _Требования: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 8.1, 10.1_

  - [ ] 3.2 Написать юнит-тесты `ChatDB` (`tests/unit/test_chat_db.py`)
    - Использовать SQLite `:memory:` через `aiosqlite`
    - Тест: создание таблиц при инициализации (SMOKE)
    - Тест: сохранение и получение сессии
    - Тест: сохранение сообщения и проверка `message_count`
    - Тест: получение истории в хронологическом порядке
    - Тест: удаление сессии с каскадным удалением сообщений
    - Тест: `DatabaseInitError` при недоступном пути
    - _Требования: 9.1_

  - [ ] 3.3 Написать property-тест: round-trip хранения сообщений (Свойство 5)
    - **Свойство 5: Round-trip хранения сообщений в Chat_DB**
    - Генерировать произвольные наборы сообщений, сохранять в `:memory:` ChatDB, читать через `get_session_history()`, проверять порядок и значения полей
    - **Validates: Requirements 3.3, 9.6**

  - [ ] 3.4 Написать property-тест: монотонный рост `message_count` (Свойство 6)
    - **Свойство 6: Монотонный рост message_count**
    - После каждого `save_message()` значение `message_count` должно увеличиваться ровно на 1
    - **Validates: Requirements 3.2**

  - [ ] 3.5 Написать property-тест: каскадное удаление сессии (Свойство 7)
    - **Свойство 7: Каскадное удаление сессии**
    - После `delete_session()` ни сессия, ни её сообщения не должны возвращаться
    - **Validates: Requirements 3.5**

- [ ] 4. Контрольная точка — базовый слой данных
  - Убедиться, что все тесты задач 2 и 3 проходят. Уточнить у пользователя при возникновении вопросов.

- [ ] 5. FastAPI CRUD-эндпоинты (`src/api/endpoints/chat_db_endpoints.py`)
  - [ ] 5.1 Создать роутер с префиксом `/chat/db`
    - `POST /chat/db/session/start` → HTTP 201, тело `StartSessionRequest`, ответ с `session_id` и `created_at`
    - `POST /chat/db/message` → HTTP 200, тело `SaveMessageRequest`; HTTP 404 если `session_id` не найден
    - `GET /chat/db/session/{session_id}` → `SessionHistoryResponse`; HTTP 404 если не найден
    - `GET /chat/db/sessions?limit&offset` → `SessionListResponse`
    - `DELETE /chat/db/session/{session_id}` → HTTP 200; HTTP 404 если не найден; если `chat_history_rag_auto_ingest=true` — запускать `asyncio.create_task` для индексации
    - Заголовок файла: `Version: 0.8.0`, docstring для каждого эндпоинта
    - _Требования: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 7.5, 8.3, 10.3_

  - [ ] 5.2 Написать интеграционные тесты CRUD-эндпоинтов (`tests/integration/test_chat_db_endpoints.py`)
    - Использовать `httpx.AsyncClient` с in-memory SQLite (фикстура в `conftest.py`)
    - `POST /chat/db/session/start` → HTTP 201, уникальный `session_id`
    - `POST /chat/db/message` → HTTP 200, `message_count` растёт
    - `GET /chat/db/session/{id}` → хронологический порядок
    - `GET /chat/db/sessions` → сортировка по `updated_at DESC`
    - `DELETE /chat/db/session/{id}` → HTTP 200, каскадное удаление
    - `GET/DELETE` с несуществующим `session_id` → HTTP 404
    - _Требования: 9.3_

- [ ] 6. Write-through в существующих эндпоинтах (`src/api/endpoints/chat_endpoints.py`)
  - [ ] 6.1 Добавить вспомогательную функцию `_save_to_db_safe(session_id, role, content)`
    - Паттерн fire-and-forget: `asyncio.create_task(_save_to_db_safe(...))`
    - Ошибки `ChatDB` перехватываются, логируются, не прерывают HTTP-ответ
    - _Требования: 4.1, 4.3, 4.4_

  - [ ] 6.2 Добавить write-through в `POST /chat/message`
    - После успешной генерации: `asyncio.create_task(_save_to_db_safe(...))` для сообщения пользователя и ответа ассистента
    - In-memory `chat_sessions` dict сохраняется без изменений
    - Обновить заголовок файла: `Version: 0.8.0`
    - _Требования: 4.1, 4.3, 4.4, 10.3_

  - [ ] 6.3 Добавить write-through в `POST /chat/stream`
    - После завершения стриминга: `asyncio.create_task(_save_to_db_safe(...))` для накопленного ответа и сообщения пользователя
    - _Требования: 4.2, 4.3, 4.4_

- [ ] 7. Конвейер RAG-индексации (`src/rag/chat_history_ingestion.py`)
  - [ ] 7.1 Реализовать класс `ChatHistoryIngestion`
    - Конструктор принимает `chat_db: ChatDB` и `indexer: IncrementalIndexer`
    - Метод `_format_chunk_text(role, content)` → `"[{role}] {content}"`
    - Метод `_split_chunks(text)` → `list[str]`: разбивка с перекрытием 10% от `config.rag_chunk_size`; если текст короче `chunk_size` — возвращать список из одного элемента
    - Метод `_deduplicate(chunks)` → `list[str]`: удаление дубликатов с сохранением порядка
    - Метод `ingest(session_ids, since_timestamp)` → `dict`: извлечение сообщений из `ChatDB`, форматирование, дедупликация, генерация эмбеддингов через `IncrementalIndexer`, инкрементальное добавление в FAISS; если индекс не инициализирован — создать `IndexFlatL2`; сохранить индекс и `chunks.json` на диск
    - Заголовок файла: `Version: 0.8.0`, docstring Google Style
    - _Требования: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 8.2, 10.2_

  - [ ] 7.2 Написать property-тест: формат текста чанка (Свойство 8)
    - **Свойство 8: Формат текста чанка**
    - Генерировать произвольные `role` и `content`, проверять точное соответствие шаблону `"[{role}] {content}"`
    - **Validates: Requirements 5.1**

  - [ ] 7.3 Написать property-тест: ограничение размера чанка (Свойство 9)
    - **Свойство 9: Ограничение размера чанка**
    - Генерировать тексты длиннее `chunk_size`, проверять что все чанки ≤ `chunk_size`
    - **Validates: Requirements 5.2**

  - [ ] 7.4 Написать property-тест: полнота чанкирования (Свойство 10)
    - **Свойство 10: Полнота чанкирования**
    - Генерировать строки длиной от 1 до 10 000 символов, проверять что результат содержит хотя бы один чанк
    - **Validates: Requirements 5.2, 9.7**

  - [ ] 7.5 Написать property-тест: дедупликация чанков (Свойство 11)
    - **Свойство 11: Дедупликация чанков**
    - Генерировать наборы строк с дубликатами, проверять что после дедупликации количество элементов равно количеству уникальных строк
    - **Validates: Requirements 5.7**

  - [ ] 7.6 Написать юнит-тесты `ChatHistoryIngestion` (`tests/unit/test_chat_ingestion.py`)
    - Мок `SentenceTransformer` и `IncrementalIndexer`
    - Тест: формат чанка `[role] content`
    - Тест: разбивка длинных чанков
    - Тест: дедупликация
    - _Требования: 9.2_

- [ ] 8. FastAPI RAG-эндпоинты (`src/api/endpoints/rag_ingest_endpoints.py`)
  - [ ] 8.1 Создать роутер с префиксом `/rag/ingest`
    - In-memory хранилище задач: `_tasks: dict[str, IngestStatusResponse]`, `_running_task: asyncio.Task | None`
    - `POST /rag/ingest/chat-history` → HTTP 202 `{task_id, status: "started"}`; HTTP 409 если задача уже выполняется; поддержка параметров `session_ids` и `since_timestamp` из тела `IngestRequest`
    - `GET /rag/ingest/status/{task_id}` → `IngestStatusResponse`; HTTP 404 если `task_id` не найден
    - При ошибке конвейера: записывать полный traceback в лог, устанавливать `status=failed`
    - Заголовок файла: `Version: 0.8.0`, docstring для каждого эндпоинта
    - _Требования: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 8.4_

  - [ ] 8.2 Написать property-тест: инкрементальный рост FAISS-индекса (Свойство 12)
    - **Свойство 12: Инкрементальный рост FAISS-индекса**
    - Для N уникальных чанков: после `ingest()` значение `ntotal` FAISS-индекса должно увеличиться ровно на N
    - **Validates: Requirements 5.4**

  - [ ] 8.3 Написать property-тест: фильтрация по `session_ids` (Свойство 13)
    - **Свойство 13: Фильтрация индексации по session_ids**
    - Проверять что в индекс попадают только сообщения из указанных сессий
    - **Validates: Requirements 6.3**

  - [ ] 8.4 Написать property-тест: фильтрация по `since_timestamp` (Свойство 14)
    - **Свойство 14: Фильтрация индексации по since_timestamp**
    - Проверять что все проиндексированные чанки имеют `timestamp` строго больше `since_timestamp`
    - **Validates: Requirements 6.4**

  - [ ] 8.5 Написать интеграционные тесты RAG-эндпоинтов (`tests/integration/test_rag_ingest_endpoints.py`)
    - Мок `IncrementalIndexer`
    - `POST /rag/ingest/chat-history` → HTTP 202, `task_id`
    - `GET /rag/ingest/status/{task_id}` → корректный статус
    - Повторный `POST` при активной задаче → HTTP 409
    - _Требования: 9.4_

- [ ] 9. Контрольная точка — все компоненты реализованы
  - Убедиться, что все тесты задач 5–8 проходят. Уточнить у пользователя при возникновении вопросов.

- [ ] 10. Регистрация роутеров и инициализация в `app.py`
  - [ ] 10.1 Добавить инициализацию `ChatDB` в функцию `lifespan()`
    - Вызвать `db = await get_chat_db()` и `await db.initialize()`
    - При `DatabaseInitError`: логировать предупреждение, продолжать работу в деградированном режиме (эндпоинты `/chat/db/*` возвращают HTTP 503)
    - _Требования: 1.6_

  - [ ] 10.2 Зарегистрировать новые роутеры в `create_app()`
    - Импортировать `chat_db_endpoints.router` и `rag_ingest_endpoints.router`
    - Подключить оба роутера с префиксом `/api/v1`
    - Обновить версию приложения до `0.8.0` в `FastAPI(version=...)`
    - _Требования: 3.1–3.8, 6.1–6.6_

- [ ] 11. Обновление версии и документация
  - [ ] 11.1 Обновить файл `VERSION` до `0.8.0`
    - _Требования: 10.1–10.3_

  - [ ] 11.2 Добавить запись `## [0.8.0]` в `CHANGELOG.md`
    - Описать: `ChatDB` (SQLite + aiosqlite), `ChatHistoryIngestion`, новые эндпоинты `/chat/db/` и `/rag/ingest/`, write-through в `/chat/message` и `/chat/stream`
    - _Требования: 10.4_

  - [ ] 11.3 Создать `docs/ru/chat-history-db.md`
    - Разделы: «Архитектура», «Конфигурация», «API-эндпоинты», «Примеры использования»
    - _Требования: 8.5_

- [ ] 12. Финальная контрольная точка
  - Убедиться, что все тесты проходят (`pytest tests/ -v`). Уточнить у пользователя при возникновении вопросов.

## Примечания

- Задачи, отмеченные `*`, являются необязательными и могут быть пропущены для ускоренного MVP
- Каждая задача ссылается на конкретные требования для обеспечения трассируемости
- Property-тесты используют библиотеку `hypothesis` с профилем `@settings(max_examples=100)`
- Write-through в задаче 6 использует паттерн fire-and-forget: ошибки БД не блокируют HTTP-ответ
- In-memory словарь `chat_sessions` сохраняется для обратной совместимости в v0.8.0
- Конфигурация `conftest.py` должна включать фикстуры: in-memory `ChatDB`, тестовый `app` с переопределённой зависимостью `get_chat_db`
