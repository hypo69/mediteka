## \file src/servers/huggingface_mcp.py
# -*- coding: utf-8 -*-
#! .pyenv/bin/python3

"""
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
"""

import asyncio
import os
from typing import Any

from mcp import Server, types
from huggingface_hub import InferenceClient

# Импорт логгера из проекта
try:
    from src.logger.logger import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO)


class HuggingFaceMCPServer:
    """
    MCP сервер для работы с HuggingFace Inference API.
    
    Класс инициализирует MCP сервер и регистрирует инструменты для работы
    с моделями HuggingFace.
    
    Attributes:
        server (Server): Экземпляр MCP сервера
        client (InferenceClient): Клиент для взаимодействия с HuggingFace API
    """
    
    def __init__(self) -> None:
        """
        Инициализация MCP сервера HuggingFace.
        
        Функция создает экземпляр сервера и клиента для работы с API.
        Токен авторизации извлекается из переменной окружения HF_TOKEN.
        
        Raises:
            ValueError: Если токен HF_TOKEN не установлен в окружении
        """
        hf_token: str | None = os.getenv('HF_TOKEN')
        
        if not hf_token:
            error_message: str = 'Переменная окружения HF_TOKEN не установлена'
            logger.error(error_message)
            raise ValueError(error_message)
        
        self.server: Server = Server('huggingface-mcp')
        self.client: InferenceClient = InferenceClient(token=hf_token)
        
        # Регистрация обработчиков MCP
        self.server.list_tools().callback(self.list_tools)
        self.server.call_tool().callback(self.call_tool)
        
        logger.info('MCP сервер HuggingFace инициализирован успешно')
    
    async def list_tools(self) -> list[types.Tool]:
        """
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
        """
        tools: list[types.Tool] = [
            types.Tool(
                name='text_generation',
                description='Генерация текста с использованием моделей HuggingFace',
                inputSchema={
                    'type': 'object',
                    'properties': {
                        'prompt': {
                            'type': 'string',
                            'description': 'Текстовый промпт для генерации'
                        },
                        'model': {
                            'type': 'string',
                            'default': 'mistralai/Mistral-7B-Instruct-v0.2',
                            'description': 'Название модели на HuggingFace'
                        },
                        'max_tokens': {
                            'type': 'number',
                            'default': 100,
                            'description': 'Максимальное количество токенов для генерации'
                        }
                    },
                    'required': ['prompt']
                }
            )
        ]
        
        logger.debug(f'Возврат списка из {len(tools)} инструментов')
        return tools
    
    async def call_tool(self, name: str, arguments: dict[str, Any]) -> list[types.TextContent]:
        """
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
        """
        logger.info(f'Вызов инструмента: {name}')
        
        if name == 'text_generation':
            prompt: str = arguments.get('prompt', '')
            model: str = arguments.get('model', 'mistralai/Mistral-7B-Instruct-v0.2')
            max_tokens: int = int(arguments.get('max_tokens', 100))
            
            try:
                logger.debug(f'Генерация текста с моделью {model}, max_tokens={max_tokens}')
                
                response: str = self.client.text_generation(
                    prompt,
                    model=model,
                    max_new_tokens=max_tokens
                )
                
                logger.info(f'Успешная генерация текста, длина: {len(response)} символов')
                
                return [types.TextContent(type='text', text=response)]
                
            except Exception as ex:
                logger.error(f'Ошибка при генерации текста: {ex}', ex, exc_info=True)
                error_text: str = f'Ошибка генерации: {str(ex)}'
                return [types.TextContent(type='text', text=error_text)]
        
        error_message: str = f'Неизвестный инструмент: {name}'
        logger.error(error_message)
        raise ValueError(error_message)
    
    async def run(self) -> None:
        """
        Запуск MCP сервера.
        
        Функция запускает основной цикл обработки запросов MCP сервера.
        
        Example:
            >>> server = HuggingFaceMCPServer()
            >>> await server.run()
        """
        logger.info('Запуск MCP сервера HuggingFace')
        await self.server.run()


async def main() -> None:
    """
    Главная точка входа приложения.
    
    Функция создает и запускает экземпляр MCP сервера HuggingFace.
    """
    try:
        server: HuggingFaceMCPServer = HuggingFaceMCPServer()
        await server.run()
    except Exception as ex:
        logger.error(f'Критическая ошибка запуска сервера: {ex}', ex, exc_info=True)
        raise


if __name__ == '__main__':
    asyncio.run(main())