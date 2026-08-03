## \file src/logger/logger.py
# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Модуль логгера с поддержкой JSON и цветного вывода
# =============================================================================
# Описание:
#   Модуль предоставляет универсальный логгер с поддержкой цветного консольного вывода,
#   записи в файлы (info, debug, errors), а также JSON-форматирования логов. Реализован
#   паттерн Singleton для единого экземпляра логгера по всему приложению.
#
# File: src/logger/logger.py
# Project: mediteka
# Package: src.logger
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

#! .pyenv/bin/python3

"""
.. module:: src.logger.logger
    :platform: Windows, Unix
    :synopsis: Модуль логгера
   
"""


import logging
import colorama
import datetime
import json
import inspect
import threading
from pathlib import Path
from typing import Optional, Tuple
from types import SimpleNamespace

import header
from header import __root__




TEXT_COLORS = {
    "black": colorama.Fore.BLACK,
    "red": colorama.Fore.RED,
    "green": colorama.Fore.GREEN,
    "yellow": colorama.Fore.YELLOW,
    "blue": colorama.Fore.BLUE,
    "magenta": colorama.Fore.MAGENTA,
    "cyan": colorama.Fore.CYAN,
    "white": colorama.Fore.WHITE,
    "light_gray": colorama.Fore.LIGHTBLACK_EX,
    "light_red": colorama.Fore.LIGHTRED_EX,
    "light_green": colorama.Fore.LIGHTGREEN_EX,
    "light_yellow": colorama.Fore.LIGHTYELLOW_EX,
    "light_blue": colorama.Fore.LIGHTBLUE_EX,
    "light_magenta": colorama.Fore.LIGHTMAGENTA_EX,
    "light_cyan": colorama.Fore.LIGHTCYAN_EX,
}

# Словарь для цветов фона
BG_COLORS = {
    "black": colorama.Back.BLACK,
    "red": colorama.Back.RED,
    "green": colorama.Back.GREEN,
    "yellow": colorama.Back.YELLOW,
    "blue": colorama.Back.BLUE,
    "magenta": colorama.Back.MAGENTA,
    "cyan": colorama.Back.CYAN,
    "white": colorama.Back.WHITE,
    "light_gray": colorama.Back.LIGHTBLACK_EX,
    "light_red": colorama.Back.LIGHTRED_EX,
    "light_green": colorama.Back.LIGHTGREEN_EX,
    "light_yellow": colorama.Back.LIGHTYELLOW_EX,
    "light_blue": colorama.Back.LIGHTBLUE_EX,
    "light_magenta": colorama.Back.LIGHTMAGENTA_EX,
    "light_cyan": colorama.Back.LIGHTCYAN_EX,
}


class SingletonMeta(type):
    """ Metaclass for Singleton pattern implementation."""

    _instances = {}
    _lock = threading.Lock()

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            with cls._lock:
                if cls not in cls._instances:
                    instance = super().__call__(*args, **kwargs)
                    cls._instances[cls] = instance
        return cls._instances[cls]


class JsonFormatter(logging.Formatter):
    """ Custom formatter for logging in JSON format."""

    def format(self, record):
        """ Format the log record as JSON."""
        log_entry = {
            "asctime": self.formatTime(record, self.datefmt),
            "levelname": record.levelname,
            "message": record.getMessage().replace('"', "'"),
            "exc_info": self.formatException(record.exc_info)
            if record.exc_info
            else None,
        }
        _json = json.dumps(log_entry, ensure_ascii=False)
        return _json


