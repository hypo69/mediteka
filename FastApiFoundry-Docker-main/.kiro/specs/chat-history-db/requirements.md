# Документ требований: Chat History DB + RAG Integration

**Версия:** 0.8.0  
**Дата:** 2026  
**Автор:** hypo69  
**Статус:** Черновик — ожидает проверки

---

## Введение

Функциональность добавляет постоянное хранилище истории чатов на базе SQLite,
заменяя текущий подход (in-memory словарь + JSON-файлы на диске).
На основе сохранённой истории формируется конвейер RAG-индексации:
диалоги преобразуются в текстовые чанки и загружаются в существующий FAISS-индекс.
Все операции доступны через FastAPI. Все схемы запросов и ответов описаны
Pydantic-моделями. Версия проекта повышается до 0.8.0.

---

## Глоссарий

- **Chat_DB** — компонент доступа к данным (SQLite через `aiosqlite`), отвечающий за хранение сессий и сообщений.
- **Session** — запись в таблице `chat_sessions`, идентифицирующая один диалог (UUID, модель, метаданные).
- **Message** — запись в таблице `chat_messages`, содержащая одно сообщение диалога (роль, текст, временная метка).
- **Chat_API** — набор FastAPI-эндпоинтов для CRUD-операций над историей чатов.
- **RAG_Ingestion_Pipeline** — компонент, преобразующий сообщения из Chat_DB в текстовые чанки и передающий их в RAG_System.
- **RAG_System** — существующий компонент (`src/rag/rag_system.py`), управляющий FAISS-индексом.
- **RAG_API** — набор FastAPI-эндпоинтов для управления RAG-индексацией из истории чатов.
- **Pydantic_Schema** — Pydantic v2 модель, описывающая структуру запроса или ответа API.
- **Chunk** — фрагмент текста фиксированного размера, передаваемый в FAISS для индексации.
- **Config** — singleton `config_manager.Config`, предоставляющий доступ к `config.json`.
- **Validator** — компонент валидации входных данных на уровне Pydantic-схем.

---

## Требования

---

### Требование 1: Инициализация базы данных SQLite

**User Story:** Как разработчик, я хочу, чтобы при старте приложения автоматически
создавалась SQLite-база данных с нужной схемой, чтобы история чатов сохранялась
между перезапусками без ручной настройки.

#### Критерии приёмки

1. THE Chat_DB SHALL создавать файл базы данных SQLite по пути, заданному в секции `chat_history.db_path` файла `config.json`, при первом обращении.
2. WHEN путь к базе данных содержит символ `~`, THE Chat_DB SHALL раскрывать его до абсолютного пути домашней директории пользователя.
3. THE Chat_DB SHALL создавать таблицу `chat_sessions` со столбцами: `session_id TEXT PRIMARY KEY`, `model TEXT`, `title TEXT`, `created_at INTEGER`, `updated_at INTEGER`, `message_count INTEGER DEFAULT 0`, `aborted INTEGER DEFAULT 0`.
4. THE Chat_DB SHALL создавать таблицу `chat_messages` со столбцами: `id INTEGER PRIMARY KEY AUTOINCREMENT`, `session_id TEXT NOT NULL`, `role TEXT NOT NULL`, `content TEXT NOT NULL`, `timestamp INTEGER NOT NULL`, `FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id) ON DELETE CASCADE`.
5. THE Chat_DB SHALL создавать индекс по столбцу `session_id` таблицы `chat_messages` для ускорения выборки истории сессии.
6. IF файл базы данных повреждён или недоступен для записи, THEN THE Chat_DB SHALL записать сообщение об ошибке в лог и выбросить исключение `DatabaseInitError`.
7. THE Chat_DB SHALL поддерживать асинхронный доступ через библиотеку `aiosqlite`.

---

### Требование 2: Pydantic-схемы для истории чатов

**User Story:** Как разработчик API, я хочу, чтобы все запросы и ответы,
связанные с историей чатов, были описаны Pydantic v2 моделями, чтобы
обеспечить автоматическую валидацию и генерацию OpenAPI-документации.

#### Критерии приёмки

