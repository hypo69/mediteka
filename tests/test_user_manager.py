# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Тесты модуля src/user_manager
# =============================================================================
# Описание:
#   Модуль содержит тесты для модуля управления пользователями. Проверяет
#   получение пути к профилю, структуру профиля по умолчанию и основные
#   функции управления пользователями. Обеспечивает покрытие ключевых
#   сценариев работы с пользовательскими данными.
#
# File: tests/test_user_manager.py
# Project: mediteka
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================
"""
Тесты модуля src/user_manager
"""

import pytest
import sqlite3
from unittest.mock import Mock, patch
from pathlib import Path


class TestUserProfile:
    """Тесты user_profile.py."""

    def test_get_profile_path(self):
        """Тест получения пути к профилю."""
        from src.user_manager.user_profile import _get_profile_path
        
        result = _get_profile_path(1)
        
        assert isinstance(result, Path)
        assert "user_1" in str(result)

    def test_default_profile_structure(self):
        """Тест структуры профиля по умолчанию."""
        from src.user_manager.user_profile import _default_profile_structure
        
        result = _default_profile_structure(1)
        
        assert isinstance(result, dict)
        assert 'last_watched' in result
        assert 'preferences' in result
        assert 'settings' in result

    def test_load_user_profile(self, tmp_path):
        """Тест загрузки профиля."""
        from src.user_manager.user_profile import load_user_profile
        
        user_id = 1
        profile_path = tmp_path / 'user_1_profile.json'
        
        with patch('src.user_manager.user_profile._get_profile_path') as mock_path:
            mock_path.return_value = profile_path
            
            # Профиль не существует - создается новый
            result = load_user_profile(user_id)
            
            assert isinstance(result, dict)

    def test_save_user_profile(self, tmp_path):
        """Тест сохранения профиля."""
        from src.user_manager.user_profile import save_user_profile
        
        user_id = 1
        profile = {'last_watched': 'test'}
        profile_path = tmp_path / 'user_1_profile.json'
        
        with patch('src.user_manager.user_profile._get_profile_path') as mock_path:
            mock_path.return_value = profile_path
            
            result = save_user_profile(user_id, profile)
            
            assert result is True

    def test_update_watch_progress(self, tmp_path):
        """Тест обновления прогресса просмотра."""
        from src.user_manager.user_profile import update_watch_progress
        
        result = update_watch_progress(
            user_id='1',
            file_path='/test/path.mp4',
            file_name='test.mp4',
            current_time=120.5,
            duration=7200.0
        )
        
        assert result is not None


class TestUserManager:
    """Тесты UserManager."""

    def test_init(self, temp_db_path):
        """Тест инициализации UserManager."""
        from src.user_manager import UserManager
        
        manager = UserManager(temp_db_path)
        
        assert manager is not None
        assert manager.db_path == temp_db_path

    def test_add_user(self, temp_db_path):
        """Тест добавления пользователя."""
        from src.user_manager import UserManager
        
        manager = UserManager(temp_db_path)
        
        user_id = manager.add_user(
            email='test@example.com',
            name='Test User',
            role='user'
        )
        
        assert user_id > 0

    def test_get_user_by_id(self, temp_db_path):
        """Тест получения пользователя по ID."""
        from src.user_manager import UserManager
        
        manager = UserManager(temp_db_path)
        
        user_id = manager.add_user(
            email='test@example.com',
            name='Test User'
        )
        
        user = manager.get_user_by_id(user_id)
        
        assert user is not None
        assert user['email'] == 'test@example.com'

    def test_get_user_by_email(self, temp_db_path):
        """Тест получения пользователя по email."""
        from src.user_manager import UserManager
        
        manager = UserManager(temp_db_path)
        
        manager.add_user(
            email='test@example.com',
            name='Test User'
        )
        
        user = manager.get_user_by_email('test@example.com')
        
        assert user is not None
        assert user['email'] == 'test@example.com'

    def test_get_user_settings(self, temp_db_path):
        """Тест получения настроек пользователя."""
        from src.user_manager import UserManager
        
        manager = UserManager(temp_db_path)
        
        user_id = manager.add_user(
            email='test@example.com',
            name='Test User'
        )
        
        settings = manager.get_user_settings(user_id)
        
        assert isinstance(settings, dict)
