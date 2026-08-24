# Mediteka — AI Assistant & Media Player Control

[![Documentation Status](https://img.shields.io/badge/docs-latest-brightgreen.svg)](https://hypo69.github.io/mediteka/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

Современный веб-интерфейс с умным медиаплеером, автономными AI-агентами (LangChain, Google Gemini, Antigravity, Microsoft AI Foundry, Ollama), потоковым RAG-поиском по локальной медиатеке и системой голосового дистанционного управления (пультом ДУ).

---

## 📚 Документация

Полная документация доступна на GitHub Pages:

- 📖 **[Руководство пользователя](https://hypo69.github.io/mediteka/user/getting-started/)** — установка, использование плеера, голосовое управление, Telegram Mini App
- 📄 **[Работа с документами](https://hypo69.github.io/mediteka/dev/document-workflow/)** — управление документацией, PDF, таблицами и изображениями
- 💻 **[Руководство разработчика](https://hypo69.github.io/mediteka/dev/getting-started/)** — архитектура, разработка, плагины
- 🔌 **[API Reference](https://hypo69.github.io/mediteka/dev/api-reference/)** — все endpoints и плагины

---

## 🚀 Возможности

- 🤖 **Мульти-провайдерные AI-агенты:**
  - ReAct-агенты на базе LangChain и LangGraph
  - Поддержка Google Gemini (включая Gemini CLI и Search Grounding)
  - Поддержка Antigravity AGY, локальных моделей Microsoft AI Foundry и Ollama
  - MCP-интеграция (Model Context Protocol, включая Playwright MCP)
- 🎬 **Умный медиаплеер:** Воспроизведение видеопотоков, синхронизация между устройствами, автоматический подбор источников
- 📡 **Голосовой пульт ДУ:** Двустороннее голосовое управление (Speech-to-Text и Text-to-Speech через Web Speech API / Edge TTS)
- 📱 **Telegram Mini App:** Управление медиатекой и воспроизведением прямо из Telegram
- 📁 **Управление торрентами:** Поиск раздач и интеграция с qBittorrent
- 🧠 **Потоковый RAG-поиск (Streaming):** Векторный и семантический поиск по локальной базе `media.db` с трансляцией промежуточных шагов инструментов через SSE
- 🌐 **Cloudflare Tunnel:** Встроенный сценарий безопасного туннелирования внешнего доступа (`Run-Cloudflared.ps1`)
- 🧩 **Модульная архитектура плагинов:** Расширяемая система обработчиков и сканеров дисков

---

## 🏗️ Архитектура

```
┌────────────────────────────────────────────────────────────────────────┐
│                             Web Interface                              │
│  ┌────────────────┐       ┌────────────────┐       ┌────────────────┐  │
│  │  User Player   │       │ Remote Control │       │    Telegram    │  │
│  │   (/user)      │       │     (/rc)      │       │   Mini App     │  │
│  └───────┬────────┘       └───────┬────────┘       └───────┬────────┘  │
│          │                        │                        │           │
│          └────────────────────────┼────────────────────────┘           │
│                                   │                                    │
│                         ┌─────────▼──────────┐                         │
│                         │   FastAPI Server   │                         │
│                         └─────────┬──────────┘                         │
│                                   │                                    │
│    ┌──────────────────────────────┼──────────────────────────────┐     │
│    │                              │                              │     │
│┌───▼────────────────┐   ┌─────────▼──────────┐   ┌───────────────▼────┐│
││  LangChain / AI    │   │  Media Organizer   │   │  Torrent / Storage ││
││ • Gemini / AGY     │   │ • RAG Search       │   │ • qBittorrent      ││
││ • Foundry / Ollama │   │ • Drive Scanner    │   │ • Local media.db   ││
││ • Playwright MCP   │   │ • TMDB Metadata    │   │ • Cloudflare Tunnel││
│└────────────────────┘   └────────────────────┘   └────────────────────┘│
└────────────────────────────────────────────────────────────────────────┘
```

---

## ⚡ Быстрый старт

### Системные требования

- **ОС:** Windows 10/11, Linux или macOS
- **Python:** 3.10+ (рекомендуется 3.12 / 3.13)
- **API Ключи:** Google Gemini API Key (для моделей и поиска)

---

### 📦 Установка

#### Вариант 1. Автоматическая установка через `install.cmd` (Windows)

1. Клонируйте репозиторий:
   ```cmd
   git clone https://github.com/hypo69/mediteka.git C:\mediteka
   cd C:\mediteka
   ```
2. Запустите мастер установки:
   ```cmd
   install.cmd
   ```

**Что выполняет установщик:**
- Автоматически снимает блокировку файлов Windows (Mark of the Web / `Unblock-File`);
- Находит системный Python и создает чистое виртуальное окружение `venv`;
- Обновляет `pip`, `setuptools`, `wheel`;
- Предлагает варианты установки модульных зависимостей (полная, только сервер, AI, dev);
- Проверяет и автоматически генерирует локальные SSL-сертификаты (`~/.certs/localhost+2.pem`) для работы HTTPS;
- Проверяет корректность инициализации библиотек.

---

#### Вариант 2. Ручная установка (pip)

1. Клонируйте репозиторий:
   ```bash
   git clone https://github.com/hypo69/mediteka.git
   cd mediteka
   ```

2. Создайте и активируйте виртуальное окружение:
   ```bash
   # Windows
   py -3.13 -m venv venv
   .\venv\Scripts\pip install -r requirements.txt

   # Linux / macOS
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

---

### 📁 Структура зависимостей (`req/`)

Зависимости проекта модульно разделены в каталоге [`req/`](file:///C:/mediteka/req/):

- `req/requirements-core.txt` — ядро сервера (FastAPI, Uvicorn, Pydantic, Dotenv, JWT, aiohttp, httpx)
- `req/requirements-ai.txt` — искусственный интеллект (LangChain, LangGraph, Google GenAI, FAISS, ChromaDB, Sentence-Transformers, MCP)
- `req/requirements-media.txt` — мультимедиа и парсинг (yt-dlp, Edge-TTS, gTTS, PyDub, SpeechRecognition, Playwright)
- `req/requirements-utils.txt` — утилиты и документы (Pandas, Pillow, BeautifulSoup4, ReportLab, FPDF2, PDFMiner, Telegram Bot)
- `req/requirements-test.txt` — тестовый фреймворк (pytest, pytest-asyncio, coverage)
- `req/requirements-docs.txt` — генератор документации (MkDocs, Material theme)

Корневой файл `requirements.txt` автоматически объединяет все модули.

---

### ⚙️ Настройка конфигурации

1. **Несекретные параметры** хранятся в [`config.json`](file:///C:/mediteka/config.json):
   - Настройки хоста, порта, SSL (`server`)
   - Модели AI, параметры Foundry, AGY, Gemini CLI (`ai`)
   - Настройки LangChain, ReAct-агентов и MCP-серверов (`langchain`, `agents`)

2. **Секретные данные и API-ключи** хранятся в `.env`:
   ```bash
   cp .env.example .env
   ```
   Заполните `.env`:
   ```ini
   GEMINI_API_KEY=your_gemini_api_key_here
   TMDB_API_KEY=your_tmdb_api_key_here
   ```

---

### ▶️ Запуск сервера

#### Запуск на Windows через `run.ps1`:
```powershell
./run.ps1
```
Скрипт автоматически:
- Использует виртуальное окружение `venv\Scripts\python.exe` напрямую (без привязки к `Activate.ps1`);
- Проверяет и освобождает порт (по умолчанию `3000`);
- При необходимости запускает Cloudflare Tunnel (`Run-Cloudflared.ps1`) и Microsoft AI Foundry (`Run-Foundry.ps1`);
- Запускает FastAPI сервер с поддержкой Auto-reload и SSL.

#### Прямой запуск:
```bash
# Через venv
.\venv\Scripts\python.exe main.py

# Или через uvicorn
.\venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 3000 --reload
```

---

## 🖥️ Доступные веб-интерфейсы

| Интерфейс | URL | Описание |
|---|---|---|
| 🎬 **Медиаплеер** | `http://localhost:3000/user` | Основной плеер, стриминг и интерактивный AI-чат |
| 📡 **Пульт ДУ** | `http://localhost:3000/rc` | Голосовое управление воспроизведением (STT + TTS) |
| 📱 **Telegram Mini App** | `http://localhost:3000/tgmini` | Облегчённый интерфейс для Telegram-клиентов |
| ⚙️ **Админ-панель** | `http://localhost:3000/admin` | Управление медиатекой, дисками и статусом плагинов |
| 📄 **API Swagger** | `http://localhost:3000/docs` | Интерактивная документация OpenAPI |

---

## 🛠️ Технологический стек

- **Backend:** Python 3.10+, FastAPI, Uvicorn, AsyncIO, Server-Sent Events (SSE)
- **AI & Agents:** LangChain, LangGraph, Google Gemini API, Gemini CLI, Antigravity, Microsoft AI Foundry, Ollama, Playwright MCP
- **Поиск и RAG:** SQLite (`media.db`), FAISS, Sentence-Transformers, TMDb API
- **Media & Torrents:** qBittorrent Web API, yt-dlp, PyDub, Edge-TTS
- **Frontend:** HTML5, CSS3, Vanilla JavaScript, Web Speech API
- **Сеть и безопасность:** Cloudflare Tunnel, mkcert SSL

---

## 📄 Лицензия

MIT © 2026 hypo69