1. THE Pydantic_Schema SHALL определять модель `MessageRecord` с полями: `role: Literal["user", "assistant", "system"]`, `content: str`, `timestamp: int`.
2. THE Pydantic_Schema SHALL определять модель `SessionRecord` с полями: `session_id: str`, `model: str`, `title: str`, `created_at: int`, `updated_at: int`, `message_count: int`, `aborted: bool`.
3. THE Pydantic_Schema SHALL определять модель `StartSessionRequest` с полями: `model: str = "default"`, `title: str = ""`.
4. THE Pydantic_Schema SHALL определять модель `SaveMessageRequest` с полями: `session_id: str`, `role: Literal["user", "assistant", "system"]`, `content: str`.
5. THE Pydantic_Schema SHALL определять модель `SessionListResponse` с полями: `success: bool`, `sessions: list[SessionRecord]`, `total: int`.
6. THE Pydantic_Schema SHALL определять модель `SessionHistoryResponse` с полями: `success: bool`, `session_id: str`, `messages: list[MessageRecord]`.
7. WHEN поле `content` модели `SaveMessageRequest` является пустой строкой, THE Validator SHALL возвращать ошибку валидации с кодом HTTP 422.
8. WHEN поле `session_id` модели `SaveMessageRequest` не соответствует формату UUID v4, THE Validator SHALL возвращать ошибку валидации с кодом HTTP 422.

---

### Требование 3: FastAPI CRUD-эндпоинты для истории чатов

**User Story:** Как клиент API, я хочу иметь полный набор эндпоинтов для
создания, чтения и удаления истории чатов через HTTP, чтобы управлять
диалогами из любого клиента.

#### Критерии приёмки

1. WHEN клиент отправляет `POST /api/v1/chat/db/session/start` с телом `StartSessionRequest`, THE Chat_API SHALL создавать новую запись в таблице `chat_sessions` и возвращать `session_id` и `created_at` с кодом HTTP 201.
2. WHEN клиент отправляет `POST /api/v1/chat/db/message` с телом `SaveMessageRequest`, THE Chat_API SHALL сохранять сообщение в таблице `chat_messages` и атомарно обновлять `message_count` и `updated_at` в соответствующей записи `chat_sessions`.
3. WHEN клиент отправляет `GET /api/v1/chat/db/session/{session_id}`, THE Chat_API SHALL возвращать все сообщения сессии в хронологическом порядке по полю `timestamp` в формате `SessionHistoryResponse`.
4. WHEN клиент отправляет `GET /api/v1/chat/db/sessions` с параметрами `limit: int = 50` и `offset: int = 0`, THE Chat_API SHALL возвращать список сессий, отсортированных по `updated_at` по убыванию, в формате `SessionListResponse`.
5. WHEN клиент отправляет `DELETE /api/v1/chat/db/session/{session_id}`, THE Chat_API SHALL удалять запись сессии и все связанные сообщения каскадно и возвращать код HTTP 200.
6. IF `session_id` в запросах `GET` или `DELETE` не существует в базе данных, THEN THE Chat_API SHALL возвращать код HTTP 404 с описанием ошибки.
7. IF `session_id` в запросе `POST /api/v1/chat/db/message` не существует в базе данных, THEN THE Chat_API SHALL возвращать код HTTP 404.
8. THE Chat_API SHALL принимать и возвращать данные в формате JSON с кодировкой UTF-8.

---

### Требование 4: Миграция существующей логики чатов на SQLite

**User Story:** Как пользователь системы, я хочу, чтобы сообщения, отправляемые
через существующие эндпоинты `/chat/message` и `/chat/stream`, автоматически
сохранялись в SQLite, чтобы история не терялась при перезапуске сервера.

#### Критерии приёмки

