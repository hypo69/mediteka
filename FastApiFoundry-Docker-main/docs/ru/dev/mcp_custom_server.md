# Создание собственного MCP сервера

## Что такое MCP?

**Model Context Protocol (MCP)** — это открытый стандарт, позволяющий языковым моделям безопасно взаимодействовать с внешними данными и инструментами. В архитектуре AI Assistant MCP-серверы играют роль «рук и глаз» системы, позволяя агентам выполнять действия в ОС, читать базы данных или обращаться к сторонним API.

## Зачем создавать свой сервер?
- Интеграция с вашей внутренней БД (SQL, NoSQL).
- Управление специфическим оборудованием или софтом.
- Чтение проприетарных форматов данных.
- Выполнение специфических скриптов автоматизации.

## Выбор протокола

AI Assistant поддерживает два основных способа взаимодействия с MCP:
1. **STDIO:** Сервер запускается как дочерний процесс. Самый простой способ для локальных инструментов.
2. **HTTP (SSE):** Сервер работает как сетевой сервис. Удобно для распределенных систем.

## Пример: Простой MCP сервер на Python (STDIO)

Для создания сервера мы рекомендуем использовать официальный SDK: `pip install mcp`.

```python
# my_custom_server.py
import asyncio
from mcp.server.models import InitializationOptions
from mcp.server import Notification, Server
import mcp.types as types
from mcp.server.stdio import stdio_server

server = Server("my-business-tools")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """Список доступных инструментов"""
    return [
        types.Tool(
            name="get_order_status",
            description="Получить статус заказа из внутренней БД",
            inputSchema={
                "type": "object",
                "properties": {
                    "order_id": {"type": "string"},
                },
                "required": ["order_id"],
            },
        )
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent]:
    """Логика выполнения инструментов"""
    if name == "get_order_status":
        order_id = arguments.get("order_id")
        # Здесь ваша логика запроса к БД
        status = "Доставлен" if order_id == "123" else "В обработке"
        return [types.TextContent(type="text", text=f"Статус заказа {order_id}: {status}")]
    raise ValueError(f"Инструмент {name} не найден")

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="my-business-tools",
                server_version="0.1.0",
                capabilities=server.get_capabilities(),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())
```

## Интеграция с AI Assistant

Чтобы AI Assistant увидел ваш сервер, добавьте его в конфигурацию. Если вы используете `McpSTDIOServer.ps1`, пропишите команду запуска в файле настроек MCP клиентов (например, в конфигурации Claude Desktop или внутреннего `mcp_agent`).

1. Соберите ваш скрипт в исполняемый файл или убедитесь, что python доступен в PATH.
2. Запустите `Start-MCPServers.ps1` для автоматического подхвата новых серверов в директории `mcp/src/servers/`.
3. Проверьте доступность инструментов через эндпоинт `/api/v1/mcp/tools`.