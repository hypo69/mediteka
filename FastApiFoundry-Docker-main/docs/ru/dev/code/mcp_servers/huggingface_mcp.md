# Huggingface Mcp

**Файл:** `servers/huggingface_mcp.py`  
**Тип:** `.py`

---

Модуль MCP сервера для интеграции с HuggingFace
=========================================================================================

Модуль предоставляет MCP (Model Context Protocol) сервер для взаимодействия с моделями
HuggingFace через Inference API. Поддерживает генерацию текста и другие возможности
inference API.

Зависимости:
    - mcp
    - huggingface_hub
    - asyncio

Пример использования:
    python src/servers/huggingface_mcp.py

.. module:: src.servers.huggingface_mcp

### `HuggingFaceMCPServer` — Класс

```python
class HuggingFaceMCPServer
```

MCP сервер для работы с HuggingFace Inference API.

Класс инициализирует MCP сервер и регистрирует инструменты для работы
с моделями HuggingFace.

Attributes:
    server (Server): Экземпляр MCP сервера
    client (InferenceClient): Клиент для взаимодействия с HuggingFace API

### `main` — Функция

```python
async def main() -> None
```

Главная точка входа приложения.

Функция создает и запускает экземпляр MCP сервера HuggingFace.

### `__init__` — Функция

```python
def __init__(self) -> None
```

Инициализация MCP сервера HuggingFace.

Функция создает экземпляр сервера и клиента для работы с API.
Токен авторизации извлекается из переменной окружения HF_TOKEN.

Raises:
    ValueError: Если токен HF_TOKEN не установлен в окружении

### `list_tools` — Функция

```python
async def list_tools(self) -> list[types.Tool]
```

Возвращает список доступных инструментов MCP.

Функция предоставляет описание всех инструментов, доступных через
данный MCP сервер.

Returns:
    list[types.Tool]: Список инструментов с описанием и схемами входных данных

Example:
    >>> server = HuggingFaceMCPServer()
    >>> tools = await server.list_tools()
    >>> print(tools[0].name)
    'text_generation'

### `call_tool` — Функция

```python
async def call_tool(self, name: str, arguments: dict[str, Any]) -> list[types.TextContent]
```

Выполнение вызова инструмента MCP.

Функция обрабатывает запросы на выполнение конкретного инструмента
и возвращает результат работы.

Args:
    name (str): Название инструмента для вызова
    arguments (dict[str, Any]): Аргументы для передачи инструменту

Returns:
    list[types.TextContent]: Список текстовых ответов от модели

Raises:
    ValueError: Если указан неизвестный инструмент
    Exception: При ошибках взаимодействия с HuggingFace API

Example:
    >>> server = HuggingFaceMCPServer()
    >>> result = await server.call_tool('text_generation', {'prompt': 'Hello'})
    >>> print(result[0].text)

### `run` — Функция

```python
async def run(self) -> None
```

Запуск MCP сервера.

Функция запускает основной цикл обработки запросов MCP сервера.

Example:
    >>> server = HuggingFaceMCPServer()
    >>> await server.run()


---

*Проект: AI Assistant (ai_assist) · v0.8.0 · автогенерация: `scripts/Create-Doc/Generate-FullReference.py`*
