#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: MCP Client Example for FastAPI Foundry
# =============================================================================
# Описание:
#   Пример клиента для работы с MCP сервером FastAPI Foundry
#   Демонстрирует использование Model Context Protocol
#
# File: example_mcp_client.py
# Project: Ai Assistant
# Module: FastApiFoundry
# Author: hypo69
# Copyright: © 2026 hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import asyncio
import json
import subprocess
import sys
from pathlib import Path
from src.logger import get_logger

# Создать логгер для MCP клиента
logger = get_logger("mcp-client")

class MCPClient:
    """Простой MCP клиент для демонстрации"""
    
    def __init__(self, server_path: str):
        self.server_path = Path(server_path)
        self.process = None
    
    async def start_server(self):
        """Запуск MCP сервера"""
        print("🚀 Запуск MCP сервера...")
        
        if not self.server_path.exists():
            print(f"❌ MCP сервер не найден: {self.server_path}")
            return False
        
        try:
            # Запуск MCP сервера как subprocess
            self.process = await asyncio.create_subprocess_exec(
                sys.executable, str(self.server_path),
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            print("✅ MCP сервер запущен")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка запуска MCP сервера: {e}")
            return False
    
    async def send_request(self, method: str, params: dict = None):
        """Отправка MCP запроса"""
        if not self.process:
            print("❌ MCP сервер не запущен")
            return None
        
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params or {}
        }
        
        try:
            # Отправка запроса
            request_data = json.dumps(request) + "\n"
            self.process.stdin.write(request_data.encode())
            await self.process.stdin.drain()
            
            # Чтение ответа
            response_data = await self.process.stdout.readline()
            if response_data:
                response = json.loads(response_data.decode().strip())
                return response
            
        except Exception as e:
            print(f"❌ Ошибка MCP запроса: {e}")
            return None
    
    async def stop_server(self):
        """Остановка MCP сервера"""
        if self.process:
            self.process.terminate()
            await self.process.wait()
            print("🛑 MCP сервер остановлен")

async def demo_mcp_client():
    """Демонстрация MCP клиента"""
    
    print("🔌 FastAPI Foundry - MCP Client Demo")
    print("=" * 50)
    
    # Путь к MCP серверу
    mcp_server_path = Path("mcp-servers/Ai Assistant-foundry/src/server.py")
    
    if not mcp_server_path.exists():
        print(f"❌ MCP сервер не найден: {mcp_server_path}")
        print("📝 Убедитесь, что MCP сервер установлен:")
        print("   cd mcp-servers/Ai Assistant-foundry")
        print("   pip install -r requirements.txt")
        return
    
    client = MCPClient(mcp_server_path)
    
    try:
        # Запуск сервера
        logger.info("Начало демонстрации MCP клиента")
        if not await client.start_server():
            logger.error("Не удалось запустить MCP сервер, завершение демонстрации")
            return
        
        # Небольшая пауза для инициализации
        await asyncio.sleep(2)
        
        print("\n1️⃣ Инициализация MCP соединения...")
        
        # Инициализация
        init_response = await client.send_request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "roots": {
                    "listChanged": True
                },
                "sampling": {}
            },
            "clientInfo": {
                "name": "FastAPI Foundry MCP Demo",
                "version": "1.0.0"
            }
        })
        
        if init_response:
            print("✅ MCP инициализация успешна")
            print(f"   Сервер: {init_response.get('result', {}).get('serverInfo', {}).get('name', 'Unknown')}")
        else:
            print("❌ Ошибка инициализации MCP")
            return
        
        print("\n2️⃣ Получение списка доступных инструментов...")
        
        # Получение списка инструментов
        tools_response = await client.send_request("tools/list")
        
        if tools_response and 'result' in tools_response:
            tools = tools_response['result'].get('tools', [])
            print(f"📦 Найдено инструментов: {len(tools)}")
            
            for tool in tools:
                print(f"  🔧 {tool['name']}")
                print(f"     {tool.get('description', 'Нет описания')}")
                
                # Показать параметры
                if 'inputSchema' in tool:
                    properties = tool['inputSchema'].get('properties', {})
                    if properties:
                        print(f"     Параметры: {', '.join(properties.keys())}")
                print()
        else:
            print("❌ Не удалось получить список инструментов")
        
        print("\n3️⃣ Демонстрация вызова инструмента...")
        
        # Пример вызова инструмента generate_text
        if tools_response and 'result' in tools_response:
            tools = tools_response['result'].get('tools', [])
            generate_tool = next((t for t in tools if t['name'] == 'generate_text'), None)
            
            if generate_tool:
                print("🤖 Вызов инструмента generate_text...")
                
                generate_response = await client.send_request("tools/call", {
                    "name": "generate_text",
                    "arguments": {
                        "prompt": "Привет! Как дела?",
                        "max_tokens": 50
                    }
                })
                
                if generate_response and 'result' in generate_response:
                    content = generate_response['result'].get('content', [])
                    if content:
                        print("✅ Ответ от AI модели:")
                        for item in content:
                            if item.get('type') == 'text':
                                print(f"   {item.get('text', '')}")
                else:
                    print("❌ Ошибка вызова инструмента")
            else:
                print("⚠️ Инструмент generate_text не найден")
        
        print("\n4️⃣ Получение ресурсов...")
        
        # Получение ресурсов
        resources_response = await client.send_request("resources/list")
        
        if resources_response and 'result' in resources_response:
            resources = resources_response['result'].get('resources', [])
            print(f"📚 Найдено ресурсов: {len(resources)}")
            
            for resource in resources[:3]:  # Показать первые 3
                print(f"  📄 {resource.get('name', 'Unknown')}")
                print(f"     URI: {resource.get('uri', 'Unknown')}")
                print(f"     Тип: {resource.get('mimeType', 'Unknown')}")
                print()
        else:
            print("❌ Не удалось получить список ресурсов")
        
        print("\n5️⃣ Полезные команды для MCP:")
        print("📋 Настройка Claude Desktop:")
        print("   1. Откройте настройки Claude Desktop")
        print("   2. Добавьте конфигурацию MCP сервера:")
        print("   {")
        print('     "mcpServers": {')
        print('       "fastapi-foundry": {')
        print('         "command": "python",')
        print(f'         "args": ["{mcp_server_path.absolute()}"]')
        print('       }')
        print('     }')
        print("   }")
        print()
        print("🔧 Прямое тестирование:")
        print(f"   python {mcp_server_path}")
        print()
        print("📚 Документация MCP:")
        print("   https://modelcontextprotocol.io/")
        
    except KeyboardInterrupt:
        print("\n⏹️ Остановка демонстрации...")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        await client.stop_server()
    
    print("\n" + "=" * 50)
    print("🎉 MCP Client Demo завершена!")
    print("📚 Проверьте mcp-servers/Ai Assistant-foundry/README.md для подробностей")

if __name__ == "__main__":
    asyncio.run(demo_mcp_client())