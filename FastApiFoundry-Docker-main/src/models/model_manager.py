# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Model Manager for FastAPI Foundry
# =============================================================================
# Description:
#   Manager for controlling AI model connections and configuration.
#   Supports providers: Foundry, Ollama, OpenAI, Anthropic, Custom.
#
# File: model_manager.py
# Project: Ai Assistant (Docker)
# Version: 0.5.5
# Changes in 0.5.5:
#   - Added try/except with logging in load_config, save_config,
#     connect_model, disconnect_model, update_model, test_model_connection,
#     all _test_* provider methods
#   - Each except block explains why the error can occur
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import asyncio
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiohttp

from config_manager import config
from ..utils.logging_system import get_logger

logger = get_logger('model-manager')


class ModelManager:
    """Manager for connected AI models."""

    def __init__(self) -> None:
        self.connected_models: Dict[str, Dict[str, Any]] = {}
        self.providers_config: Dict[str, Any] = {
            'foundry':   {'name': 'Foundry AI',       'requires_api_key': False, 'default_endpoint': config.foundry_base_url,          'supported_features': ['text_generation', 'chat', 'embeddings']},
            'ollama':    {'name': 'Ollama',            'requires_api_key': False, 'default_endpoint': 'http://localhost:11434/api/',     'supported_features': ['text_generation', 'chat', 'embeddings']},
            'openai':    {'name': 'OpenAI',            'requires_api_key': True,  'default_endpoint': 'https://api.openai.com/v1/',      'supported_features': ['text_generation', 'chat', 'embeddings', 'function_calling']},
            'anthropic': {'name': 'Anthropic',         'requires_api_key': True,  'default_endpoint': 'https://api.anthropic.com/v1/',  'supported_features': ['text_generation', 'chat']},
            'lmstudio':  {'name': 'LM Studio',         'requires_api_key': False, 'default_endpoint': config.lmstudio_base_url,          'supported_features': ['text_generation', 'chat', 'model_management']},
            'custom':    {'name': 'Custom Provider',   'requires_api_key': False, 'default_endpoint': None,                             'supported_features': ['text_generation']},
        }
        self.config_file = Path('models_config.json')
        self.load_config()

    # ── Persistence ───────────────────────────────────────────────────────

    def load_config(self) -> None:
        """Load model configuration from models_config.json."""
        if not self.config_file.exists():
            logger.info('models_config.json not found — creating default Foundry model')
            self.add_default_foundry_model()
            return

        try:
            with open(self.config_file, encoding='utf-8') as f:
                data = json.load(f)
            self.connected_models = data.get('connected_models', {})
            logger.info(f'Model config loaded: {len(self.connected_models)} models')
        except json.JSONDecodeError as e:
            # models_config.json is malformed — reset to empty to avoid crash loop
            logger.error(f'❌ models_config.json contains invalid JSON: {e}')
            self.connected_models = {}
        except OSError as e:
            # File exists but cannot be read (permissions, lock)
            logger.error(f'❌ Cannot read models_config.json: {e}')
            self.connected_models = {}

    def save_config(self) -> None:
        """Persist model configuration to models_config.json."""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(
                    {'connected_models': self.connected_models, 'last_updated': datetime.now().isoformat()},
                    f, indent=2, ensure_ascii=False, default=str,
                )
        except OSError as e:
            # Disk full or permission denied — config updated in memory only
            logger.error(f'❌ Failed to save models_config.json: {e}')

    def add_default_foundry_model(self) -> None:
        """Add the default Foundry model entry."""
        self.connected_models[config.foundry_default_model] = {
            'model_id':           config.foundry_default_model,
            'model_name':         'Foundry Default Model',
            'provider':           'foundry',
            'endpoint_url':       config.foundry_base_url,
            'api_key':            None,
            'parameters':         {'temperature': config.foundry_temperature, 'max_tokens': config.foundry_max_tokens},
            'default_temperature': config.foundry_temperature,
            'default_max_tokens': config.foundry_max_tokens,
            'enabled':            True,
            'status':             'unknown',
            'last_check':         datetime.now(),
            'usage_count':        0,
            'avg_response_time':  None,
            'created_at':         datetime.now(),
        }
        self.save_config()

    # ── CRUD ──────────────────────────────────────────────────────────────

    async def connect_model(self, model_data: Dict[str, Any]) -> Dict[str, Any]:
        """Connect a new model.

        Args:
            model_data: Dict with keys: model_id, provider, model_name (opt),
                        endpoint_url (opt), api_key (opt), parameters (opt),
                        default_temperature (opt), default_max_tokens (opt), enabled (opt).

        Returns:
            dict: success, model_id, status on success; success=False, error on failure.
        """
        model_id = model_data['model_id']
        if model_id in self.connected_models:
            return {'success': False, 'model_id': model_id, 'error': 'Model already connected'}

        try:
            provider = model_data['provider']
            model_cfg: Dict[str, Any] = {
                'model_id':           model_id,
                'model_name':         model_data.get('model_name', model_id),
                'provider':           provider,
                'endpoint_url':       model_data.get('endpoint_url') or self.providers_config[provider]['default_endpoint'],
                'api_key':            model_data.get('api_key'),
                'parameters':         model_data.get('parameters', {}),
                'default_temperature': model_data.get('default_temperature', 0.7),
                'default_max_tokens': model_data.get('default_max_tokens', 2048),
                'enabled':            model_data.get('enabled', True),
                'status':             'unknown',
                'last_check':         datetime.now(),
                'usage_count':        0,
                'avg_response_time':  None,
                'created_at':         datetime.now(),
            }
            test = await self.test_model_connection(model_cfg)
            model_cfg['status'] = 'online' if test['success'] else 'offline'
            self.connected_models[model_id] = model_cfg
            self.save_config()
            logger.info(f'✅ Model connected: {model_id} ({model_cfg["status"]})')
            return {'success': True, 'model_id': model_id, 'status': model_cfg['status']}
        except KeyError as e:
            # model_data missing required field or unknown provider
            logger.error(f'❌ connect_model: missing field {e} for model_id={model_id}')
            return {'success': False, 'model_id': model_id, 'error': f'Missing field: {e}'}
        except Exception as e:
            logger.error(f'❌ connect_model failed for {model_id}: {e}')
            return {'success': False, 'model_id': model_id, 'error': str(e)}

    async def disconnect_model(self, model_id: str) -> Dict[str, Any]:
        """Disconnect a model.

        Args:
            model_id: ID of the model to disconnect.

        Returns:
            dict: success, model_id on success; success=False, error on failure.
        """
        if model_id not in self.connected_models:
            return {'success': False, 'model_id': model_id, 'error': 'Model not found'}
        try:
            del self.connected_models[model_id]
            self.save_config()
            return {'success': True, 'model_id': model_id}
        except Exception as e:
            # Unexpected error during dict mutation or save
            logger.error(f'❌ disconnect_model failed for {model_id}: {e}')
            return {'success': False, 'model_id': model_id, 'error': str(e)}

    async def update_model(self, model_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update model settings.

        Args:
            model_id: ID of the model to update.
            update_data: Dict with any of: model_name, enabled, default_temperature,
                         default_max_tokens, api_key, parameters.

        Returns:
            dict: success, model_id, status on success; success=False, error on failure.
        """
        if model_id not in self.connected_models:
            return {'success': False, 'model_id': model_id, 'error': 'Model not found'}
        try:
            cfg = self.connected_models[model_id]
            for field in ('model_name', 'enabled', 'default_temperature', 'default_max_tokens', 'api_key'):
                if field in update_data:
                    cfg[field] = update_data[field]
            if 'parameters' in update_data:
                cfg['parameters'].update(update_data['parameters'])
            cfg['updated_at'] = datetime.now()

            if cfg['enabled']:
                test = await self.test_model_connection(cfg)
                cfg['status'] = 'online' if test['success'] else 'offline'
            else:
                cfg['status'] = 'disabled'

            self.save_config()
            return {'success': True, 'model_id': model_id, 'status': cfg['status']}
        except Exception as e:
            logger.error(f'❌ update_model failed for {model_id}: {e}')
            return {'success': False, 'model_id': model_id, 'error': str(e)}

    # ── Connection tests ──────────────────────────────────────────────────

    async def test_model_connection(self, model_cfg: Dict[str, Any],
                                    test_prompt: str = 'Hello') -> Dict[str, Any]:
        """Test connectivity to a model endpoint.

        Args:
            model_cfg: Model configuration dict (must contain model_id, provider, endpoint_url).
            test_prompt: Short prompt to send as a connectivity test.

        Returns:
            dict: success, model_id, response_text, response_time on success;
                  success=False, error, response_time on failure.
        """
        start = time.time()
        provider = model_cfg.get('provider', 'custom')
        _test_map = {
            'foundry':   self._test_foundry_model,
            'ollama':    self._test_ollama_model,
            'openai':    self._test_openai_model,
            'anthropic': self._test_anthropic_model,
            'lmstudio':  self._test_lmstudio_model,
        }
        try:
            fn = _test_map.get(provider, self._test_custom_model)
            result = await fn(model_cfg, test_prompt)
            result['response_time'] = time.time() - start
            if result['success']:
                model_cfg['last_check'] = datetime.now()
                avg = model_cfg.get('avg_response_time')
                model_cfg['avg_response_time'] = result['response_time'] if avg is None else (avg + result['response_time']) / 2
            return result
        except Exception as e:
            logger.error(f'❌ test_model_connection failed for {model_cfg["model_id"]}: {e}')
            return {'success': False, 'model_id': model_cfg['model_id'], 'error': str(e), 'response_time': time.time() - start}

    async def _test_foundry_model(self, cfg: Dict[str, Any], prompt: str) -> Dict[str, Any]:
        endpoint = cfg.get('endpoint_url') or config.foundry_base_url
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{endpoint.rstrip('/')}/chat/completions",
                    json={'model': cfg['model_id'], 'messages': [{'role': 'user', 'content': prompt}], 'max_tokens': 50},
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return {'success': True, 'model_id': cfg['model_id'],
                                'response_text': data.get('choices', [{}])[0].get('message', {}).get('content', '')}
                    return {'success': False, 'model_id': cfg['model_id'], 'error': f'HTTP {resp.status}'}
        except aiohttp.ClientError as e:
            # Network error: Foundry not running or wrong port
            logger.error(f'❌ Foundry connection error for {cfg["model_id"]}: {e}')
            return {'success': False, 'model_id': cfg['model_id'], 'error': str(e)}

    async def _test_ollama_model(self, cfg: Dict[str, Any], prompt: str) -> Dict[str, Any]:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{cfg['endpoint_url'].rstrip('/')}/generate",
                    json={'model': cfg['model_id'], 'prompt': prompt, 'stream': False},
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return {'success': True, 'model_id': cfg['model_id'], 'response_text': data.get('response', '')}
                    return {'success': False, 'model_id': cfg['model_id'], 'error': f'HTTP {resp.status}'}
        except aiohttp.ClientError as e:
            # Ollama not running or wrong endpoint
            logger.error(f'❌ Ollama connection error for {cfg["model_id"]}: {e}')
            return {'success': False, 'model_id': cfg['model_id'], 'error': str(e)}

    async def _test_openai_model(self, cfg: Dict[str, Any], prompt: str) -> Dict[str, Any]:
        if not cfg.get('api_key'):
            return {'success': False, 'model_id': cfg['model_id'], 'error': 'API key required for OpenAI'}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{cfg['endpoint_url'].rstrip('/')}/chat/completions",
                    headers={'Authorization': f"Bearer {cfg['api_key']}"},
                    json={'model': cfg['model_id'], 'messages': [{'role': 'user', 'content': prompt}], 'max_tokens': 50},
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return {'success': True, 'model_id': cfg['model_id'],
                                'response_text': data.get('choices', [{}])[0].get('message', {}).get('content', '')}
                    return {'success': False, 'model_id': cfg['model_id'], 'error': f'HTTP {resp.status}'}
        except aiohttp.ClientError as e:
            # Network error or invalid API key causing connection reset
            logger.error(f'❌ OpenAI connection error for {cfg["model_id"]}: {e}')
            return {'success': False, 'model_id': cfg['model_id'], 'error': str(e)}

    async def _test_anthropic_model(self, cfg: Dict[str, Any], prompt: str) -> Dict[str, Any]:
        if not cfg.get('api_key'):
            return {'success': False, 'model_id': cfg['model_id'], 'error': 'API key required for Anthropic'}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{cfg['endpoint_url'].rstrip('/')}/messages",
                    headers={'x-api-key': cfg['api_key'], 'anthropic-version': '2023-06-01'},
                    json={'model': cfg['model_id'], 'max_tokens': 50, 'messages': [{'role': 'user', 'content': prompt}]},
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return {'success': True, 'model_id': cfg['model_id'],
                                'response_text': data.get('content', [{}])[0].get('text', '')}
                    return {'success': False, 'model_id': cfg['model_id'], 'error': f'HTTP {resp.status}'}
        except aiohttp.ClientError as e:
            # Network error or Anthropic API rate limit causing connection drop
            logger.error(f'❌ Anthropic connection error for {cfg["model_id"]}: {e}')
            return {'success': False, 'model_id': cfg['model_id'], 'error': str(e)}

    async def _test_lmstudio_model(self, cfg: Dict[str, Any], prompt: str) -> Dict[str, Any]:
        endpoint = (cfg.get('endpoint_url') or config.lmstudio_base_url).rstrip('/')
        headers = {'Content-Type': 'application/json'}
        if cfg.get('api_key') or config.lmstudio_api_key:
            headers['Authorization'] = f"Bearer {cfg.get('api_key') or config.lmstudio_api_key}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{endpoint}/api/v1/chat",
                    headers=headers,
                    json={'model': cfg['model_id'], 'input': prompt, 'max_output_tokens': 50, 'store': False},
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        content = ''
                        for item in data.get('output', []):
                            if item.get('type') == 'message':
                                content += item.get('content', '')
                        return {'success': True, 'model_id': cfg['model_id'], 'response_text': content}
                    return {'success': False, 'model_id': cfg['model_id'], 'error': f'HTTP {resp.status}'}
        except aiohttp.ClientError as e:
            logger.error(f'❌ LM Studio connection error for {cfg["model_id"]}: {e}')
            return {'success': False, 'model_id': cfg['model_id'], 'error': str(e)}

    async def _test_custom_model(self, cfg: Dict[str, Any], prompt: str) -> Dict[str, Any]:
        try:
            headers = {'Content-Type': 'application/json'}
            if cfg.get('api_key'):
                headers['Authorization'] = f"Bearer {cfg['api_key']}"
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    cfg['endpoint_url'],
                    headers=headers,
                    json={'model': cfg['model_id'], 'prompt': prompt, 'max_tokens': 50},
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return {'success': True, 'model_id': cfg['model_id'], 'response_text': str(data)}
                    return {'success': False, 'model_id': cfg['model_id'], 'error': f'HTTP {resp.status}'}
        except aiohttp.ClientError as e:
            # Custom endpoint unreachable or wrong URL format
            logger.error(f'❌ Custom model connection error for {cfg["model_id"]}: {e}')
            return {'success': False, 'model_id': cfg['model_id'], 'error': str(e)}

    # ── Queries ───────────────────────────────────────────────────────────

    async def check_all_models_health(self) -> None:
        """Check health of all enabled connected models."""
        for model_id, cfg in self.connected_models.items():
            if cfg.get('enabled'):
                test = await self.test_model_connection(cfg, 'ping')
                cfg['status'] = 'online' if test['success'] else 'offline'
                cfg['last_check'] = datetime.now()
        self.save_config()

    def get_connected_models(self) -> Dict[str, Any]:
        """Return list of connected models with status.

        Returns:
            dict: success, models (list), total_count, online_count,
                  default_model, timestamp.
        """
        models_list = []
        online_count = 0
        for model_id, cfg in self.connected_models.items():
            models_list.append({
                'model_id':          model_id,
                'model_name':        cfg['model_name'],
                'provider':          cfg['provider'],
                'endpoint_url':      cfg.get('endpoint_url'),
                'enabled':           cfg['enabled'],
                'status':            cfg['status'],
                'last_check':        cfg['last_check'],
                'parameters':        cfg.get('parameters', {}),
                'usage_count':       cfg.get('usage_count', 0),
                'avg_response_time': cfg.get('avg_response_time'),
            })
            if cfg['status'] == 'online' and cfg['enabled']:
                online_count += 1
        return {'success': True, 'models': models_list, 'total_count': len(models_list),
                'online_count': online_count, 'default_model': config.foundry_default_model,
                'timestamp': datetime.now()}

    def get_providers(self) -> Dict[str, Any]:
        """Return list of available providers.

        Returns:
            dict: success, providers (list of provider dicts), timestamp.
        """
        return {
            'success': True,
            'providers': [
                {'provider_id': pid, **pcfg}
                for pid, pcfg in self.providers_config.items()
            ],
            'timestamp': datetime.now(),
        }

    def get_model_config(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Return configuration for a specific model.

        Args:
            model_id: Model identifier.

        Returns:
            dict | None: Model config dict, or None if not found.
        """
        return self.connected_models.get(model_id)

    def increment_usage(self, model_id: str, response_time: Optional[float] = None) -> None:
        """Increment usage counter and update average response time.

        Args:
            model_id: Model identifier.
            response_time: Response time in seconds to include in rolling average.
        """
        if model_id not in self.connected_models:
            return
        cfg = self.connected_models[model_id]
        cfg['usage_count'] = cfg.get('usage_count', 0) + 1
        if response_time is not None:
            avg = cfg.get('avg_response_time')
            cfg['avg_response_time'] = response_time if avg is None else (avg + response_time) / 2


# Global singleton
model_manager = ModelManager()
