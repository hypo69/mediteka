# Полное описание проекта gemini-simplechat для AI-модели

## Общее назначение

**gemini-simplechat** — интеллектуальная медиа-платформа с веб-интерфейсом, чат-ботом на Google Gemini и системой управления медиатекой.

**Три основные функции:**
1. AI Ассистент — Google Gemini для чатов, рекомендаций и классификации медиа
2. Умный медиаплеер — воспроизведение файлов с синхронизацией между устройствами
3. Система управления медиатекой — сканирование, классификация и организация фильмов/сериалов

---

## Архитектура системы

```
┌────────────────────────────────────────────────────────────────────────────┐
│                         Web Interface Layer                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │  User Player │  │ Remote Control│ │  Telegram    │  │  Admin Panel │    │
│  │  (video +    │  │  (voice + TTS)│ │  Mini App    │  │  (tabs)      │    │
│  │   chat)      │  │               │  │               │  │              │    │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘    │
│         │                 │                 │                 │             │
│         └─────────────────┴─────────────────┴─────────────────┘             │
│                           │                                                 │
│                  ┌────────▼────────┐                                        │
│                  │   FastAPI Server│                                        │
│                  └────────┬────────┘                                        │
│                           │                                                 │
│    ┌──────────────────────┼──────────────────────┐                         │
│    │                      │                      │                         │
│┌───▼────┐           ┌────▼──────┐          ┌───▼────┐                     │
││  AI    │           │  Media    │          │ Torrent│                     │
││ Gemini │           │ Organizer │          │QBittorrent│                 │
│└────────┘           └───────────┘          └──────────┘                     │
│    │                      │                      │                         │
│    │              ┌──────▼───────┐               │                         │
│    │              │  RAG Index   │               │                         │
│    │              │  (SQLite +   │               │                         │
│    │              │   Embeddings)│               │                         │
│    │              └──────────────┘               │                         │
│    │                      │                      │                         │
│    │              ┌──────▼───────┐               │                         │
│    │              │  Media DB    │               │                         │
│    │              │  (SQLite)    │               │                         │
│    │              └──────────────┘               │                         │
│    │                                             │                         │
│    └─────────────────────────────────────────────┘                         │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## Ключевые компоненты

### 1. FastAPI Backend (`src/fastapi/`)

| Модуль | Описание |
|--------|----------|
| `router_chat.py` | Эндпоинт `/api/chat` для обработки сообщений через плагины и AI |
| `router_media.py` | `/api/media` — сканирование, аудит, поиск медиа, стриминг файлов |
| `router_qbittorrent.py` | `/api/torrents` — управление торрентами через qBittorrent API |
| `router_auth.py` | `/auth` — Google OAuth и JWT токены |
| `config.json` | Конфигурация сервера (host, port, SSL) |

### 2. AI Модель (`src/ai/`)

| Модуль | Описание |
|--------|----------|
| `gemini/generative_ai.py` | Класс `GoogleGenerativeAI` для взаимодействия с Gemini |
| `gemini/rag.py` | Класс `GeminiRAG` — векторный поиск через Gemini Embeddings API |
| `foundry_chat.py` | Базовый класс для локальных Foundry моделей (qwen3) |
| `clients/foundry.py` | Клиент для Microsoft AI Foundry API |

### 3. Медиатека (`plugins/media_organizer/`)

| Модуль | Описание |
|--------|----------|
| `core/database.py` | Класс `MediaDatabase` — управление SQLite `media.db` |
| `core/media_scanner.py` | `TMDBClient`, `MediaScanner` — сканирование файлов и TMDB API |
| `core/genre_classifier.py` | `PersistentGenreClassifier` — классификация жанров через Gemini |
| `core/media_auditor.py` | `MediaAuditor` — проверка целостности данных |
| `core/media_organizer.py` | Плагин для чата (`MediaOrganizerPlugin`) |
| `core/media_rag.py` | RAG-индексация медиатеки для семантического поиска |
| `core/series_collector.py` | Сбор и анализ эпизодов сериалов |
| `core/report_generator.py` | Экспорт данных в JSON и Markdown |
| `core/media_rebuild.py` | Консолидация дубликатов в БД |

### 4. Плагины (`plugins/`)

| Плагин | Назначение |
|--------|-----------|
| `media_layer` | Простой слой для медиа-запросов (чтение из БД без сканирования) |
| `media_organizer` | Полное управление медиатекой (сканирование, классификация, отчёты) |
| `qbittorrent` | Интеграция с qBittorrent для управления загрузками |
| `telegram_bot` | Telegram Mini App для удалённого управления |
| `torrent_playwright` | Автоматическое полу��ение торрентов |

---

## Основные процессы

### 1. Сканирование медиатеки

```
Запуск (через чат или API)
    ↓