class Logger(metaclass=SingletonMeta):
    """ Logger class implementing Singleton pattern with console, file, and JSON logging."""
    log_files_path: Path
    info_log_path: Path
    debug_log_path: Path
    errors_log_path: Path
    json_log_path: Path

    def __init__(
        self,
        info_log_path: Optional[str] = None,
        debug_log_path: Optional[str] = None,
        errors_log_path: Optional[str] = None,
        json_log_path: Optional[str] = None,
    ):

        timestamp = datetime.datetime.now().strftime("%d%m%y%H%M")
        self.log_files_path: Path =  __root__ / 'logs'
        self.info_log_path = self.log_files_path / (info_log_path or "info.log")
        self.debug_log_path = self.log_files_path / (debug_log_path or "debug.log")
        self.errors_log_path = self.log_files_path / (errors_log_path or "errors.log")
        self.json_log_path = self.log_files_path / (json_log_path or "log.json")

        # Ensure directories exist
        self.log_files_path.mkdir(parents=True, exist_ok=True)

        # Ensure log files exist
        self.info_log_path.touch(exist_ok=True)
        self.debug_log_path.touch(exist_ok=True)
        self.errors_log_path.touch(exist_ok=True)
        self.json_log_path.touch(exist_ok=True)

        # Console logger
        self.logger_console = logging.getLogger(name="logger_console")
        self.logger_console.setLevel(logging.DEBUG)

        import os
        from dotenv import load_dotenv
        load_dotenv(__root__ / '.env')
        mode_val = os.getenv('MODE', 'dev').lower()
        debug_val = os.getenv('DEBUG', 'true').lower()
        self.is_debug_mode = (mode_val in ('dev', 'debug') or debug_val in ('true', '1', 'yes'))

        # Info file logger
        self.logger_file_info = logging.getLogger(name="logger_file_info")
        self.logger_file_info.setLevel(logging.INFO)
        self.logger_file_info.propagate = False
        info_handler = logging.FileHandler(self.info_log_path, encoding='utf-8')
        info_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
        self.logger_file_info.addHandler(info_handler)

        # Debug file logger
        self.logger_file_debug = logging.getLogger(name="logger_file_debug")
        self.logger_file_debug.setLevel(logging.DEBUG)
        self.logger_file_debug.propagate = False
        debug_handler = logging.FileHandler(self.debug_log_path, encoding='utf-8')
        debug_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
        self.logger_file_debug.addHandler(debug_handler)

        # Errors file logger
        self.logger_file_errors = logging.getLogger(name="logger_file_errors")
        self.logger_file_errors.setLevel(logging.ERROR)
        self.logger_file_errors.propagate = False
        errors_handler = logging.FileHandler(self.errors_log_path, encoding='utf-8')
        errors_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
        self.logger_file_errors.addHandler(errors_handler)


        # JSON file logger
        self.logger_file_json = logging.getLogger(name='logger_json')
        self.logger_file_json.setLevel(logging.DEBUG)
        self.logger_file_json.propagate = False
        json_handler = logging.FileHandler(self.json_log_path, encoding='utf-8')
        json_handler.setFormatter(JsonFormatter())  # Используем наш кастомный форматтер
        self.logger_file_json.addHandler(json_handler)


        # Удаляем все обработчики, которые выводят в консоль
        for handler in self.logger_file_json.handlers:
            if isinstance(handler, logging.StreamHandler):
                self.logger_file_json.removeHandler(handler)

    def _format_message(self, message, ex=None, color: Optional[Tuple[str, str]] = None):
        """ Returns formatted message with optional color and exception information."""
        if color:
            text_color, bg_color = color
            text_color = TEXT_COLORS.get(text_color, colorama.Fore.RESET)
            bg_color = BG_COLORS.get(bg_color, colorama.Back.RESET)
            ex_str = ""
            if ex:
                ex_str = f" {ex}"
            message = f"{text_color}{bg_color}{message}{ex_str}{colorama.Style.RESET_ALL}"
        return message

    def _ex_full_info(self, ex):
        """ Returns full exception information along with the previous function, file, and line details."""
        frame_info = inspect.stack()[3]
        file_name = frame_info.filename
        function_name = frame_info.function
        line_number = frame_info.lineno

        ex_str = ""
        if ex:
            ex_str = f"{ex}"
        return f"\nFile: {file_name}, \n |\n  -Function: {function_name}, \n   |\n    --Line: {line_number}\n{ex_str}"

    def log(self, level, message, ex=None, exc_info=False, color: Optional[Tuple[str, str]] = None):
        """
        Логирует сообщение с заданным уровнем, опциональным цветом и информацией об исключении.

        Args:
            level (int): Уровень логирования (например, logging.INFO).
            message (str): Текстовое сообщение.
            ex (Exception, optional): Исключение для записи.
            exc_info (bool, optional): Включить информацию об исключении в вывод.
            color (tuple, optional): Кортеж (текст, фон) для раскраски сообщения.

        Returns:
            None
        """
        # In PROD mode (not self.is_debug_mode), do not log DEBUG events
        if level == logging.DEBUG and not self.is_debug_mode:
            return

        formatted_message = self._format_message(message, ex, color)
        if exc_info:
            formatted_message += self._ex_full_info(ex)

        if self.logger_console:
            self.logger_console.log(level, formatted_message, exc_info=exc_info)

        if self.logger_file_json:
            self.logger_file_json.log(level, message, exc_info=exc_info)

        if level == logging.INFO and self.logger_file_info:
            self.logger_file_info.log(level, formatted_message)

        if level == logging.DEBUG and self.logger_file_debug:
            self.logger_file_debug.log(level, formatted_message)

        if level in [logging.ERROR, logging.CRITICAL] and self.logger_file_errors:
            self.logger_file_errors.log(level, formatted_message)

    def info(self, message, ex=None, exc_info=False, text_color: str = "green", bg_color: str = ""):
        """
        Логирует сообщение уровня INFO.

        Args:
            message (str): Текстовое сообщение.
            ex (Exception, optional): Исключение.
            exc_info (bool, optional): Включить инфо об исключении.
            text_color (str): Цвет текста.
            bg_color (str): Цвет фона.

        Returns:
            None
        """
        color = (text_color, bg_color)
        self.log(logging.INFO, message, ex, exc_info, color)

    def success(self, message, ex=None, exc_info=False, text_color: str = "yellow", bg_color: str = ""):
        """
        Логирует сообщение об успешной операции.

        Args:
            message (str): Текстовое сообщение.
            ex (Exception, optional): Исключение.
            exc_info (bool, optional): Включить инфо об исключении.
            text_color (str): Цвет текста.
            bg_color (str): Цвет фона.

        Returns:
            None
        """
        color = (text_color, bg_color)
        self.log(logging.INFO, message, ex, exc_info, color)

    def warning(self, message, ex=None, exc_info=False, text_color: str = "black", bg_color: str = "yellow"):
        """
        Логирует сообщение уровня WARNING.

        Args:
            message (str): Текстовое сообщение.
            ex (Exception, optional): Исключение.
            exc_info (bool, optional): Включить инфо об исключении.
            text_color (str): Цвет текста.
            bg_color (str): Цвет фона.

        Returns:
            None
        """
        color = (text_color, bg_color)
        self.log(logging.WARNING, message, ex, exc_info, color)

    def debug(self, message, ex=None, exc_info=True, text_color: str = "cyan", bg_color: str = ""):
        """
        Логирует сообщение уровня DEBUG.

        Args:
            message (str): Текстовое сообщение.
            ex (Exception, optional): Исключение.
            exc_info (bool, optional): Включить инфо об исключении.
            text_color (str): Цвет текста.
            bg_color (str): Цвет фона.

        Returns:
            None
        """
        color = (text_color, bg_color)
        self.log(logging.DEBUG, message, ex, exc_info, color)

    def error(self, message, ex=None, exc_info=True, text_color: str = "red", bg_color: str = ""):
        """
        Логирует сообщение уровня ERROR.

        Args:
            message (str): Текстовое сообщение.
            ex (Exception, optional): Исключение.
            exc_info (bool, optional): Включить инфо об исключении.
            text_color (str): Цвет текста.
            bg_color (str): Цвет фона.

        Returns:
            None
        """
        color = (text_color, bg_color)
        self.log(logging.ERROR, message, ex, exc_info, color)

    def critical(self, message, ex=None, exc_info=True, text_color: str = "red", bg_color: str = "white"):
        """
        Логирует сообщение уровня CRITICAL.

        Args:
            message (str): Текстовое сообщение.
            ex (Exception, optional): Исключение.
            exc_info (bool, optional): Включить инфо об исключении.
            text_color (str): Цвет текста.
            bg_color (str): Цвет фона.

        Returns:
            None
        """
        color = (text_color, bg_color)
        self.log(logging.CRITICAL, message, ex, exc_info, color)

# Initialize logger with file paths
#logger = Logger(info_log_path='info.log', debug_log_path='debug.log', errors_log_path='errors.log', json_log_path='log.json')
logger: Logger = Logger()