1. WHEN эндпоинт `POST /api/v1/chat/message` успешно генерирует ответ, THE Chat_API SHALL сохранять сообщение пользователя и ответ ассистента в Chat_DB в рамках одной транзакции.
2. WHEN эндпоинт `POST /api/v1/chat/stream` завершает стриминг, THE Chat_API SHALL сохранять накопленный ответ ассистента и сообщение пользователя в Chat_DB.
3. WHILE сохранение в Chat_DB завершается с ошибкой, THE Chat_API SHALL возвращать ответ клиенту без прерывания и записывать ошибку в лог (сохранение в БД не блокирует ответ).
4. THE Chat_API SHALL сохранять in-memory сессию (`chat_sessions` dict) параллельно с записью в SQLite для обратной совместимости в версии 0.8.0.

---

### Требование 5: Конвейер RAG-индексации из истории чатов

**User Story:** Как пользователь системы, я хочу, чтобы история диалогов
автоматически преобразовывалась в RAG-чанки и добавлялась в FAISS-индекс,
чтобы AI-ассистент мог использовать прошлые диалоги как источник знаний.

#### Критерии приёмки

1. THE RAG_Ingestion_Pipeline SHALL извлекать сообщения из Chat_DB и формировать текстовые чанки в формате: `"[{role}] {content}"` с метаданными `source: "chat_history"`, `session_id`, `timestamp`.
2. WHEN размер сформированного чанка превышает значение `rag_system.chunk_size` из `config.json`, THE RAG_Ingestion_Pipeline SHALL разбивать чанк на части с перекрытием в 10% от `chunk_size`.
3. THE RAG_Ingestion_Pipeline SHALL генерировать векторные эмбеддинги для чанков с использованием той же модели `SentenceTransformer`, что и RAG_System.
4. THE RAG_Ingestion_Pipeline SHALL добавлять сгенерированные векторы в существующий FAISS-индекс без полного пересоздания индекса (инкрементальное обновление).
5. IF FAISS-индекс не инициализирован, THEN THE RAG_Ingestion_Pipeline SHALL создавать новый индекс типа `IndexFlatL2` с размерностью, соответствующей модели эмбеддингов.
6. THE RAG_Ingestion_Pipeline SHALL сохранять обновлённый FAISS-индекс и файл `chunks.json` на диск по пути `config.rag_index_dir` после каждого успешного обновления.
7. THE RAG_Ingestion_Pipeline SHALL дедуплицировать чанки перед индексацией: чанк с идентичным текстом не добавляется повторно.

---

### Требование 6: FastAPI-эндпоинты управления RAG-индексацией

**User Story:** Как администратор системы, я хочу иметь возможность запускать
и контролировать процесс RAG-индексации из истории чатов через HTTP-эндпоинты,
чтобы управлять базой знаний без перезапуска сервера.

#### Критерии приёмки

1. WHEN клиент отправляет `POST /api/v1/rag/ingest/chat-history`, THE RAG_API SHALL запускать RAG_Ingestion_Pipeline асинхронно и возвращать `{"task_id": "<uuid>", "status": "started"}` с кодом HTTP 202.
2. WHEN клиент отправляет `GET /api/v1/rag/ingest/status/{task_id}`, THE RAG_API SHALL возвращать текущий статус задачи: `status` (`running` | `completed` | `failed`), `chunks_added`, `duration_seconds`, `error` (если применимо).
3. WHEN клиент отправляет `POST /api/v1/rag/ingest/chat-history` с параметром `session_ids: list[str]`, THE RAG_API SHALL индексировать только указанные сессии.
4. WHEN клиент отправляет `POST /api/v1/rag/ingest/chat-history` с параметром `since_timestamp: int`, THE RAG_API SHALL индексировать только сообщения, созданные после указанной временной метки Unix.
5. IF RAG_Ingestion_Pipeline завершается с ошибкой, THEN THE RAG_API SHALL записывать полный стек ошибки в лог и возвращать статус `failed` с описанием ошибки в поле `error`.
6. THE RAG_API SHALL возвращать код HTTP 409, если задача индексации уже выполняется в момент нового запроса `POST /api/v1/rag/ingest/chat-history`.

---

### Требование 7: Обновление конфигурации

**User Story:** Как разработчик, я хочу, чтобы все параметры новой функциональности
управлялись через `config.json`, чтобы не требовалось изменять код для настройки.

#### Критерии приёмки

