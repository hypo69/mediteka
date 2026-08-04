# Recommender Agent

Персональная рекомендательная система на основе истории просмотров браузера.

---

## Архитектура

```
Browser Extension (content.js)
  │  pagehide → time_spent, url, title
  ▼
background.js
  │  POST /api/v1/recommender/track
  ▼
RecommenderAgent (src/agents/recommender_agent.py)
  ├─ analyze_interests   → AI анализирует топики из истории
  └─ generate_recommendations → AI формирует рекомендации
  ▼
GET /api/v1/recommender/recommendations → ответ пользователю
```

---

## Как это работает

1. **Браузерное расширение** (`content.js`) измеряет время на каждой странице.
2. При уходе со страницы (`pagehide`) отправляет событие в `background.js`.
3. `background.js` пересылает событие на сервер: `POST /api/v1/recommender/track`.
4. Сервер накапливает историю в памяти (по `user_id`).
5. Пользователь нажимает **Get Recommendations** в popup расширения.
6. `RecommenderAgent` запускает AI-цикл:
   - вызывает `analyze_interests` → получает топ страниц из истории
   - вызывает `generate_recommendations` → AI формирует список рекомендаций
7. Результат отображается в popup.

---

## API Endpoints

### `POST /api/v1/recommender/track`

Принять событие просмотра страницы от расширения.

**Body:**
```json
{
  "user_id": "user_abc123",
  "url": "https://example.com/article",
  "title": "Article Title",
  "time_spent": 120,
  "timestamp": "2025-01-01T12:00:00Z"
}
```

**Response:**
```json
{"success": true, "total_views": 42}
```

---

### `POST /api/v1/recommender/recommendations`

Получить AI-рекомендации на основе истории просмотров.

**Body:**
```json
{
  "user_id": "user_abc123",
  "model": "foundry::qwen3-0.6b",
  "top_k": 5
}
```

**Response:**
```json
{
  "success": true,
  "answer": "Based on your browsing history...",
  "tool_calls": [...],
  "iterations": 2
}
```

---

### `GET /api/v1/recommender/history?user_id=...&min_time=10`

Получить историю просмотров пользователя.

**Response:**
```json
{
  "success": true,
  "user_id": "user_abc123",
  "views": [
    {"url": "...", "title": "...", "time_spent": 120, "timestamp": "..."}
  ],
  "count": 15
}
```

---

## Установка расширения

1. Открыть `chrome://extensions/`
2. Включить **Developer mode**
3. Нажать **Load unpacked**
4. Выбрать папку `extensions/browser-extension-recommender/`

---

## Конфигурация

В popup расширения можно изменить URL сервера (по умолчанию `http://localhost:9696`).

Для корпоративного развёртывания укажите адрес внутреннего сервера.

---

## Хранение данных

- История просмотров хранится **в памяти сервера** (не на диске).
- Данные сбрасываются при перезапуске сервера.
- Хранятся только страницы, на которых пользователь провёл ≥ 10 секунд.
- Автоматическая очистка событий старше 30 дней.

!!! note "Production"
    Для продакшена замените `_page_views` dict в `recommender_agent.py`
    на Redis или SQLite.

---

## Файлы

| Файл | Назначение |
|---|---|
| `src/agents/recommender_agent.py` | Серверный агент (AI-цикл + хранилище) |
| `src/api/endpoints/recommender.py` | FastAPI роутер |
| `extensions/browser-extension-recommender/manifest.json` | Манифест расширения |
| `extensions/browser-extension-recommender/content.js` | Трекер времени на странице |
| `extensions/browser-extension-recommender/background.js` | Service worker, отправка на сервер |
| `extensions/browser-extension-recommender/popup.html` | UI расширения |
| `extensions/browser-extension-recommender/popup.js` | Логика popup |