TMDBClient + MediaScanner — базовое сканирование
    ↓
PersistentGenreClassifier — классификация через Gemini
    ↓
MediaDatabase — сохранение в SQLite
    ↓
MediaAuditor — проверка целостности
    ↓
Генерация отчётов (JSON + Markdown)
    ↓
Поиск торрентов и назначение категорий
```

### 2. Обработка сообщения в чате

```
Пользователь отправляет сообщение
    ↓
POST /api/chat
    ↓
router_chat.py перебирает плагины
    ↓
Первый плагин с ответом обрабатывает запрос
    ↓
Если ни один плагин не подошёл — обращение к AI
    ↓
GoogleGenerativeAI.chat() с ротацией ключей
    ↓
StreamingResponse с посимвольным выводом
```

### 3. RAG поиск по медиатеке

```
Пользователь ищет фильм по описанию
    ↓
GeminiRAG.embed() — векторизация через Gemini Embedding API
    ↓
Поиск cosine similarity в SQLite
    ↓
Возврат топ-K наиболее релевантных записей
```

---

## База данных SQLite (media.db)

**Структура таблицы `media`:**

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | INTEGER | Первичный ключ |
| `disk_name` | TEXT | Имя диска (например, "ДИСК 1") |
| `path` | TEXT | Полный путь к файлу/папке |
| `title` | TEXT | Название медиа |
| `title_orig` | TEXT | Оригинальное название |
| `title_ru` | TEXT | Русское название |
| `year` | INTEGER | Год выпуска |
| `main_category` | TEXT | Категория (10 категорий по умолчанию) |
| `country` | TEXT | Страна |
| `genres` | TEXT | JSON-массив жанров |
| `directors` | TEXT | JSON-массив режиссёров |
| `cast` | TEXT | JSON-массив актёров (до 5) |
| `num_of_seasons` | INTEGER | Количество сезонов (для сериалов) |
| `num_episodes_per_season` | TEXT | JSON-массив количества серий |
| `status` | TEXT | Статус сериала ("завершён"/"продолжается"/"отменён") |
| `rating` | TEXT | JSON-объект с оценками (IMDb, TMDB) |
| `awards` | TEXT | JSON-массив наград |
| `plot` | TEXT | Сюжет (100-150 слов) |
| `atmosphere` | TEXT | Атмосфера (~15 слов) |
| `why_watch` | TEXT | Почему стоит смотреть |
| `mood` | TEXT | Настроение для просмотра |
| `final_verdict` | TEXT | Финальный вердикт |
| `can_stop_at` | TEXT | Можно остановиться после (сезон) |
| `quote` | TEXT | Культовая цитата |
| `facts` | TEXT | JSON-массив интересных фактов |
| `similar` | TEXT | JSON-массив похожих медиа |
| `parent_id` | INTEGER | ID родительского элемента |
| `episode_scan_skipped` | INTEGER | 1 если сканирование эпизодов пропущено |
| `media_type` | TEXT | Тип: `movie`, `series`, `season`, `episode` |
| `number` | INTEGER | Порядковый номер |

**Иерархия:**
- `episode → season → serial`
- Для `season`: `parent_id` указывает на ID сериала
- Для `episode`: `parent_id` указывает на ID сезона
- Для `movie` и `series`: `parent_id` = 0

**10 Категорий по умолчанию:**
1. Боевики
2. Триллеры
3. Приключения
4. Драмы
5. Семейные
6. Исторические/Костюмированные
7. Расследования
8. Шпионы
9. Мюзиклы
10. Документальные

---

## Ключевые файлы конфигурации

| Файл | Описание |
|------|----------|
| `.env` | Переменные окружения (API ключи, пути) |
| `src/fastapi/config.json` | Настройки сервера (host, port, SSL) |
| `src/secrets/gemini_keys.json` | API ключи Gemini и статусы |
| `src/secrets/api_key_state.py` | Менеджер API ключей с ротацией |
| `plugins/media_organizer/config/media_paths.txt` | Пути к медиафайлам |
| `plugins/media_organizer/config/torrents_names.json.md` | Список торрентов |

---

## AI и RAG

### Google Generative AI

**Класс:** `GoogleGenerativeAI` (`src/ai/gemini/generative_ai.py`)

**Особенности:**
- Автоматическая ротация API ключей (из `gemini_keys.json`)
- Обработка ошибок 429 (лимит запросов) — переключение на следующий ключ
- Управление историей чата с сохранением
- Поддержка нескольких моделей (gemini-2.0-flash-exp и другие)
- Внешние промпты из файлов

### RAG (Retrieval-Augmented Generation)

**Класс:** `GeminiRAG` (`src/ai/gemini/rag.py`)

**Особенности:**
- Векторизация через Gemini Embedding API (gemini-embedding-2)
- Хранение в SQLite с векторным поиском через numpy
- Автоматическая обработка лимитов и переключение ключей
- Пакетная обработка документов (batch_size=50)

---

## Веб-интерфейсы

| Интерфейс | URL | Описание |
|-----------|-----|----------|
| Плеер | `/user` | Основной интерфейс (чат + плеер) |
| Пульт ДУ | `/rc` | Управление голосом + TTS |
| Telegram | `/tgmini` | Telegram Mini App |
| Админка | `/admin` | Управление медиатекой |

---

## Плагины — расширяемая архитектура

Все плагины наследуются от `BasePlugin` и реализуют метод `handle(message)`:

```python
from plugins.plugin import BasePlugin

