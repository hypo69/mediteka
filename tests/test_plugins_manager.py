# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Тесты менеджера плагинов и манифестов
# =============================================================================
# Описание:
#   Тестирование обнаружения плагинов, получения метаданных, манифестов,
#   включения/отключения, сохранения настроек и выполнения действий плагинов.
#
# File: tests/test_plugins_manager.py
# Project: mediteka
# Package: tests
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from plugins import load_plugins, get_all_plugins_registry
from plugins.plugin import BasePlugin
from main import app

client = TestClient(app)


class DummyTestPlugin(BasePlugin):
    name = "dummy_plugin"
    title = "Тестовый плагин"
    description = "Плагин для модульного тестирования"
    icon = "🧪"
    version = "1.0.0"
    category = "tools"

    def get_manifest(self):
        return {
            'name': self.name,
            'title': self.title,
            'description': self.description,
            'icon': self.icon,
            'version': self.version,
            'category': self.category,
            'enabled': self.enabled,
            'config': self.get_config(),
            'fields': [
                {'id': 'test_key', 'label': 'Test Key', 'type': 'string', 'default': 'test_val'}
            ],
            'actions': [
                {'id': 'ping', 'label': 'Ping', 'description': 'Ping test action'}
            ]
        }

    async def action_ping(self, params):
        return {'success': True, 'message': 'pong', 'echo': params.get('echo', '')}

    async def _handle(self, message: str, **kwargs):
        return "dummy_response"


def test_base_plugin_manifest_and_config():
    """Тест базовых методов манифеста и конфигурации BasePlugin."""
    mock_ai = MagicMock()
    plugin = DummyTestPlugin(mock_ai)

    manifest = plugin.get_manifest()
    assert manifest['name'] == 'dummy_plugin'
    assert manifest['title'] == 'Тестовый плагин'
    assert manifest['enabled'] is True
    assert len(manifest['fields']) == 1
    assert len(manifest['actions']) == 1


@pytest.mark.asyncio
async def test_plugin_action_execution():
    """Тест выполнения экшена плагина."""
    mock_ai = MagicMock()
    plugin = DummyTestPlugin(mock_ai)

    res = await plugin.execute_action('ping', {'echo': 'hello'})
    assert res['success'] is True
    assert res['message'] == 'pong'
    assert res['echo'] == 'hello'

    # Несуществующее действие
    res_invalid = await plugin.execute_action('non_existent', {})
    assert res_invalid['success'] is False


def test_load_plugins_and_registry():
    """Тест загрузки всех плагинов и генерации общего реестра."""
    mock_ai = MagicMock()
    plugins = load_plugins(mock_ai)

    assert isinstance(plugins, dict)
    assert len(plugins) > 0

    # Проверка наличия ключевых плагинов
    assert 'media_organizer' in plugins
    assert 'web_search' in plugins
    assert 'qbittorrent' in plugins
    assert 'rag' in plugins

    registry = get_all_plugins_registry(plugins)
    assert isinstance(registry, list)
    assert len(registry) == len(plugins)

    media_org = next((p for p in registry if p['name'] == 'media_organizer'), None)
    assert media_org is not None
    assert media_org['icon'] == '🎬'
    assert len(media_org['actions']) > 0


def test_plugin_endpoints_api():
    """Тест REST API эндпоинтов менеджера плагинов."""
    with TestClient(app) as client:
        # 1. GET /api/admin/plugins
        resp = client.get('/api/admin/plugins')
        assert resp.status_code == 200
        data = resp.json()
        assert 'plugins' in data
        assert data['count'] > 0

        # 2. GET /api/admin/plugins/media_organizer
        resp_mo = client.get('/api/admin/plugins/media_organizer')
        assert resp_mo.status_code == 200
        mo_data = resp_mo.json()
        assert mo_data['plugin']['name'] == 'media_organizer'
        assert len(mo_data['plugin']['actions']) > 0

        # 3. POST /api/admin/plugins/media_organizer/toggle
        resp_toggle = client.post('/api/admin/plugins/media_organizer/toggle', json={'enabled': True})
        assert resp_toggle.status_code == 200
        assert resp_toggle.json()['enabled'] is True
