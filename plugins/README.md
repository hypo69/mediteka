# Модуль `plugins` — Плагинная архитектура

## Назначение
Каталог содержит 12 подключаемых функциональных плагинов системы `mediteka`. 
Плагинная архитектура обеспечивает модульность, расширяемость и динамическую загрузку компонентов.

## Архитектура плагинов

### Базовый класс `BasePlugin`
Все плагины наследуются от `BasePlugin` (`plugin.py`) и реализуют стандартный интерфейс:

```python
class BasePlugin(ABC):
    name: str = 'base'
    enabled: bool = True
    
    async def handle(self, message: str, **kwargs) -> str:
        """Обработка входящего сообщения плагином"""
        pass
    
    def get_manifest(self) -> dict:
        """Возвращает манифест плагина для регистрации"""
        pass
```

### Динамическая загрузка
Функция `load_plugins(ai_model)` в `__init__.py` динамически сканирует поддиректории и регистрирует плагины:
- Автоматическое обнаружение новых плагинов
- Загрузка конфигурации из `config.json` и `.env`
- Управление состоянием (enabled/disabled)
- Интеграция с UnifiedChatModel

### Точка входа
Каждый плагин экспортирует фабричную функцию `plugin(ai_model)`, которая возвращает экземпляр плагина с инжектированной AI моделью.

## Доступные плагины (12)

| Плагин | Категория | Описание | Триггеры | Интеграция |
|--------|-----------|----------|----------|------------|
| `media_organizer` | Медиатека | Управление медиатекой, сканирование дисков, RAG | Function Calling | UnifiedChatModel, SQLite |
| `rag` | Поиск | Семантический поиск по медиатеке | "фильм", "сериал", "посоветуй" | FAISS, Gemini Embeddings |
| `media_layer` | Медиатека | Облегченный слой доступа к базе медиа | "фильм", "сериал" | SQLite, конфигурация |
| `web_search` | Веб | Поиск в интернете через Playwright | "погугли", "поищи в интернете" | Playwright, AI анализ |
| `torrent_playwright` | Торренты | Поиск торрентов через Playwright | "торрент", "скачать" | Rutracker, NNMClub, AI фильтрация |
| `movie_search_sources` | Источники | Каталог стриминговых сервисов | "где посмотреть", "плеер" | TMDB, streaming сервисы |
| `qbittorrent` | Торренты | Интеграция с qBittorrent | "добавь торрент", "категории" | QBittorrent API, категории |
| `telegram_bot` | Коммуникация | Удаленное управление через Telegram | — (отдельный процесс) | Telegram Bot API, Mini App |
| `user_manager_tool` | Пользователи | Управление пользователями | `!list_users`, `!user_activity` | SQLite users.db, сессии |
| `yt_dlp` | Загрузка | Скачивание медиаконтента | "скачай", "youtube", "mp3" | yt-dlp, прогресс-бар |
| `langchain_media` | AI | LangChain медиа-инструменты | "лангчейн", "агент" | LangChain, агенты, цепочки |
| `plugin_manager` | Система | Управление плагинами | — (админ) | Конфигурация, интерфейсы |

## Конфигурация плагинов

### Файл `config.json`
```json
{
  "plugins": {
    "media_organizer": {
      "enabled": true,
      "config": {
        "db_path": "plugins/media_organizer/data/media.db",
        "rag_enabled": true
      }
    },
    "rag": {
      "enabled": true,
      "config": {
        "index_path": "rag/faiss_index",
        "embedding_model": "gemini"
      }
    }
  }
}
```

### Переменные окружения
```env
DISABLED_PLUGINS=plugin1,plugin2
PLUGINS_CONFIG_PATH=config.json
```

## Регистрация в интерфейсах

### Манифест плагина
Каждый плагин предоставляет манифест через метод `get_manifest()`:
```json
{
  "name": "media_organizer",
  "title": "Медиатека",
  "description": "Управление медиатекой и сканирование дисков",
  "icon": "🎬",
  "version": "1.0.0",
  "category": "media",
  "enabled": true,
  "fields": [
    {"name": "db_path", "type": "string", "label": "Путь к БД"},
    {"name": "rag_enabled", "type": "boolean", "label": "RAG поиск"}
  ],
  "actions": [
    {"name": "scan", "label": "Сканировать", "endpoint": "/api/media/scan"},
    {"name": "search", "label": "Поиск", "endpoint": "/api/media/by-title"}
  ]
}
```

### Автоматическая регистрация
Манифесты автоматически используются для:
- Отображения плагинов в административном интерфейсе
- Генерации форм конфигурации
- Регистрации действий и эндпоинтов
- Категоризации и фильтрации

## Разработка новых плагинов

### Структура плагина
```
plugins/new_plugin/
├── __init__.py          # Фабричная функция plugin()
├── plugin.py           # Основной класс плагина
├── config.json         # Конфигурация плагина
├── README.md          # Документация плагина
└── requirements.txt    # Зависимости (опционально)
```

