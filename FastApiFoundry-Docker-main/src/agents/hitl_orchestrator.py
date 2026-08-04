# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Оркестратор с подтверждением действий (HITL)
# =============================================================================
# Описание:
#   Реализация логики перехвата потенциально опасных команд MCP инструментов.
#   Проверка описаний инструментов и сверка со списками ограничений.
#
# File: hitl_orchestrator.py
# Project: Ai Assistant
# Author: Gemini Code Assist
# Copyright: © 2026 Ai Assistant
# =============================================================================

import asyncio
from datetime import datetime
import uuid
from src.logger import logger
from src.core.config import config
from src.api.websocket_manager import manager

class HITLOrchestrator:
    """Класс для управления подтверждением действий пользователя (Human-in-the-loop)
    
    Attributes:
        dangerous_patterns (list): Список маркеров опасности в описаниях инструментов.
        protected_tools (list): Список имен инструментов, требующих подтверждения.
    """

    def __init__(self) -> None:
        """Инициализация оркестратора и загрузка конфигурации."""
        # Получение настроек из секции mcp_agent
        mcp_config: dict = config.get("mcp_agent", {})
        self.protected_tools: list = mcp_config.get("require_confirmation", [])
        
        # Стандартные маркеры опасного контента
        self.dangerous_patterns: list = ["[DANGEROUS]", "danger_", "удаление", "format"]

    def is_confirmation_required(self, tool_name: str, tool_description: str) -> bool:
        """Проверка необходимости подтверждения перед выполнением.

        Args:
            tool_name (str): Имя инструмента.
            tool_description (str): Текстовое описание функционала инструмента.

        Returns:
            bool: True при необходимости ручного подтверждения.

        Examples:
            >>> orchestrator = HITLOrchestrator()
            >>> orchestrator.is_confirmation_required("delete_file", "Удаляет файл")
            True
        """
        # Проверка по списку защищенных имен
        if tool_name in self.protected_tools:
            logger.warning(f"Обнаружен защищенный инструмент: {tool_name}")
            return True

        # Проверка наличия опасных паттернов в описании
        description_lower = tool_description.lower()
        for pattern in self.dangerous_patterns:
            if pattern.lower() in description_lower:
                logger.warning(f"Обнаружен маркер опасности '{pattern}' в инструменте {tool_name}")
                return True

        return False

    async def request_user_permission(self, tool_name: str, arguments: dict) -> bool:
        """Запрос разрешения у пользователя на выполнение действия.

        Args:
            tool_name (str): Имя инструмента.
            arguments (dict): Параметры вызова.

        Returns:
            bool: Результат выбора пользователя.
        """
        permission_id = str(uuid.uuid4())
        timeout = 300  # 5 минут согласно mcp_hitl.md
        
        logger.info(f"🔑 [HITL] Запрос разрешения {permission_id} для инструмента: {tool_name}")

        # Отправляем уведомление в UI через WebSocket
        payload = {
            "type": "hitl_request",
            "permission_id": permission_id,
            "tool": tool_name,
            "arguments": arguments,
            "timeout": timeout
        }
        
        await manager.broadcast(payload)

        try:
            # Ожидаем ответа от пользователя через WebSocketManager
            # Предполагается, что менеджер умеет хранить Future для конкретных ID
            confirmed = await asyncio.wait_for(
                manager.wait_for_permission(permission_id), 
                timeout=timeout
            )
            
            # Логирование ответа пользователя
            status = "РАЗРЕШЕНО" if confirmed else "ОТКЛОНЕНО"
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_msg = f"📝 [HITL] Решение: {status} | Инструмент: {tool_name} | Пользователь: User | Время: {timestamp} | ID: {permission_id}"
            
            if confirmed:
                logger.info(f"✅ {log_msg}")
            else:
                logger.warning(f"🚫 {log_msg}")
                
            return confirmed
            
        except asyncio.TimeoutError:
            logger.error(f"⌛ [HITL] ТАЙМАУТ: Действие {tool_name} автоматически отклонено (ID: {permission_id})")
            # Уведомляем интерфейс о таймауте для автоматического закрытия модального окна
            asyncio.create_task(manager.broadcast({
                "type": "hitl_timeout",
                "permission_id": permission_id
            }))
            return False

if __name__ == "__main__":
    # Пример использования
    orchestrator = HITLOrchestrator()
    is_dangerous = orchestrator.is_confirmation_required("rm_rf", "[DANGEROUS] Удаление всего")
    print(f"Требуется подтверждение: {is_dangerous}")