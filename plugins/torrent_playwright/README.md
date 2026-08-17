# Модуль `plugins.torrent_playwright` — Поиск торрентов через Playwright

## Назначение
Автоматизированный поиск торрент-раздач на трекерах (Rutracker, NNMClub) с использованием headless браузера Playwright:
- `playwright_searcher.py`: асинхронный движок поиска и авторизации на трекерах.
- `session_state/`: сохраненные сессии и cookies браузера для исключения повторной авторизации.
- `tools/`: вспомогательные скрипты и патчи для Playwright.\n