### Шаблон плагина
```python
# plugins/new_plugin/plugin.py
from typing import Any, Dict
from plugins.plugin import BasePlugin

class NewPlugin(BasePlugin):
    name = 'new_plugin'
    
    def __init__(self, ai_model):
        super().__init__()
        self.ai_model = ai_model
        self.config = self._load_config()
    
    async def handle(self, message: str, **kwargs) -> str:
        """Обработка входящих сообщений"""
        if not self.enabled:
            return "Плагин отключен"
        
        # Логика обработки
        result = await self._process_message(message)
        
        # Потоковый вывод
        yield {"status": "Обработка", "text": "Выполняется обработка..."}
        yield {"text": result}
    
    def get_manifest(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "title": "Новый плагин",
            "description": "Описание функциональности плагина",
            "icon": "🧩",
            "version": "1.0.0",
            "category": "tools",
            "enabled": self.enabled,
            "fields": [],
            "actions": []
        }
    
    def _load_config(self):
        # Загрузка конфигурации
        pass
    
    async def _process_message(self, message: str):
        # Основная логика обработки
        pass


def plugin(ai_model) -> NewPlugin:
    """Фабричная функция для создания экземпляра плагина"""
    return NewPlugin(ai_model)
```

### Правила разработки
1. **Наследование от BasePlugin** — обязательно
2. **Потоковый вывод** — для длительных операций использовать `yield`
3. **Обработка ошибок** — не нарушать работу системы при ошибках в плагине
4. **Конфигурация** — использовать стандартные механизмы конфигурации
5. **Манифест** — предоставлять полный манифест для регистрации
6. **Интеграция с AI** — использовать переданный UnifiedChatModel
7. **Тестирование** — покрывать тестами основную функциональность

## Управление плагинами

### Динамическое включение/выключение
```python
# Через конфигурацию
plugins['media_organizer'].enabled = False

# Через переменные окружения
export DISABLED_PLUGINS=media_organizer,rag

# Через веб-интерфейс
POST /api/admin/plugins/{name}/toggle
```

### Мониторинг состояния
```python
# Получение статуса всех плагинов
for name, plugin in plugins.items():
    print(f"{name}: {'Включен' if plugin.enabled else 'Отключен'}")
```

### Обновление конфигурации
```python
# Динамическое обновление конфигурации
plugin.config.update(new_config)
plugin._save_config()
```

## Интеграция с UnifiedChatModel

### Function Calling
Плагины могут предоставлять функции для AI моделей через механизм Function Calling:

```python
class MediaOrganizerPlugin(BasePlugin):
    # ...
    
    def get_tools(self):
        return [
            {
                "type": "function",
                "function": {
                    "name": "search_media",
                    "description": "Поиск медиа по названию",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "type": {"type": "string", "enum": ["movie", "series"]}
                        }
                    }
                }
            }
        ]
```

### Автоматическая регистрация инструментов
Инструменты плагинов автоматически регистрируются в UnifiedChatModel и доступны для Function Calling.

## Примеры использования

### Обработка запроса через плагин
```python
plugins = load_plugins(ai_model)

# Автоматический выбор плагина по триггерам
query = "посоветуй фильм про космос"
for plugin in plugins.values():
    if plugin.enabled and plugin.should_handle(query):
        async for chunk in plugin.handle(query):
            print(chunk)
```

### Интеграция с чатом
```python
# В router_chat.py
async def chat_endpoint(message: str):
    # Проверка триггеров плагинов
    for plugin in plugins.values():
        if plugin.enabled and _is_plugin_query(message, plugin):
            async for chunk in plugin.handle(message):
                yield chunk
            return
    
    # Обычный AI запрос
    async for chunk in ai_model.chat_stream(message):
        yield chunk
```

## Отладка и мониторинг

### Логирование
```python
from src.logger import logger

logger.info(f"Плагин {self.name} запущен")
logger.error(f"Ошибка в плагине {self.name}", exc_info=True)
```

### Метрики
- Количество обработанных запросов
- Время выполнения операций
- Статус плагинов (enabled/disabled)
- Ошибки и исключения

## Устранение неполадок

### Плагин не загружается
1. Проверить наличие `__init__.py` с функцией `plugin()`
2. Проверить наследование от `BasePlugin`
3. Проверить конфигурацию в `config.json`
4. Проверить переменную окружения `DISABLED_PLUGINS`

### Плагин не обрабатывает запросы
1. Проверить триггеры в манифесте
2. Проверить метод `should_handle()`
3. Проверить логирование ошибок
4. Проверить интеграцию с UnifiedChatModel

### Ошибки в потоковом выводе
1. Проверить использование `yield` вместо `return`
2. Проверить формат выходных данных
3. Проверить обработку исключений
4. Проверить интеграцию с SSE/WebSocket

---

**Последнее обновление:** 24 августа 2026  
**Количество плагинов:** 12  
**Архитектура:** BasePlugin + UnifiedChatModel + динамическая загрузка