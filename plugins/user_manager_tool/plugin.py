# -*- coding: utf-8 -*-
import sqlite3
from plugins.plugin import BasePlugin
from src.user_manager import UserManager
from header import __root__

class UserManagerTool(BasePlugin):
    name: str = 'user_manager'

    def __init__(self, ai_model) -> None:
        super().__init__(ai_model)
        self.user_manager = UserManager(__root__ / 'src' / 'user_manager' / 'users.db')

    async def _handle(self, message: str, **kwargs) -> str:
        message = message.lower().strip()
        
        if message.startswith('!list_users'):
            users = self.user_manager.get_all_users(active_only=False)
            if not users:
                return "Пользователей не найдено."
            response = "Список пользователей:\n"
            for u in users:
                response += f"- ID: {u['id']}, Email: {u['email']}, Имя: {u['name']}, Роль: {u['role']}\n"
            return response
        
        elif message.startswith('!user_activity'):
            try:
                parts = message.split()
                if len(parts) < 2:
                    return "Использование: !user_activity <user_id>"
                user_id = int(parts[1])
                
                with self.user_manager._get_connection() as conn:
                    conn.row_factory = sqlite3.Row
                    logs = conn.execute(
                        'SELECT * FROM user_activity_log WHERE user_id = ? ORDER BY timestamp DESC LIMIT 10',
                        (user_id,)
                    ).fetchall()
                
                if not logs:
                    return f"Активность для пользователя {user_id} не найдена."
                
                response = f"Последняя активность пользователя {user_id}:\n"
                for log in logs:
                    response += f"- [{log['timestamp']}] {log['action']} | {log['details']}\n"
                return response
            except ValueError:
                return "Неверный формат user_id."
            except Exception as e:
                return f"Ошибка при получении логов: {e}"
            
        return ""
