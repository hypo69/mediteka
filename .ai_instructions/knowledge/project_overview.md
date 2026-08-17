# Обновленное описание проекта mediteka для AI-модели (август 2026)

## Общее назначение

**mediteka** — полноценная AI-платформа для управления медиатекой с расширяемой архитектурой плагинов, поддержкой FastAPI и множеством интерфейсов.

**Основные функции:**
1. 🤖 **AI-ассистент** — интегрированные Google Gemini и Microsoft AI Foundry
2. 🎬 **Умный медиаплеер** — синхронизированный плеер с WebSocket управлением
3. 📡 **Дистанционное управление** — голосовой пульт ДУ с TTS/STT
4. 📱 **Telegram Mini App** — удалённый доступ из Telegram
5. 🧠 **RAG-поиск** — семантический поиск по медиатеке с функцией Function Calling
6. 🧩 **Плагинная архитектура** — 10 модульных плагинов для разных задач
7. 📁 **Полный цикл медиа** — от поиска торрентов до автоматической организации

---

## Обновленная архитектура системы

```
┌────────────────────────────────────────────────────────────────────────────┐
│                         Web Interface Layer                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  User Player │  │ Remote Control│ │  Telegram    │  │  Admin Panel │  │
│  │  (video +    │  │  (voice + TTS)│ │  Mini App    │  │  (tabs)      │  │
│  │   chat)      │  │               │  │               │  │              │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │
│         │                 │                 │                 │          │
│         └─────────────────┴─────────────────┴─────────────────┘          │
│                           │                                               │
│                  ┌────────▼────────┐                                      │
│                  │   FastAPI Server│                                      │
│                  │   (FastAPI +    │                                      │
│                  │    Websocket)   │                                      │
│                  └────────┬────────┘                                      │
│                           │                                               │
│    ┌──────────────────────┼──────────────────────┐                       │
│    │                      │                      │                       │
│┌───▼────┐           ┌────▼──────┐          ┌───▼────┐                  │
││  AI    │           │  Media    │          │ Torrent│                  │
││Gemini/ │           │ Organizer │          │QBittorrent│              │
││Foundry │           └───────────┘          └──────────┘                  │
│└────────┘                  │                      │                       │
│    │              ┌──────▼───────┐               │                       │
│    │              │  RAG Index   │               │                       │
│    │              │  (SQLite +   │               │                       │
│    │              │   Embeddings)│               │                       │
│    │              └──────────────┘               │                       │
│    │                      │                      │                       │
│    │              ┌──────▼───────┐               │                       │
│    │              │  Media DB    │               │                       │
│    │              │  (SQLite)    │               │                       │
│    │              └──────────────┘               │                       │
│    │                                             │                       │
│    └─────────────────────────────────────────────┘                       │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## Ключевые компоненты 2026

### 1. FastAPI Backend (`src/fastapi/`)
Обновленная маршрутизация с 9 роутерами:

| Модуль | Описание | Эндпоинты |
|--------|----------|-----------|
| `router_chat.py` | Основной чат AI | `/api/chat` (веб-сокет, SSE) |
| `router_qbittorrent.py` | Управление торрентами | `/api/torrents/`, `/api/torrents/search`, `/api/torrents/add` |
| `router_media.py` | Медиа-управление | `/api/media/`, `/api/media-admin/` (админ) |
| `router_auth.py` | Аутентификация | `/auth/google`, `/auth/logout`, `/auth/me` |
| `router_control.py` | Веб-сокет управление | WebSocket `/ws/control` |
| `router_tts.py` | Текст в речь | `/api/tts/synthesize`, `/api/tts/voices` |
| `router_logs.py` | Логирование | `/api/logs/`, `/api/logs/analyze` |
| `router_keys.py` | Управление ключами | `/api/keys/`, `/api/keys/status` |
| `router_admin.py` | Админ-панель | `/admin`, `/api/admin/` |

### 2. AI Модель (`src/ai/`)
Архитектура: Google Gemini + Microsoft AI Foundry + AGY + Ollama

| Модуль | Описание | Префикс |
|--------|----------|---------|
| `unified_chat.py` | `UnifiedChatModel` — единый интерфейс | Роутинг по префиксу |
| `foundry_chat.py` | Клиент Foundry | `foundry:` |
| `gemini/generative_ai.py` | GoogleGenerativeAI | `gemini-*` (по умолчанию) |
| `agy_chat.py` | AGY SDK (Gemini через прокси) | `agy-*` |
| `ollama_chat.py` | Ollama локальные модели | `ollama:` |

**Правила выбора модели:**
- `foundry:qwen3-one` → Microsoft AI Foundry
- `gemini-2.0-flash` → Google Gemini (по умолчанию)
- `agy-flash` → AGY SDK
- `ollama:llama3.1` → Ollama локально

### 3. Плагины 2026 (`plugins/`)
**Теперь 10 полных плагинов** (а не 5 как раньше):

| Плагин | Триггеры | Назначение | Особенности |
|--------|----------|-----------|-------------|
| `media_organizer` | — (Function Calling) | Управление медиатекой, RAG | Предоставляет Function Calling API |
| `rag` | "фильм", "сериал", "кино", "посоветуй" | Семантический поиск медиа | Интеграция с RAG, случайная "карусель" |
| `media_layer` | "фильм", "сериал" | Простой медиа-слой | Чтение из БД без сканирования |
| `web_search` | "поищи в интернете", "погугли" | Веб-поиск через Playwright | Асинхронный поиск с AI-анализом |
| `torrent_playwright` | "торрент", "скачать" | Поиск торрентов | Rutracker + NNMClub, AI фильтрация |
| `movie_search_sources` | "где посмотреть", "плеер" | Поиск источников для просмотра | Каталог streaming-сервисов |
| `qbittorrent` | "добавь торрент", "категории" | Управление qBittorrent | Категории, теги, поиск |
| `telegram_bot` | — (отдельный процесс) | Telegram Mini App | Удалённое управление |
| `user_manager_tool` | `!list_users`, `!user_activity` | Управление пользователями | SQLite users.db |
| `yt_dlp` | "скачай", "youtube", "mp3" | Скачивание видео/аудио | Поддержка yt-dlp (новый) |

**Загрузка плагинов:**
```python
# plugins/__init__.py — динамическая загрузка всех плагинов
# Отключаемые через DISABLED_PLUGINS в .env
def load_plugins(ai_model) -> dict[str, BasePlugin]
```

**Архитектура плагина:**
```python
class BasePlugin(ABC):
    name: str = 'base'
    
    async def handle(self, message: str, **kwargs) -> str:
        # Потоковый вывод через yield {"status": "...", "text": "..."}
