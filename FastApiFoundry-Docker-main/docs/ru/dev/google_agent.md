# Google Agent — Gmail, Calendar, Sheets, Docs

**Версия:** 0.7.1

Google Agent позволяет AI-модели работать с сервисами Google Workspace:
читать и отправлять письма, управлять календарём, читать и записывать данные в таблицы,
работать с документами. Авторизация — через OAuth2, данные не покидают вашу машину.

---

## Как это работает

```
Пользователь → POST /api/v1/agent/run (agent: "google")
                        │
                   GoogleAgent.run()
                        │
              Foundry / Ollama (function calling)
                        │
              model выбирает tool_call
                        │
         GoogleAgent._execute_tool("gmail_list", args)
                        │
              Google API (OAuth2, HTTPS)
                        │
                   результат → модель
                        │
              модель формирует финальный ответ
                        │
                   Пользователь
```

Агент сам решает, какие инструменты вызвать и в каком порядке.
Один запрос «Покажи непрочитанные письма и создай встречу на завтра» может
породить несколько последовательных tool_call: `gmail_list` → `calendar_create`.

---

## Настройка (одноразово)

### Шаг 1 — Установить зависимости

```powershell
venv\Scripts\pip install -r requirements-google.txt
```

Файл `requirements-google.txt` в корне проекта:

```
google-auth>=2.23.0
google-auth-oauthlib>=1.1.0
google-auth-httplib2>=0.1.1
google-api-python-client>=2.100.0
```

---

### Шаг 2 — Создать проект в Google Cloud Console

