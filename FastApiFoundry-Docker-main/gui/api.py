# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Системный мост (API Bridge)
# =============================================================================
# Описание:
#   Предоставление доступа к функциям операционной системы из JavaScript.
#   Реализация безопасного выполнения команд и работы с файлами.
#
# File: api.py
# Project: Ai Assistant
# Class: Api
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import subprocess
from typing import Optional

class Api:
    """Класс взаимодействия между JS и Python через pywebview bridge."""

    def run_powershell(self, command: str) -> str:
        """Выполнение PowerShell команды.

        Args:
            command (str): Текст команды для выполнения.

        Returns:
            str: Стандартный вывод (stdout) или текст ошибки.

        ПОЧЕМУ -NoProfile:
          Ускорение запуска и предотвращение конфликтов с пользовательскими скриптами профиля.
        """
        if not command:
            return "Error: Empty command"

        try:
            result = subprocess.run(
                ['powershell', '-NoProfile', '-Command', command],
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            return result.stdout if result.returncode == 0 else result.stderr
        except Exception as ex:
            return str(ex)