```

---

## База данных медиатеки 2026

### Таблицы `media.db`:

1. **Основная таблица `media`:**
```sql
id, disk_name, path, title, title_ru, title_orig, year, 
main_category, country, genres, directors, cast, 
num_of_seasons, num_episodes_per_season, status, rating, 
awards, plot, atmosphere, why_watch, mood, final_verdict, 
can_stop_at, quote, facts, similar, parent_id, 
episode_scan_skipped, media_type, number
```

2. **Таблица `media_vector`:**
```sql
id, media_id, embedding
```

3. **Таблица `search_history`:**
```sql
id, query, timestamp, results_count
```

**10 Категорий по умолчанию:**
1. 🎬 Боевики
2. 😱 Триллеры  
3. 🚀 Приключения
4. 😢 Драмы
5. 👪 Семейные
6. 🏰 Исторические/Костюмированные
7. 🔍 Расследования
8. 🕵️ Шпионы
9. 🎭 Мюзиклы
10. 📹 Документальные

---

## Новый RAG-поиск (Retrieval-Augmented Generation)

**Обновлённый стек:**
1. **Gemini Embeddings API** — векторное представление
2. **SQLite + FAISS** — хранение и поиск векторов
3. **Function Calling** — интеграция с AI-моделями
4. **Streaming статусы** — отображение прогресса в UI

**Процесс RAG-поиска:**
```python
# 1. Векторизация запроса
embedding = await ai_model.embed(query)

# 2. Поиск в FAISS индексе  
results = search_faiss_index(embedding)