class MyPlugin(BasePlugin):
    name = "my_plugin"
    
    async def _handle(self, message: str) -> str:
        # Обработка логики
        return "Ответ"
```

**Список плагинов:**

| Плагин | Триггеры | Назначение |
|--------|----------|-----------|
| `media_layer` | "фильм", "сериал", "кино", "рекомендуй" | Простой ответ из БД без сканирования |
| `media_organizer` | "скан", "scan", "отчет", "ревизи", "rebuild" | Полное управление медиатекой |
| `qbittorrent` | "торрент", "добавь", "поиск" | Управление торрентами |

---

## Примеры использования

1. **Сканирование диска:**
   ```
   "скан диск 1" — запуск сканирования диска 1
   ```

2. **Поиск медиа:**
   ```
   "найди фильм про космос" — семантический пои��к через RAG
   ```

3. **Рекомендации:**
   ```
   "похожие фильмы на Титаник" — поиск похожих по сюжету
   ```

4. **Управление торрентами:**
   ```
   "добавь торрент файл" — интеграция с qBittorrent
   ```

5. **Аудит:**
   ```
   "ревизия медиатеки" — проверка целостности данных
   ```

---

## Технологический стек

| Компонент | Технология |
|-----------|-----------|
| Backend | Python 3.10+, FastAPI, Uvicorn |
| AI | Google Gemini (gemini-2.0-flash-exp), Foundry (qwen3) |
| Database | SQLite (media.db, media_rag.db, users.db) |
| Frontend | HTML5, CSS3, JavaScript (Vanilla) |
| Media | qBittorrent, TMDB API, MPV/VLC (встроенный плеер) |
| Auth | Google OAuth 2.0, JWT |
| Deployment | PowerShell скрипты, SSL сертификаты |

---

## Структура проекта

```
gemini-simplechat/
├── .ai_instructions/           # Инструкции для AI
│   ├── prompts/               # Системные инструкции
│   │   ├── chat/              # Инструкция для чата
│   │   └── media_organizer/   # Инструкция для медиатеки
│   ├── rules/                 # Инженерные правила
│   └── plans/                 # Планы развития
├── .mcp/                       # MCP серверы
├── plugins/                    # Плагины
│   ├── media_organizer/       # Управление медиатекой
│   ├── qbittorrent/           # Интеграция с qBittorrent
│   ├── media_layer/           # Слой медиа-запросов
│   ├── telegram_bot/          # Telegram бот
│   ├── rag/                   # RAG индекс
│   └── torrent_playwright/    # Получение торрентов
├── src/
│   ├── ai/                    # AI модели
│   │   ├── gemini/           # Google Gemini
│   │   └── foundry_chat.py   # Foundry клиент
│   ├── fastapi/              # FastAPI роутеры
│   ├── logger/               # Система логирования
│   ├── secrets/              # Конфигурация API ключей
│   └── utils/                # Утилиты
├── webinterface/              # Веб-интерфейсы
│   ├── user/                 # Пользовательский интерфейс
│   ├── admin/                # Админка
│   ├── rc/                   # Пульт ДУ
│   └── tgmini/               # Telegram Mini App
├── main.py                    # Точка входа
├── requirements.txt           # Зависимости
└── .env                       # Переменные окружения
```

---

## Примечания для AI

- Все инструкции по работе с медиатекой находятся в файле `.ai_instructions/prompts/media_organizer/system_instruction.md`
- Используйте TMDB API для получения жанров (Kinopoisk API закрыт)
- Всегда проверяйте лимиты API и переключайте ключи при необходимости
- RAG-индекс позволяет искать фильмы по описанию на естественном языке
- Медиатека хранится в SQLite и может быть выгружена в JSON/Markdown
- Плагины — основной механизм расширения функциональности