1. THE Config SHALL читать параметр `chat_history.db_path` из `config.json` со значением по умолчанию `~/.ai_assist/chat_history.db`.
2. THE Config SHALL читать параметр `chat_history.retention_days` из `config.json` со значением по умолчанию `90`.
3. THE Config SHALL читать параметр `chat_history.max_sessions` из `config.json` со значением по умолчанию `10000`.
4. THE Config SHALL читать параметр `chat_history.rag_auto_ingest` из `config.json` со значением по умолчанию `false`.
5. WHEN параметр `chat_history.rag_auto_ingest` равен `true`, THE Chat_API SHALL автоматически запускать RAG_Ingestion_Pipeline после каждого завершения сессии (при вызове `DELETE /api/v1/chat/db/session/{session_id}` или явного закрытия сессии).

---

### Требование 8: Документация

**User Story:** Как разработчик, я хочу, чтобы новая функциональность была
задокументирована в MkDocs и через docstring, чтобы другие разработчики
могли быстро разобраться в коде.

#### Критерии приёмки

1. THE Chat_DB SHALL содержать docstring в формате Google Style для каждого публичного метода с описанием аргументов, возвращаемых значений и исключений.
2. THE RAG_Ingestion_Pipeline SHALL содержать docstring в формате Google Style для каждого публичного метода.
3. THE Chat_API SHALL содержать docstring для каждого эндпоинта с описанием параметров запроса, кодов ответа и примеров.
4. THE RAG_API SHALL содержать docstring для каждого эндпоинта с описанием параметров запроса, кодов ответа и примеров.
5. WHEN в директории `docs/ru/` существует файл `chat-history-db.md`, THE Chat_DB SHALL быть описан в нём с разделами: «Архитектура», «Конфигурация», «API-эндпоинты», «Примеры использования».

---

### Требование 9: Тестирование

**User Story:** Как разработчик, я хочу иметь автоматические тесты для новой
функциональности, чтобы регрессии обнаруживались до деплоя.

#### Критерии приёмки

1. THE Chat_DB SHALL быть покрыт юнит-тестами, проверяющими: создание таблиц, сохранение сессии, сохранение сообщения, получение истории, удаление сессии с каскадным удалением сообщений.
2. THE RAG_Ingestion_Pipeline SHALL быть покрыт юнит-тестами с мок-объектами для FAISS и `SentenceTransformer`, проверяющими: формирование чанков, дедупликацию, разбивку длинных чанков.
3. THE Chat_API SHALL быть покрыт интеграционными тестами через `httpx.AsyncClient` с in-memory SQLite базой данных (`:memory:`).
4. THE RAG_API SHALL быть покрыт интеграционными тестами, проверяющими: запуск задачи, получение статуса, обработку конфликта (HTTP 409).
5. FOR ALL валидных объектов `MessageRecord`, сериализация в JSON и десериализация обратно SHALL производить эквивалентный объект (round-trip свойство).
6. FOR ALL наборов сообщений сессии, сохранение в Chat_DB и последующее чтение SHALL возвращать сообщения в том же порядке и с теми же значениями полей (round-trip свойство).
7. FOR ALL входных строк `content` длиной от 1 до 10 000 символов, RAG_Ingestion_Pipeline SHALL формировать хотя бы один чанк (свойство полноты).
8. THE Pydantic_Schema SHALL быть покрыта тестами на граничные значения: пустой `content`, неверный `role`, неверный формат `session_id`.

---

### Требование 10: Обновление версии

**User Story:** Как пользователь, я хочу видеть актуальную версию в заголовках
файлов и в `CHANGELOG.md`, чтобы понимать, какие изменения были внесены.

#### Критерии приёмки

1. THE Chat_DB SHALL содержать в заголовке файла строку `Version: 0.8.0`.
2. THE RAG_Ingestion_Pipeline SHALL содержать в заголовке файла строку `Version: 0.8.0`.
3. THE Chat_API SHALL содержать в заголовке файла строку `Version: 0.8.0`.
4. WHEN файл `CHANGELOG.md` существует, THE Chat_DB SHALL быть упомянут в разделе `## [0.8.0]` с описанием добавленной функциональности.