# 3. Function Calling в Gemini
tools = get_media_tools()  # search_media, get_media_card, get_random_media
response = await ai_model.chat(query, tools=tools)

# 4. Потоковый вывод
yield {"status": "🔍 Поиск в RAG-индексе..."}
yield {"text": "Найдены результаты..."}
```

---

## Технологический стек 2026

| Компонент | Технология | Версия |
|-----------|-----------|--------|
| Backend | Python 3.10+, FastAPI, Uvicorn | Python 3.10+ |
| AI | Google Gemini 2.0, Microsoft AI Foundry | Gemini 2.0-flash |
| Database | SQLite, FAISS | SQLite 3.45+ |
| Frontend | HTML5, CSS3, Vanilla JS | Modern Web APIs |
| Медиа | qBittorrent API, yt-dlp, TMDB API | QBittorrent 4.6+ |
| Поиск | Playwright, DuckDuckGo, Rutracker | Playwright 1.45+ |
| Голос | Silero TTS, Web Speech API | Silero v4 |
| Деплой | PowerShell scripts, SSL/TLS | Windows |

---

## Структура проекта (обновленная)

```
mediteka/
├── .ai_instructions/           # AI-инструкции (обновлены)
│   ├── knowledge/              # Знания о проекте
│   │   ├── project_overview.md # ← этот файл
│   │   ├── legacy_project_knowledge.md # ← старый обзор
│   │   └── codex/              # Инженерные правила
│   ├── prompts/                # Промпты для моделей
│   │   ├── chat/               # Инструкция чата
│   │   └── media_organizer/    # Инструкция медиатеки
│   └── plans/                  # Дорожная карта
├── plugins/                    # 10 ПЛАГИНОВ
│   ├── media_organizer/       # Управление медиатекой (+RAG)
│   ├── rag/                   # RAG-поиск (Function Calling)
│   ├── media_layer/           # Простой медиа-слой
│   ├── web_search/            # Веб-поиск через Playwright
│   ├── torrent_playwright/    # Поиск торрентов
│   ├── movie_search_sources/  # Источники для просмотра
│   ├── qbittorrent/           # Управление qBittorrent
│   ├── telegram_bot/          # Telegram Mini App
│   ├── user_manager_tool/     # Управление пользователями
│   └── yt_dlp/                # Скачивание видео/аудио ← НОВЫЙ!
├── src/
│   ├── ai/                    # AI модели (Gemini + Foundry)
│   │   ├── unified_chat.py    # UnifiedChatModel
│   │   ├── foundry_chat.py    # Microsoft AI Foundry
│   │   ├── gemini/            # Google Gemini
│   │   └── dev_rag.py         # RAG для разработки
│   ├── fastapi/               # 9 роутеров FastAPI
│   ├── logger/                # Система логирования
│   ├── user_manager/          # Управление пользователями
│   ├── tts/                   # Text-to-Speech (Silero)
│   └── utils/                 # Утилиты (jjson, file)
├── webinterface/              # 6 веб-интерфейсов
│   ├── user/                  # Пользователь (плеер+чат)
│   ├── admin/                 # Админ-панель (пароль: onela)
│   ├── rc/                    # Пульт ДУ (голос+TTS)
│   ├── tgmini/                # Telegram Mini App
│   ├── tv/                    # Телевизионный интерфейс
│   └── user_tts/              # Тестирование TTS
├── main.py                    # Точка входа (FastAPI)
├── requirements.txt           # Зависимости (с yt-dlp)
├── .env                       # Переменные окружения
├── pytest.ini                 # Конфигурация тестов
├── conftest.py                # Фикстуры pytest
└── mkdocs.yml                 # Документация MkDocs
```

---

## Ключевые файлы конфигурации

| Файл | Описание | Критичность |
|------|----------|-------------|
| `.env` | Переменные окружения (API ключи) | Критично |
| `src/fastapi/config.json` | Настройки сервера (host:0.0.0.0, port:3000) | Критично |
| `plugins/media_organizer/config.json` | Настройки медиатеки | Важно |
| `plugins/qbittorrent/config.json` | Настройки qBittorrent | Важно |
| `plugins/yt_dlp/config.json` | Настройки yt-dlp (новый) | Дополнительно |

---

## Примеры использования плагинов 2026

1. **RAG-поиск фильма:**
   ```
   "посоветуй фильм про космос"
   → Плагин: rag
   → Процесс: RAG-поиск → Function Calling → AI-рекомендация
   ```

2. **Скачивание видео:**
   ```
   "скачай https://youtube.com/watch?v=..."
   → Плагин: yt_dlp
   → Процесс: YtDlpClient → прогресс-бар → HTML-карточка результата
   ```

3. **Поиск торрента:**
   ```
   "найди торрент фильма Начало"
   → Плагин: torrent_playwright
   → Процесс: Playwright поиск → AI-фильтрация → HTML-список
   ```

4. **Веб-поиск:**
   ```
   "погугли актёров из фильма Криминальное чтиво"
   → Плагин: web_search
   → Процесс: Playwright → AI-анализ → структурированный ответ
   ```

5. **Управление торрентами:**
   ```
   "категории торрентов"
   → Плагин: qbittorrent
   → Процесс: QBittorrentClient → назначение категорий
   ```

6. **Поиск источника:**
   ```
   "где посмотреть фильм Интерстеллар"
   → Плагин: movie_search_sources
   → Процесс: Каталог streaming-сервисов → рекомендации
   ```

---

## Новые возможности 2026

### 1. **Streaming-архитектура**
- SSE (Server-Sent Events) для статусов
- WebSocket для управления плеером
- Асинхронный прогресс загрузок

### 2. **Расширенная AI-интеграция**
- Единый интерфейс UnifiedChatModel
- Авто-переключение между Gemini и Foundry
- Поддержка Function Calling во всех плагинах

### 3. **Новый плагин yt_dlp**
- Скачивание видео с YouTube и других платформ
- Конвертация в аудио (mp3)
- Поиск по YouTube через ytsearch
- Прогресс-бар и HTML-карточки

### 4. **Улучшенный RAG**
- FAISS для векторного поиска
- Function Calling для медиа-поиска
- "Карусель" случайных фильмов
- Веб-интеграция через Playwright

### 5. **Голосовой интерфейс**
- Silero TTS для русского языка
- Web Speech API для распознавания речи
- Озвучка AI-ответов на пульте ДУ

---

## Примечания для AI (важные изменения)

1. **Плагины загружаются динамически** через `plugins/__init__.py`
2. **Отключение плагинов**: переменная `DISABLED_PLUGINS` в `.env`
3. **Unified AI**: Используйте `UnifiedChatModel` из `src/ai/unified_chat.py`
4. **Потоковый вывод**: Все плагины поддерживают `yield {"status": "...", "text": "..."}`
5. **RAG-маршрут**: Медиа-запросы всегда идут через `rag` плагин
6. **Новый yt-dlp**: Добавлен как зависимость в `requirements.txt`

---

## Основные изменения с предыдущей версии

| Аспект | Было (2024) | Стало (2026) |
|--------|------------|-------------|
| Плагины | 5 | 10 |
| AI Модели | Только Gemini | Gemini + Foundry |
| Поиск | Простой RAG | RAG + Function Calling |
| Веб-поиск | Отсутствовал | Playwright + AI анализ |
| Скачивание видео | Нет | yt-dlp плагин |
| Интерфейсы | 4 | 6 (добавлены tv, user_tts) |
| Архитектура | Синхронная | Асинхронная + Streaming |
| База данных | media.db | media.db + media_vector |

---

## Быстрый старт 2026

```bash
# Установка зависимостей (теперь с yt-dlp)
pip install -r requirements.txt

# Настройка окружения
cp .env.example .env
# Отредактируйте .env: GEMINI_API_KEY_NAMES, TELEGRAM_BOT_TOKEN и др.

# Запуск сервера
python main.py

# Доступные интерфейсы:
# http://localhost:3000/user      - плеер+чат
# http://localhost:3000/rc        - пульт ДУ
# http://localhost:3000/tgmini    - Telegram Mini App
# http://localhost:3000/admin     - админка (пароль: onela)
```

---

**Последнее обновление: август 2026**  
*Актуализировано после добавления yt_dlp плагина и расширения архитектуры до 10 плагинов.*
