# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Тестирование конфигурации проекта
# =============================================================================
# Описание:
#   Тесты для проверки конфигурационных файлов проекта Mediteka.
#   Проверка структуры config.json, .env.example и других конфигураций.
#
# Примеры:
#   pytest tests/test_configuration.py -v
#   python -m pytest tests/test_configuration.py::TestConfiguration
#
# File: test_configuration.py
# Project: Mediteka
# Package: Testing
# Class: TestConfiguration
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import json
import os
from pathlib import Path
import pytest
import sys

# Добавление корня проекта в путь импорта
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestConfiguration:
    """Тестирование конфигурационных файлов проекта Mediteka."""

    def test_config_json_structure(self):
        """Проверка структуры config.json.
        
        Проверка: Файл config.json содержит все необходимые секции.
        Нарушение: Отсутствие обязательных секций конфигурации.
        """
        config_path = project_root / "config.json"
        assert config_path.exists(), "Файл config.json не найден"
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Проверка обязательных секций
        required_sections = ["server", "ai", "plugins"]
        
        for section in required_sections:
            assert section in config, f"Секция '{section}' отсутствует в config.json"
        
        # Проверка структуры сервера
        assert "host" in config["server"], "Отсутствует host в конфигурации сервера"
        assert "port" in config["server"], "Отсутствует port в конфигурации сервера"
        
        # Проверка AI конфигурации
        ai_config = config.get("ai", {})
        assert isinstance(ai_config, dict), "Секция ai должна быть словарем"
        
        # Проверка конфигурации плагинов
        plugins_config = config.get("plugins", {})
        assert isinstance(plugins_config, dict), "Секция plugins должна быть словарем"
    
    def test_env_example_structure(self):
        """Проверка структуры .env.example.
        
        Проверка: Файл .env.example содержит все необходимые переменные.
        Нарушение: Отсутствие обязательных переменных окружения.
        """
        env_example_path = project_root / ".env.example"
        assert env_example_path.exists(), "Файл .env.example не найден"
        
        with open(env_example_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Проверка обязательных переменных
        required_variables = [
            "GEMINI_API_KEY_NAMES",
            "FOUNDRY_API_KEY",
            "FOUNDRY_BASE_URL",
            "QBT_HOST",
            "QBT_PORT",
            "QBT_USER",
            "QBT_PASS",
            "DISABLED_PLUGINS"
        ]
        
        for var in required_variables:
            assert var in content, f"Переменная окружения '{var}' отсутствует в .env.example"
        
        # Проверка комментариев к переменным
        assert "# Токен HuggingFace" in content or "# HuggingFace Token" in content
        assert "# qBittorrent" in content or "# QBittorrent configuration" in content
    
    def test_requirements_files_exist(self):
        """Проверка наличия файлов зависимостей.
        
        Проверка: Все файлы требований существуют.
        Нарушение: Отсутствие файлов зависимостей.
        """
        required_files = [
            "requirements.txt",
            "requirements-test.txt",
            "requirements-docs.txt",
            "docs-requirements.txt"
        ]
        
        for file_name in required_files:
            file_path = project_root / file_name
            assert file_path.exists(), f"Файл зависимостей '{file_name}' не найден"
            
            # Проверка что файл не пустой
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            assert len(content) > 0, f"Файл зависимостей '{file_name}' пустой"
    
    def test_pytest_configuration(self):
        """Проверка конфигурации pytest.
        
        Проверка: Файлы конфигурации pytest существуют и корректны.
        Нарушение: Неправильная конфигурация тестирования.
        """
        # Проверка pytest.ini
        pytest_ini_path = project_root / "pytest.ini"
        assert pytest_ini_path.exists(), "Файл pytest.ini не найден"
        
        with open(pytest_ini_path, 'r', encoding='utf-8') as f:
            pytest_ini_content = f.read()
        
        assert "[tool:pytest]" in pytest_ini_content or "[pytest]" in pytest_ini_content
        
        # Проверка conftest.py
        conftest_path = project_root / "conftest.py"
        assert conftest_path.exists(), "Файл conftest.py не найден"
        
        # Проверка .coveragerc
        coveragerc_path = project_root / ".coveragerc"
        assert coveragerc_path.exists(), "Файл .coveragerc не найден"
        
        with open(coveragerc_path, 'r', encoding='utf-8') as f:
            coveragerc_content = f.read()
        
        assert "[run]" in coveragerc_content
        assert "[report]" in coveragerc_content or "[html]" in coveragerc_content
    
    def test_mkdocs_configuration(self):
        """Проверка конфигурации документации MkDocs.
        
        Проверка: Файл mkdocs.yml существует и корректно настроен.
        Нарушение: Неправильная конфигурация документации.
        """
        mkdocs_path = project_root / "mkdocs.yml"
        assert mkdocs_path.exists(), "Файл mkdocs.yml не найден"
        
        with open(mkdocs_path, 'r', encoding='utf-8') as f:
            mkdocs_content = f.read()
        
        # Проверка основных секций
        assert "site_name:" in mkdocs_content
        assert "nav:" in mkdocs_content or "pages:" in mkdocs_content
        assert "theme:" in mkdocs_content
    
    def test_plugin_configurations_exist(self):
        """Проверка конфигураций плагинов.
        
        Проверка: Основные плагины имеют файлы конфигурации.
        Нарушение: Отсутствие конфигурации у обязательных плагинов.
        """
        plugins_with_config = [
            "media_organizer",
            "qbittorrent",
            "rag",
            "yt_dlp"
        ]
        
        for plugin in plugins_with_config:
            config_path = project_root / "plugins" / plugin / "config.json"
            # config.json может быть опциональным
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                assert isinstance(config, dict), f"Конфигурация плагина '{plugin}' должна быть словарем"
    
    def test_ai_model_configurations(self):
        """Проверка конфигураций AI моделей.
        
        Проверка: Файлы конфигурации AI моделей существуют.
        Нарушение: Отсутствие конфигурации AI моделей.
        """
        # Проверка config.json в fastapi директории
        fastapi_config_path = project_root / "src" / "fastapi" / "config.json"
        if fastapi_config_path.exists():
            with open(fastapi_config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Проверка что конфигурация содержит настройки сервера
            assert "server" in config or "host" in config or "port" in config
    
    def test_security_configurations(self):
        """Проверка конфигураций безопасности.
        
        Проверка: Наличие конфигураций для безопасности.
        Нарушение: Отсутствие базовых конфигураций безопасности.
        """
        # Проверка .gitignore
        gitignore_path = project_root / ".gitignore"
        assert gitignore_path.exists(), "Файл .gitignore не найден"
        
        with open(gitignore_path, 'r', encoding='utf-8') as f:
            gitignore_content = f.read()
        
        # Проверка что секретные файлы в .gitignore
        assert ".env" in gitignore_content
        assert "*.pyc" in gitignore_content
        assert "__pycache__" in gitignore_content
        
        # Проверка .gitattributes если есть
        gitattributes_path = project_root / ".gitattributes"
        if gitattributes_path.exists():
            with open(gitattributes_path, 'r', encoding='utf-8') as f:
                gitattributes_content = f.read()
            assert len(gitattributes_content) > 0
    
    def test_build_configurations(self):
        """Проверка конфигураций сборки.
        
        Проверка: Наличие конфигураций для сборки и деплоя.
        Нарушение: Отсутствие конфигураций сборки.
        """
        # Проверка pyproject.toml если есть
        pyproject_path = project_root / "pyproject.toml"
        if pyproject_path.exists():
            with open(pyproject_path, 'r', encoding='utf-8') as f:
                pyproject_content = f.read()
            assert "[tool." in pyproject_content or "[build-system]" in pyproject_content
        
        # Проверка setup.cfg если есть
        setup_cfg_path = project_root / "setup.cfg"
        if setup_cfg_path.exists():
            with open(setup_cfg_path, 'r', encoding='utf-8') as f:
                setup_cfg_content = f.read()
            assert "[metadata]" in setup_cfg_content or "[options]" in setup_cfg_content
        
        # Проверка .readthedocs.yml
        rtd_path = project_root / ".readthedocs.yml"
        if rtd_path.exists():
            with open(rtd_path, 'r', encoding='utf-8') as f:
                rtd_content = f.read()
            assert "version:" in rtd_content or "build:" in rtd_content


class TestConfigurationValidation:
    """Тестирование валидности конфигураций."""

    def test_config_json_is_valid_json(self):
        """Проверка что config.json является валидным JSON.
        
        Проверка: Файл config.json может быть корректно разобран.
        Нарушение: Невалидный JSON в config.json.
        """
        config_path = project_root / "config.json"
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Дополнительная проверка структуры
            assert isinstance(config, dict), "config.json должен содержать объект верхнего уровня"
            
        except json.JSONDecodeError as e:
            pytest.fail(f"config.json содержит невалидный JSON: {e}")
    
    def test_env_example_format(self):
        """Проверка формата .env.example.
        
        Проверка: .env.example имеет правильный формат переменных окружения.
        Нарушение: Неправильный формат переменных в .env.example.
        """
        env_example_path = project_root / ".env.example"
        
        with open(env_example_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Проверка формата ключевых переменных
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                # Проверка что строка содержит = (переменная=значение)
                assert '=' in line, f"Строка в .env.example не содержит '=': {line}"
                
                parts = line.split('=', 1)
                assert len(parts) == 2, f"Неправильный формат строки в .env.example: {line}"
                
                key = parts[0].strip()
                value = parts[1].strip()
                
                # Проверка что ключ не пустой
                assert len(key) > 0, f"Пустой ключ в .env.example: {line}"
                
                # Проверка что ключ содержит только допустимые символы
                assert key.replace('_', '').isalnum(), f"Недопустимые символы в ключе: {key}"
    
    def test_plugin_configs_are_valid_json(self):
        """Проверка что конфигурации плагинов являются валидным JSON.
        
        Проверка: Все config.json в плагинах могут быть корректно разобраны.
        Нарушение: Невалидный JSON в конфигурациях плагин��в.
        """
        plugins_dir = project_root / "plugins"
        
        for plugin_dir in plugins_dir.iterdir():
            if not plugin_dir.is_dir() or plugin_dir.name.startswith('_'):
                continue
            
            config_path = plugin_dir / "config.json"
            if config_path.exists():
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                    
                    # Проверка что конфигурация является словарем
                    assert isinstance(config, dict), \
                        f"Конфигурация плагина '{plugin_dir.name}' должна быть словарем"
                    
                except json.JSONDecodeError as e:
                    pytest.fail(f"config.json в плагине '{plugin_dir.name}' содержит невалидный JSON: {e}")
    
    def test_no_hardcoded_secrets_in_config(self):
        """Проверка что в config.json нет жестко закодированных секретов.
        
        Проверка: Секреты используют переменные окружения через ${VAR}.
        Нарушение: Жестко закодированные секреты в config.json.
        """
        config_path = project_root / "config.json"
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config_str = f.read()
        
        # Проверка на наличие подозрительных жестко закодированных значений
        suspicious_patterns = [
            "password\": \"",
            "secret\": \"", 
            "key\": \"",
            "token\": \""
        ]
        
        for pattern in suspicious_patterns:
            # Игнорируем если значение содержит ${ (переменная окружения)
            if pattern in config_str:
                # Ищем строки содержащие паттерн
                lines = config_str.split('\n')
                for i, line in enumerate(lines, 1):
                    if pattern in line and '${' not in line:
                        # Проверяем что это не комментарий и не пример
                        if not any(comment in line for comment in ['//', '#', 'example', 'Пример']):
                            pytest.fail(
                                f"Возможно жестко закодированный секрет в config.json, строка {i}:\n{line}"
                            )


def test_launcher_scripts_content():
    """Проверка содержания скриптов запуска.
    
    Проверка: Скрипты запуска содержат необходимые команды.
    Нарушение: Скрипты запуска не содержат ключевых команд.
    """
    launcher_scripts = [
        "run.ps1",
        "Run-Unicorn.ps1",
        "Run-Cloudflared.ps1",
        "Run-Foundry.ps1"
    ]
    
    for script in launcher_scripts:
        script_path = project_root / script
        if script_path.exists():
            with open(script_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Проверка что скрипт не пустой
            assert len(content.strip()) > 0, f"Скрипт '{script}' пустой"
            
            # Проверка содержания в зависимости от скрипта
            if script == "run.ps1":
                assert "python" in content or "uvicorn" in content or "fastapi" in content
            elif script == "Run-Unicorn.ps1":
                assert "uvicorn" in content or "main:app" in content
            elif script == "Run-Cloudflared.ps1":
                assert "cloudflared" in content
            elif script == "Run-Foundry.ps1":
                assert "foundry" in content or "Foundry" in content


if __name__ == "__main__":
    """Запуск тестов конфигурации.
    
    Примеры:
        python tests/test_configuration.py
        pytest tests/test_configuration.py -v
    """
    print("Запуск тестов конфигурации проекта Mediteka...")
    print(f"Корневая директория проекта: {project_root}")
    
    # Запуск pytest
    import pytest
    exit_code = pytest.main([__file__, "-v"])
    
    if exit_code == 0:
        print("\n✅ Все тесты конфигурации пройдены успешно!")
        print("Конфигурационные файлы корректны и полны.")
    else:
        print("\n❌ Тесты конфигурации выявили проблемы.")
        print("Пожалуйста, проверьте конфигурационные файлы.")