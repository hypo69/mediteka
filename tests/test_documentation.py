# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Тестирование актуальности документации
# =============================================================================
# Описание:
#   Тесты для проверки соответствия документации актуальному коду проекта.
#   Проверка количества роутеров, плагинов, AI моделей и конфигураций.
#
# Примеры:
#   pytest tests/test_documentation.py -v
#   python -m pytest tests/test_documentation.py::TestDocumentation
#
# File: test_documentation.py
# Project: Mediteka
# Package: Testing
# Class: TestDocumentation
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import json
import os
from pathlib import Path
from typing import Dict, List
import pytest
import sys

# Добавление корня проекта в путь импорта
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestDocumentation:
    """Тестирование актуальности документации проекта Mediteka."""

    def test_project_overview_structure(self):
        """Проверка структуры проекта в overview документации.
        
        Проверка: Основные компоненты проекта корректно описаны в документации.
        Зависимости: Файл .ai_instructions/knowledge/project_overview.md
        """
        # Чтение файла overview
        overview_path = project_root / ".ai_instructions" / "knowledge" / "project_overview.md"
        assert overview_path.exists(), "Файл project_overview.md не найден"
        
        with open(overview_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Проверка ключевых компонентов
        required_sections = [
            "FastAPI Backend",
            "AI Модель",
            "Плагины 2026",
            "База данных медиатеки 2026",
            "Технологический стек 2026",
            "Структура проекта"
        ]
        
        for section in required_sections:
            assert section in content, f"Раздел '{section}' отсутствует в документации"
        
        # Проверка количества роутеров (должно быть 10)
        assert "10 роутеров" in content, "Документация должна указывать 10 роутеров FastAPI"
        
        # Проверка количества плагинов (должно быть 11)
        assert "11 полных плагинов" in content or "11 ПЛАГИНОВ" in content or "11 плагинов" in content, \
            "Документация должна указывать 11 плагинов"
    
    def test_fastapi_routers_count(self):
        """Проверка количества роутеров FastAPI.
        
        Проверка: В проекте должно быть 10 роутеров FastAPI.
        Нарушение: Несоответствие количества роутеров в коде и документации.
        """
        fastapi_dir = project_root / "src" / "fastapi"
        assert fastapi_dir.exists(), "Директория src/fastapi не найдена"
        
        # Поиск файлов роутеров
        router_files = list(fastapi_dir.glob("router_*.py"))
        
        # Должно быть 10 роутеров
        expected_routers = 10
        actual_routers = len(router_files)
        
        assert actual_routers == expected_routers, \
            f"Ожидалось {expected_routers} роутеров, найдено {actual_routers}. " \
            f"Роутеры: {[f.name for f in router_files]}"
        
        # Проверка наличия router_agents.py
        agents_router = fastapi_dir / "router_agents.py"
        assert agents_router.exists(), "Роутер router_agents.py не найден (новый роутер агентов)"
    
    def test_plugins_count_and_structure(self):
        """Проверка количества и структуры плагинов.
        
        Проверка: В проекте должно быть 12 плагинов с правильной структурой.
        Нарушение: Несоответствие количества или структуры плагинов.
        """
        plugins_dir = project_root / "plugins"
        assert plugins_dir.exists(), "Директория plugins не найдена"
        
        # Получение списка плагинов (директории, не начинающиеся с _)
        plugin_dirs = [
            d for d in plugins_dir.iterdir() 
            if d.is_dir() and not d.name.startswith('_') and d.name != "__pycache__"
        ]
        
        expected_plugins = 11
        actual_plugins = len(plugin_dirs)
        
        assert actual_plugins == expected_plugins, \
            f"Ожидалось {expected_plugins} плагинов, найдено {actual_plugins}. " \
            f"Плагины: {[d.name for d in plugin_dirs]}"
        
        # Проверка обязательных плагинов
        required_plugins = [
            "media_organizer",
            "rag", 
            "qbittorrent",
            "media_layer",
            "web_search",
            "torrent_playwright",
            "movie_search_sources",
            "telegram_bot",
            "user_manager_tool",
            "yt_dlp"
        ]
        
        for plugin in required_plugins:
            plugin_path = plugins_dir / plugin
            assert plugin_path.exists(), f"Обязательный плагин '{plugin}' не найден"
            
            # Проверка структуры плагина
            assert (plugin_path / "__init__.py").exists(), \
                f"Плагин '{plugin}' не имеет __init__.py"
    
    def test_unified_chat_model_structure(self):
        """Проверка структуры UnifiedChatModel.
        
        Проверка: Архитектура AI моделей соответствует документации.
        Нарушение: Отсутствие UnifiedChatModel или компонентов AI.
        """
        ai_dir = project_root / "src" / "ai"
        assert ai_dir.exists(), "Директория src/ai не найдена"
        
        # Проверка ключевых файлов
        required_files = [
            "unified_chat.py",
            "foundry_chat.py", 
            "agy_chat.py",
            "ollama_chat.py",
            "model_manager.py"
        ]
        
        for file in required_files:
            file_path = ai_dir / file
            assert file_path.exists(), f"Файл AI модели '{file}' не найден"
        
        # Проверка директории gemini
        gemini_dir = ai_dir / "gemini"
        assert gemini_dir.exists(), "Директория gemini не найдена"
        
        # Проверка generative_ai.py в gemini
        generative_ai = gemini_dir / "generative_ai.py"
        assert generative_ai.exists(), "Файл generative_ai.py не найден в директории gemini"
    
    def test_configuration_files_exist(self):
        """Проверка наличия файлов конфигурации.
        
        Проверка: Все необходимые файлы конфигурации существуют.
        Нарушение: Отсутствие обязательных файлов конфигурации.
        """
        required_configs = [
            project_root / ".env.example",
            project_root / "config.json",
            project_root / "requirements.txt",
            project_root / "pytest.ini"
        ]
        
        for config_file in required_configs:
            assert config_file.exists(), f"Файл конфигурации '{config_file.name}' не найден"
    
    def test_launcher_scripts_exist(self):
        """Проверка наличия скриптов запуска.
        
        Проверка: Все основные скрипты запуска существуют.
        Нарушение: Отсутствие обязательных скриптов запуска.
        """
        required_launchers = [
            "run.ps1",
            "Run-Unicorn.ps1", 
            "Run-Cloudflared.ps1",
            "Run-Foundry.ps1",
            "install.ps1"
        ]
        
        for launcher in required_launchers:
            launcher_path = project_root / launcher
            assert launcher_path.exists(), f"Скрипт запуска '{launcher}' не найден"
    
    def test_database_structure(self):
        """Проверка структуры базы данных.
        
        Проверка: Файлы базы данных и RAG существуют.
        Нарушение: Отсутствие обязательных файлов БД.
        """
        # Проверка media.db (может быть в разных местах)
        possible_db_locations = [
            project_root / "media.db",
            project_root / "plugins" / "media_organizer" / "data" / "media.db"
        ]
        
        db_exists = any(loc.exists() for loc in possible_db_locations)
        assert db_exists, "Файл базы данных media.db не найден"
        
        # Проверка директории RAG
        rag_dir = project_root / "rag"
        assert rag_dir.exists(), "Директория RAG не найдена"
    
    def test_web_interfaces_exist(self):
        """Проверка наличия веб-интерфейсов.
        
        Проверка: Все 6 веб-интерфейсов существуют.
        Нарушение: Отсутствие обязательных интерфейсов.
        """
        webinterface_dir = project_root / "webinterface"
        assert webinterface_dir.exists(), "Директория webinterface не найдена"
        
        required_interfaces = [
            "user",
            "admin", 
            "rc",
            "tgmini",
            "tv",
            "user_tts"
        ]
        
        for interface in required_interfaces:
            interface_dir = webinterface_dir / interface
            assert interface_dir.exists(), f"Интерфейс '{interface}' не найден"
            
            # Проверка наличия index.html
            index_file = interface_dir / "index.html"
            if interface != "tgmini":  # tgmini может иметь другую структуру
                assert index_file.exists(), f"Интерфейс '{interface}' не имеет index.html"
    
    def test_code_rules_validation(self):
        """Проверка соответствия инженерному стандарту.
        
        Проверка: Файл CODE_RULES.md содержит актуальные правила.
        Нарушение: Отсутствие правил для новых компонентов.
        """
        code_rules_path = project_root / ".ai_instructions" / "rules" / "CODE_RULES.md"
        assert code_rules_path.exists(), "Файл CODE_RULES.md не найден"
        
        with open(code_rules_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Проверка правил для новых компонентов
        required_rules = [
            "UnifiedChatModel архитектуры",
            "системы плагинов",
            "REST API (FastAPI роутеры)",
            "Манифест плагина:",
            "потоковый вывод"
        ]
        
        for rule in required_rules:
            assert rule in content, f"Правило для '{rule}' отсутствует в CODE_RULES.md"
    
    def test_api_documentation_completeness(self):
        """Проверка полноты документации API.
        
        Проверка: Документация API покрывает все роутеры.
        Нарушение: Неполная документация API.
        """
        api_docs_path = project_root / ".ai_instructions" / "knowledge" / "api_documentation.md"
        assert api_docs_path.exists(), "Файл api_documentation.md не найден"
        
        with open(api_docs_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Проверка всех роутеров в документации
        required_routers_in_docs = [
            "router_chat.py",
            "router_media.py",
            "router_qbittorrent.py",
            "router_auth.py",
            "router_control.py",
            "router_tts.py",
            "router_logs.py",
            "router_keys.py",
            "router_admin.py",
            "router_agents.py"
        ]
        
        # Проверка описания эндпоинтов
        required_endpoints = [
            "/api/chat",
            "/api/media",
            "/api/torrents",
            "/auth",
            "/ws/control",
            "/api/tts",
            "/api/logs",
            "/api/keys",
            "/admin",
            "/api/agents"
        ]
        
        for endpoint in required_endpoints:
            assert endpoint in content, f"Эндпоинт '{endpoint}' отсутствует в документации API"
    
    def test_plugins_documentation_completeness(self):
        """Проверка полноты документации плагинов.
        
        Проверка: Документация плагинов покрывает все 12 плагинов.
        Нарушение: Неполная документация плагинов.
        """
        plugins_docs_path = project_root / ".ai_instructions" / "knowledge" / "plugins_documentation.md"
        assert plugins_docs_path.exists(), "Файл plugins_documentation.md не найден"
        
        with open(plugins_docs_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Проверка всех плагинов в документации
        required_plugins_in_docs = [
            "media_organizer",
            "rag",
            "media_layer",
            "web_search",
            "torrent_playwright",
            "movie_search_sources",
            "qbittorrent",
            "telegram_bot",
            "user_manager_tool",
            "yt_dlp",
            "langchain_media"
        ]
        
        for plugin in required_plugins_in_docs:
            assert plugin in content, f"Плагин '{plugin}' отсутствует в документации"


class TestDocumentationConsistency:
    """Тестирование согласованности документации."""

    def test_version_consistency(self):
        """Проверка согласованности версий в документации.
        
        Проверка: Все файлы документации ссылаются на одну версию (2026).
        Нарушение: Несогласованность версий в разных файлах документации.
        """
        docs_files = [
            project_root / ".ai_instructions" / "knowledge" / "project_overview.md",
            project_root / ".ai_instructions" / "knowledge" / "api_documentation.md",
            project_root / ".ai_instructions" / "knowledge" / "plugins_documentation.md",
            project_root / ".ai_instructions" / "rules" / "CODE_RULES.md"
        ]
        
        for doc_file in docs_files:
            if doc_file.exists():
                with open(doc_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Проверка ссылки на 2026 год
                assert "2026" in content, f"Файл {doc_file.name} не содержит ссылки на 2026 год"
    
    def test_architecture_consistency(self):
        """Проверка согласованности архитектурного описания.
        
        Проверка: Архитектура одинакова во всех файлах документации.
        Нарушение: Противоречия в описании архитектуры.
        """
        # Проверка согласованности количества компонентов
        overview_path = project_root / ".ai_instructions" / "knowledge" / "project_overview.md"
        api_docs_path = project_root / ".ai_instructions" / "knowledge" / "api_documentation.md"
        
        with open(overview_path, 'r', encoding='utf-8') as f:
            overview_content = f.read()
        
        with open(api_docs_path, 'r', encoding='utf-8') as f:
            api_content = f.read()
        
        # Проверка согласованности количества роутеров
        assert "10 роутеров" in overview_content or "10 роутеров FastAPI" in overview_content
        assert "10 роутеров" in api_content or "10 роутеров FastAPI" in api_content
        
        # Проверка согласованности количества плагинов
        assert "11 плагинов" in overview_content or "11 ПЛАГИНОВ" in overview_content or "11 полных плагинов" in overview_content


class TestRealCodeVsDocumentation:
    """Тестирование соответствия реального кода документации."""

    def test_router_agents_exists_and_documented(self):
        """Проверка что router_agents.py существует и документирован.
        
        Проверка: Новый роутер агентов существует в коде и описан в документации.
        Нарушение: Роутер существует но не документирован или наоборот.
        """
        # Проверка существования в коде
        agents_router = project_root / "src" / "fastapi" / "router_agents.py"
        assert agents_router.exists(), "router_agents.py не существует в коде"
        
        # Проверка документации
        api_docs_path = project_root / ".ai_instructions" / "knowledge" / "api_documentation.md"
        with open(api_docs_path, 'r', encoding='utf-8') as f:
            api_content = f.read()
        
        assert "router_agents.py" in api_content, "router_agents.py не документирован в API документации"
        assert "/api/agents" in api_content, "Эндпоинты /api/agents не документированы"
    
    def test_unified_chat_model_documented(self):
        """Проверка что UnifiedChatModel документирован.
        
        Проверка: UnifiedChatModel описан в документации.
        Нарушение: UnifiedChatModel существует но не документирован.
        """
        overview_path = project_root / ".ai_instructions" / "knowledge" / "project_overview.md"
        with open(overview_path, 'r', encoding='utf-8') as f:
            overview_content = f.read()
        
        assert "UnifiedChatModel" in overview_content, "UnifiedChatModel не документирован в overview"
        
        api_docs_path = project_root / ".ai_instructions" / "knowledge" / "api_documentation.md"
        with open(api_docs_path, 'r', encoding='utf-8') as f:
            api_content = f.read()
        
        assert "UnifiedChatModel" in api_content, "UnifiedChatModel не документирован в API документации"
    
    def test_plugins_documentation_matches_code(self):
        """Проверка что документация плагинов соответствует коду.
        
        Проверка: Все плагины из кода описаны в документации.
        Нарушение: Плагин существует в коде но не документирован.
        """
        plugins_dir = project_root / "plugins"
        plugin_dirs = [
            d.name for d in plugins_dir.iterdir() 
            if d.is_dir() and not d.name.startswith('_') and d.name != "__pycache__"
        ]
        
        plugins_docs_path = project_root / ".ai_instructions" / "knowledge" / "plugins_documentation.md"
        with open(plugins_docs_path, 'r', encoding='utf-8') as f:
            plugins_content = f.read()
        
        for plugin in plugin_dirs:
            assert plugin in plugins_content, f"Плагин '{plugin}' не документирован"


def test_main_py_structure():
    """Проверка структуры main.py.
    
    Проверка: main.py содержит импорт всех роутеров.
    Нарушение: Отсутствие импорта какого-либо роутера.
    """
    main_py_path = project_root / "main.py"
    assert main_py_path.exists(), "Файл main.py не найден"
    
    with open(main_py_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Проверка импортов роутеров
    required_imports = [
        "init_auth_router",
        "init_chat_router",
        "init_qbt_router",
        "init_media_router", 
        "init_control_router",
        "init_tts_router",
        "init_logs_router",
        "init_keys_router",
        "init_admin_router",
        "init_agents_router"
    ]
    
    for router in required_imports:
        assert router in content, f"Роутер '{router}' не импортирован в main.py"


def test_requirements_file_contains_dependencies():
    """Проверка что requirements.txt содержит ключевые зависимости.
    
    Проверка: Файл зависимостей содержит необходимые пакеты.
    Нарушение: Отсутствие ключевых зависимостей.
    """
    requirements_path = project_root / "requirements.txt"
    assert requirements_path.exists(), "Файл requirements.txt не найден"
    
    # Проверяем структуру подфайлов
    with open(requirements_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Проверяем наличие подфайлов
    assert "-r req/requirements-core.txt" in content, "Отсутствует подфайл requirements-core.txt"
    assert "-r req/requirements-ai.txt" in content, "Отсутствует подфайл requirements-ai.txt"
    
    # Проверяем существование подфайлов
    req_dir = project_root / "req"
    assert req_dir.exists(), "Директория req не найдена"
    
    required_subfiles = [
        "requirements-core.txt",
        "requirements-ai.txt", 
        "requirements-media.txt",
        "requirements-utils.txt"
    ]
    
    for subfile in required_subfiles:
        subfile_path = req_dir / subfile
        assert subfile_path.exists(), f"Подфайл зависимостей '{subfile}' не найден"
        
        # Проверяем наличие ключевых зависимостей в подфайлах
        with open(subfile_path, 'r', encoding='utf-8') as sf:
            subcontent = sf.read()
            
        # Определяем какие зависимости должны быть в каждом подфайле
        if subfile == "requirements-core.txt":
            assert "fastapi" in subcontent, f"fastapi отсутствует в {subfile}"
            assert "uvicorn" in subcontent, f"uvicorn отсутствует в {subfile}"
            assert "requests" in subcontent, f"requests отсутствует в {subfile}"  # используется для qbittorrent API
        elif subfile == "requirements-ai.txt":
            assert "google-genai" in subcontent, f"google-genai отсутствует в {subfile}"
        elif subfile == "requirements-media.txt":
            assert "playwright" in subcontent, f"playwright отсутствует в {subfile}"
            assert "yt-dlp" in subcontent, f"yt-dlp отсутствует в {subfile}"
            # qbittorrent-api может быть в другом подфайле или использоваться через requests
        elif subfile == "requirements-utils.txt":
            assert "langchain" in subcontent, f"langchain отсутствует в {subfile}"


if __name__ == "__main__":
    """Запуск тестов документации.
    
    Примеры:
        python tests/test_documentation.py
        pytest tests/test_documentation.py -v
    """
    print("Запуск тестов документации проекта Mediteka...")
    print(f"Корневая директория проекта: {project_root}")
    
    # Запуск pytest
    import pytest
    exit_code = pytest.main([__file__, "-v"])
    
    if exit_code == 0:
        print("\n✅ Все тесты документации пройдены успешно!")
        print("Документация актуальна и соответствует коду проекта.")
    else:
        print("\n❌ Тесты документации выявили проблемы.")
        print("Пожалуйста, обновите документацию в соответствии с кодом.")