"""
Тесты модуля src/logger
"""

import pytest
import json
from unittest.mock import Mock
from pathlib import Path


class TestJsonFormatter:
    """Тесты JsonFormatter."""

    def test_format(self):
        """Тест форматирования лога."""
        from src.logger.logger import JsonFormatter
        
        formatter = JsonFormatter()
        
        record = Mock()
        record.levelname = "INFO"
        record.getMessage = Mock(return_value="Test message")
        record.pathname = "/test/path.py"
        record.lineno = 123
        record.funcName = "test_func"
        
        result = formatter.format(record)
        
        assert isinstance(result, str)
        log_data = json.loads(result)
        assert log_data['levelname'] == 'INFO'
        assert log_data['message'] == 'Test message'


class TestLogger:
    """Тесты Logger."""

    def test_logger_singleton(self):
        """Тест синглтона логера."""
        from src.logger.logger import Logger
        
        logger1 = Logger()
        logger2 = Logger()
        
        assert logger1 is logger2

    def test_logger_methods(self):
        """Тест методов логера."""
        from src.logger.logger import Logger
        
        logger = Logger()
        
        # Проверка что методы существуют
        assert hasattr(logger, 'info')
        assert hasattr(logger, 'error')
        assert hasattr(logger, 'warning')
        assert hasattr(logger, 'debug')
        assert hasattr(logger, 'critical')

    def test_logger_log(self):
        """Тест логирования."""
        from src.logger.logger import logger
        
        # Проверка что глобальный logger доступен
        assert logger is not None
        assert hasattr(logger, 'info')


class TestLogAnalyzer:
    """Тесты log_analyzer.py."""

    def test_get_max_size_bytes(self):
        """Тест получения максимального размера лога."""
        from src.logger.log_analyzer import get_max_size_bytes
        
        result = get_max_size_bytes()
        
        assert result > 0
