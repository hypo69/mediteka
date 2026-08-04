# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Менеджер WebSocket соединений
# =============================================================================
# Описание:
#   Управление активными WebSocket соединениями с поддержкой комнат (rooms).
#   Обеспечивает изоляцию потоков уведомлений для разных модулей (Foundry, RAG).
#
# File: src/api/websocket_manager.py
# Project: Ai Assistant
# Package: src.api
# Module: websocket_manager
# Version: 0.6.1
# Author: hypo69
# Copyright: © 2026 hypo69
# License: MIT
# Date: 2025
# =============================================================================

import asyncio
import json
from typing import List, Dict, Optional
from fastapi import WebSocket
from src.logger import logger

class ConnectionManager:
    """Класс для управления жизненным циклом WebSocket соединений и рассылки уведомлений."""

    def __init__(self) -> None:
        """Инициализация хранилища соединений и комнат."""
        self.active_connections: List[WebSocket] = []
        self.rooms: Dict[str, List[WebSocket]] = {
            "foundry": [],
            "rag": [],
            "system": []
        }
        self.pending_permissions: Dict[str, asyncio.Future] = {}

    async def connect(self, websocket: WebSocket, room: Optional[str] = None) -> None:
        """Регистрация нового соединения.

        Args:
            websocket (WebSocket): Объект веб-сокета.
            room (str, optional): Название комнаты для подписки.
        """
        await websocket.accept()
        self.active_connections.append(websocket)
        
        if room and room in self.rooms:
            self.rooms[room].append(websocket)
            logger.debug(f"WebSocket: Клиент подключен к комнате '{room}'")
        else:
            logger.debug("WebSocket: Клиент подключен к общему каналу")

        # Автоматическая отправка приветственного сообщения
        # Automatic sending of a welcome message
        await self.send_personal_message({
            "type": "welcome",
            "message": f"Successfully connected to room: {room or 'general'}",
            "room": room,
            "timestamp": asyncio.get_event_loop().time()
        }, websocket)

    def disconnect(self, websocket: WebSocket, room: Optional[str] = None) -> None:
        """Удаление закрытого соединения из реестра.

        Args:
            websocket (WebSocket): Объект веб-сокета.
            room (str, optional): Название комнаты.
        """
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        
        if room and room in self.rooms and websocket in self.rooms[room]:
            self.rooms[room].remove(websocket)

    async def send_personal_message(self, message: dict, websocket: WebSocket) -> None:
        """Отправка приватного сообщения конкретному клиенту."""
        await websocket.send_json(message)

    async def broadcast(self, message: dict, room: Optional[str] = None) -> None:
        """Рассылка уведомления группе клиентов или всем сразу.

        Обоснование:
          - Поддержка комнат позволяет экономить трафик и ресурсы клиента.
          - Автоматическая очистка "мёртвых" соединений при попытке отправки.

        Args:
            message (dict): Данные для отправки.
            room (str, optional): Название целевой комнаты. Если None — всем.
        """
        targets: List[WebSocket] = []
        dead_connections: List[WebSocket] = []

        # Определение списка получателей
        # Definition of the recipient list
        if room and room in self.rooms:
            targets = self.rooms[room]
        else:
            targets = self.active_connections

        for connection in targets:
            try:
                # Асинхронная отправка JSON-данных
                # Asynchronous JSON data delivery
                await connection.send_json(message)
            except Exception:
                # Сбор "мёртвых" соединений для удаления
                # Collection of dead connections for removal
                dead_connections.append(connection)

        # Очистка невалидных соединений
        # Cleanup of invalid connections
        for dead in dead_connections:
            self.disconnect(dead, room)

        if dead_connections:
            logger.debug(f"WebSocket: Очищено {len(dead_connections)} закрытых соединений")

    async def wait_for_permission(self, permission_id: str) -> bool:
        """Регистрация ожидания подтверждения от пользователя."""
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        self.pending_permissions[permission_id] = future
        return await future

    async def handle_hitl_response(self, permission_id: str, confirmed: bool) -> None:
        """Обработка ответа пользователя и сохранение решения в Chat DB.

        Args:
            permission_id (str): Идентификатор запроса.
            confirmed (bool): Выбор пользователя (разрешить/отклонить).
        """
        if permission_id in self.pending_permissions:
            future = self.pending_permissions.pop(permission_id)
            if not future.done():
                future.set_result(confirmed)

            # Сохранение решения в SQLite (Chat DB) для истории и аудита
            try:
                from src.db.chat_db import get_chat_db
                db = await get_chat_db()
                # Сохраняем запись в системную сессию аудита
                await db.save_message(
                    session_id="hitl_audit_log",
                    role="system",
                    content=f"HITL Decision: {'ALLOWED' if confirmed else 'DENIED'} | Request: {permission_id}"
                )
                logger.info(f"WebSocket: Решение HITL {permission_id} сохранено в БД.")
            except Exception as e:
                logger.error(f"WebSocket: Ошибка при сохранении лога HITL: {e}")


# Глобальный экземпляр менеджера
# Global manager instance
manager = ConnectionManager()