1. Открыть [https://console.cloud.google.com/](https://console.cloud.google.com/)
2. Создать новый проект (или выбрать существующий)
3. Перейти в **APIs & Services → Library**
4. Включить следующие API (поиск по названию, кнопка **Enable**):

| API | Для чего |
|---|---|
| Gmail API | Чтение и отправка писем |
| Google Calendar API | Просмотр и создание событий |
| Google Sheets API | Чтение и запись таблиц |
| Google Docs API | Чтение и редактирование документов |

---

### Шаг 3 — Создать OAuth2 credentials

1. Перейти в **APIs & Services → Credentials**
2. Нажать **Create Credentials → OAuth 2.0 Client ID**
3. Тип приложения: **Desktop app**
4. Дать любое имя, нажать **Create**
5. Нажать **Download JSON** → сохранить файл как `credentials.json` в корень проекта

```
FastApiFoundry-Docker/
├── credentials.json   ← сюда
├── config.json
├── run.py
└── ...
```

!!! warning "Не коммитьте credentials.json"
    Добавьте в `.gitignore`:
    ```
    credentials.json
    token.json
    ```

---

### Шаг 4 — Настроить OAuth Consent Screen

1. Перейти в **APIs & Services → OAuth consent screen**
2. Тип: **External** (или Internal для корпоративного Google Workspace)
3. Заполнить обязательные поля: App name, User support email, Developer email
4. На шаге **Scopes** — можно пропустить (scopes задаются в коде)
5. На шаге **Test users** — добавить свой Google-аккаунт

!!! note "Статус приложения"
    Пока приложение в статусе **Testing**, авторизоваться могут только пользователи
    из списка Test users. Для личного использования этого достаточно.

---

### Шаг 5 — Первый запуск (авторизация)

При первом обращении к Google Agent сервер автоматически откроет браузер
для авторизации через Google:

```
Запустите сервер:
  venv\Scripts\python.exe run.py

Отправьте любой запрос к Google Agent:
  POST /api/v1/agent/run
  {"agent": "google", "message": "покажи мои письма", "model": "ollama::llama3"}

В браузере откроется страница Google → выберите аккаунт → разрешите доступ
```

После успешной авторизации в корне проекта появится `token.json`.
При следующих запросах браузер открываться не будет — токен обновляется автоматически.

```
FastApiFoundry-Docker/
├── credentials.json   ← OAuth2 client (не менять)
├── token.json         ← токен доступа (создаётся автоматически)
```

---

## Быстрый старт

### Прочитать непрочитанные письма

```bash
POST /api/v1/agent/run
Content-Type: application/json

{
  "agent": "google",
  "message": "Покажи мои непрочитанные письма",
  "model": "ollama::llama3"
}
```

Ответ:

```json
{
  "success": true,
  "answer": "У вас 3 непрочитанных письма:\n1. От: boss@company.com — Тема: Встреча в пятницу...",
  "tool_calls": [
    {
      "tool": "gmail_list",
      "arguments": {"query": "is:unread", "max_results": 10},
      "result": "ID: 18f3a...\n  От: boss@company.com\n  Тема: Встреча в пятницу\n  Дата: Mon, 9 Dec 2025"
    }
  ],
  "iterations": 2,
  "agent": "google"
}
```

---

### Отправить письмо

```json
{
  "agent": "google",
  "message": "Отправь письмо на ivan@example.com с темой 'Привет' и текстом 'Как дела?'",
  "model": "ollama::llama3"
}
```

---

### Создать событие в календаре

```json
{
  "agent": "google",
  "message": "Создай встречу 'Планёрка' завтра с 10:00 до 11:00",
  "model": "ollama::llama3"
}
```

---

### Прочитать данные из таблицы

```json
{
  "agent": "google",
  "message": "Прочитай данные из таблицы 1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms диапазон Sheet1!A1:D5",
  "model": "ollama::llama3"
}
```

---

### Комплексный запрос

```json
{
  "agent": "google",
  "message": "Проверь непрочитанные письма от boss@company.com, прочитай последнее и создай событие в календаре на основе его содержимого",
  "model": "ollama::llama3",
  "max_iterations": 8
}
```

---

## Инструменты агента

### Gmail

#### `gmail_list` — список писем

| Параметр | Тип | Обязательный | Описание |
|---|---|---|---|
| `query` | string | нет | Поисковый запрос Gmail |
| `max_results` | integer | нет | Максимум писем (по умолчанию 10) |

Примеры запросов Gmail:

| Запрос | Что ищет |
|---|---|
| `is:unread` | Непрочитанные |
| `from:boss@company.com` | От конкретного отправителя |
| `subject:отчёт` | По теме |
| `after:2025/12/01` | После даты |
| `has:attachment` | С вложениями |
| `is:unread from:boss@company.com` | Комбинация |

---

#### `gmail_read` — прочитать письмо

| Параметр | Тип | Обязательный | Описание |
|---|---|---|---|
| `message_id` | string | да | ID письма из `gmail_list` |

Возвращает: отправитель, получатель, тема, дата, текст письма (до 3000 символов).

---

#### `gmail_send` — отправить письмо

| Параметр | Тип | Обязательный | Описание |
|---|---|---|---|
| `to` | string | да | Email получателя |
| `subject` | string | да | Тема письма |
| `body` | string | да | Текст письма |

---

### Google Calendar

#### `calendar_list` — список событий

| Параметр | Тип | Обязательный | Описание |
|---|---|---|---|
| `max_results` | integer | нет | Максимум событий (по умолчанию 10) |
| `time_min` | string | нет | Начало диапазона ISO8601 (по умолчанию — сейчас) |

Возвращает список предстоящих событий с датой, временем и ID.

---

#### `calendar_create` — создать событие

| Параметр | Тип | Обязательный | Описание |
|---|---|---|---|
| `title` | string | да | Название события |
| `start` | string | да | Начало ISO8601: `2025-12-25T10:00:00` |
| `end` | string | да | Конец ISO8601: `2025-12-25T11:00:00` |
| `description` | string | нет | Описание события |
| `attendees` | array | нет | Список email участников |

!!! note "Формат времени"
    Используйте ISO8601 с указанием часового пояса или без него (тогда UTC).
    Пример: `2025-12-25T10:00:00+03:00` для Москвы.

---

### Google Sheets

#### `sheets_read` — прочитать данные

| Параметр | Тип | Обязательный | Описание |
|---|---|---|---|
| `spreadsheet_id` | string | да | ID таблицы из URL |
| `range` | string | да | Диапазон ячеек |

Как найти ID таблицы в URL:
```
https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms/edit
                                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                                       это и есть spreadsheet_id
```

Примеры диапазонов:

| Диапазон | Что читает |
|---|---|
| `Sheet1!A1:D10` | Ячейки A1–D10 на листе Sheet1 |
| `A:A` | Весь столбец A |
| `1:1` | Вся первая строка |
| `Sheet2!B2:F20` | Диапазон на другом листе |

---

#### `sheets_write` — записать данные

| Параметр | Тип | Обязательный | Описание |
|---|---|---|---|
| `spreadsheet_id` | string | да | ID таблицы |
| `range` | string | да | Начальная ячейка или диапазон |
| `values` | array | да | Двумерный массив значений |

Пример `values`:
```json
[
  ["Имя", "Возраст", "Город"],
  ["Иван", 30, "Москва"],
  ["Мария", 25, "СПб"]
]
```

---

### Google Docs

#### `docs_read` — прочитать документ

| Параметр | Тип | Обязательный | Описание |
|---|---|---|---|
| `document_id` | string | да | ID документа из URL |

Как найти ID документа:
```
https://docs.google.com/document/d/1aBcDeFgHiJkLmNoPqRsTuVwXyZ/edit
                                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^
                                   это document_id
```

Возвращает текст документа (до 5000 символов).

---

#### `docs_append` — добавить текст

| Параметр | Тип | Обязательный | Описание |
|---|---|---|---|
| `document_id` | string | да | ID документа |
| `text` | string | да | Текст для добавления в конец документа |

---

## API Reference

### `POST /api/v1/agent/run`

| Поле | Тип | По умолчанию | Описание |
|---|---|---|---|
| `message` | string | — | Запрос пользователя |
| `agent` | string | `"powershell"` | Укажите `"google"` |
| `model` | string | из config.json | ID модели (должна поддерживать function calling) |
| `temperature` | float | `0.7` | Температура генерации |
| `max_tokens` | int | `2048` | Максимум токенов |
| `max_iterations` | int | `5` | Максимум итераций tool-call |

### `GET /api/v1/agent/google/tools`

Список всех инструментов Google Agent.

### `GET /api/v1/agent/list`

Все зарегистрированные агенты, включая `google`.

---

## Выбор модели

Google Agent требует модели с поддержкой **function calling**.

| Модель | Поддержка tools | Рекомендация |
|---|---|---|
| `ollama::llama3` | ✅ | Хороший баланс скорости и качества |
| `ollama::qwen2.5:7b` | ✅ | Отлично понимает задачи с инструментами |
| `ollama::mistral` | ✅ | Быстрый, хорошо следует инструкциям |
| `foundry::qwen3-0.6b-generic-cpu:4` | ✅ | Минимальные требования к железу |
| `hf::microsoft/phi-2` | ⚠️ | Ограниченная поддержка tools |

!!! tip "Рекомендация"
    Для задач с Google Workspace лучше использовать модели 7B+.
    Маленькие модели (0.5–1.5B) могут неточно формировать аргументы инструментов.

---

## Архитектура

```
src/agents/google_agent.py       — GoogleAgent (BaseAgent)
  ├── _gmail_list()              — gmail.users.messages.list
  ├── _gmail_read()              — gmail.users.messages.get
  ├── _gmail_send()              — gmail.users.messages.send
  ├── _calendar_list()           — calendar.events.list
  ├── _calendar_create()         — calendar.events.insert
  ├── _sheets_read()             — sheets.spreadsheets.values.get
  ├── _sheets_write()            — sheets.spreadsheets.values.update
  ├── _docs_read()               — docs.documents.get
  └── _docs_append()             — docs.documents.batchUpdate

credentials.json                 — OAuth2 client secrets (не коммитить!)
token.json                       — OAuth2 access token (создаётся автоматически)
requirements-google.txt          — зависимости
```

---

## Безопасность

- Все данные передаются напрямую между вашим компьютером и Google API по HTTPS
- AI-модель работает локально и не видит ваши Google-данные напрямую — только результаты tool_call
- `credentials.json` и `token.json` хранятся только локально
- Токен обновляется автоматически через `google-auth`

!!! danger "Никогда не публикуйте credentials.json"
    Этот файл даёт доступ к вашему Google-аккаунту.
    Добавьте в `.gitignore`:
    ```
    credentials.json
    token.json
    ```

---

## Устранение неполадок

### `credentials.json not found`

Файл не найден в корне проекта. Скачайте его из Google Cloud Console
(APIs & Services → Credentials → ваш OAuth2 client → Download JSON)
и сохраните как `credentials.json` в корень проекта.

---

### `Access blocked: This app's request is invalid`

OAuth Consent Screen не настроен или приложение не прошло верификацию.
Для личного использования: добавьте свой email в **Test users** на странице
OAuth consent screen.

---

### `google-api-python-client not installed`

```powershell
venv\Scripts\pip install -r requirements-google.txt
```

---

### `Token has been expired or revoked`

Удалите `token.json` и повторите авторизацию:

```powershell
del token.json
```

При следующем запросе к агенту браузер откроется снова.

---

### Модель не вызывает инструменты

Убедитесь, что используемая модель поддерживает function calling.
Попробуйте `ollama::qwen2.5:7b` или `ollama::llama3`.
Увеличьте `max_iterations` до 8–10 для сложных задач.
