# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Enhanced Foundry Client
# =============================================================================
# Описание:
#   Расширенный клиент для работы с Foundry API
#   Поддержка CPU/GPU, стриминг, управление моделями
#
# File: enhanced_foundry_client.py
# Project: Ai Assistant (Docker)
# Version: 0.2.1
# Author: hypo69
# Copyright: © 2026 hypo69
# Copyright: © 2026 hypo69
# Date: 9 декабря 2025
# =============================================================================

import asyncio
import aiohttp
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, AsyncGenerator

class EnhancedFoundryClient:
    """Расширенный клиент для работы с Foundry API"""
    
    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = base_url or self._find_foundry_url()
        self.timeout = aiohttp.ClientTimeout(total=60)
        self.session = None
        self.available_models = []
        self.model_cache = {}
        
    def _find_foundry_url(self) -> str:
        """Найти URL Foundry сервиса.

        Returns:
            str: Base URL like 'http://127.0.0.1:<port>/v1', or fallback URL.
        """
        import socket
        
        # Популярные порты Foundry
        ports = [50477, 49788, 58717, 51601, 5272]
        
        for port in ports:
            try:
                # Проверяем, отвечает ли порт
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex(('127.0.0.1', port))
                sock.close()
                
                if result == 0:
                    # Проверяем, что это Foundry
                    try:
                        import requests
                        response = requests.get(f"http://127.0.0.1:{port}/v1/models", timeout=2)
                        if response.status_code == 200:
                            return f"http://127.0.0.1:{port}/v1"
                    except:
                        continue
            except:
                continue
                
        # Fallback
        return "http://localhost:50477/v1"
        
    async def _get_session(self):
        """Получить HTTP сессию.

        Returns:
            aiohttp.ClientSession: Active HTTP session.
        """
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(timeout=self.timeout)
        return self.session
    
    async def close(self) -> None:
        """Закрыть HTTP сессию.

        Returns:
            None
        """
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def health_check(self) -> Dict:
        """Проверка здоровья Foundry.

        Returns:
            dict: status (healthy/unhealthy/disconnected), models_count,
                  response_time_ms, url, timestamp.
        """
        try:
            session = await self._get_session()
            url = f"{self.base_url.rstrip('/')}/models"
            
            start_time = time.time()
            async with session.get(url) as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    models = data.get('data', [])
                    self.available_models = models
                    
                    return {
                        "status": "healthy",
                        "models_count": len(models),
                        "response_time_ms": round(response_time * 1000, 2),
                        "url": self.base_url,
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    return {
                        "status": "unhealthy",
                        "error": f"HTTP {response.status}",
                        "response_time_ms": round(response_time * 1000, 2),
                        "url": self.base_url,
                        "timestamp": datetime.now().isoformat()
                    }
        except Exception as e:
            return {
                "status": "disconnected",
                "error": str(e),
                "url": self.base_url,
                "timestamp": datetime.now().isoformat()
            }
    
    async def list_models(self) -> Dict:
        """Получить список доступных моделей с детальной информацией.

        Returns:
            dict: success, models (list with type/size/capabilities/recommended_settings),
                  count, timestamp on success; success=False, error, models=[] on failure.
        """
        try:
            session = await self._get_session()
            url = f"{self.base_url.rstrip('/')}/models"
            
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    models = data.get('data', [])
                    
                    # Обогащаем информацию о моделях
                    enhanced_models = []
                    for model in models:
                        model_info = {
                            "id": model.get("id", "unknown"),
                            "name": model.get("id", "unknown"),
                            "type": self._detect_model_type(model.get("id", "")),
                            "size": self._estimate_model_size(model.get("id", "")),
                            "capabilities": self._get_model_capabilities(model.get("id", "")),
                            "recommended_settings": self._get_recommended_settings(model.get("id", ""))
                        }
                        enhanced_models.append(model_info)
                    
                    return {
                        "success": True,
                        "models": enhanced_models,
                        "count": len(enhanced_models),
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    return {
                        "success": False,
                        "error": f"HTTP {response.status}",
                        "models": []
                    }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "models": []
            }
    
    async def generate_text(self, prompt: str, **kwargs: object) -> Dict:
        """Генерация текста с расширенными параметрами.

        Args:
            prompt: User input text.
            **kwargs: model (str), temperature (float), max_tokens (int),
                      top_p (float), top_k (int), stop (list),
                      presence_penalty (float), frequency_penalty (float).

        Returns:
            dict: success, content, model, usage, performance, timestamp on success;
                  success=False, error on failure.
        """
        try:
            # Проверяем доступность Foundry
            health = await self.health_check()
            if health["status"] != "healthy":
                return {
                    "success": False,
                    "error": "Foundry server not available",
                    "foundry_status": health["status"]
                }
            
            session = await self._get_session()
            url = f"{self.base_url.rstrip('/')}/chat/completions"
            
            # Определяем оптимальную модель если не указана
            model = kwargs.get('model') or self._select_optimal_model()
            
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": kwargs.get('temperature', 0.7),
                "max_tokens": kwargs.get('max_tokens', 2048),
                "top_p": kwargs.get('top_p', 0.9),
                "top_k": kwargs.get('top_k', 40),
                "stream": kwargs.get('stream', False),
                "stop": kwargs.get('stop', []),
                "presence_penalty": kwargs.get('presence_penalty', 0.0),
                "frequency_penalty": kwargs.get('frequency_penalty', 0.0)
            }
            
            start_time = time.time()
            async with session.post(url, json=payload) as response:
                generation_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    content = data['choices'][0]['message']['content']
                    usage = data.get('usage', {})
                    
                    return {
                        "success": True,
                        "content": content,
                        "model": model,
                        "usage": {
                            "prompt_tokens": usage.get('prompt_tokens', 0),
                            "completion_tokens": usage.get('completion_tokens', 0),
                            "total_tokens": usage.get('total_tokens', 0)
                        },
                        "performance": {
                            "generation_time_s": round(generation_time, 2),
                            "tokens_per_second": round(usage.get('completion_tokens', 0) / generation_time, 2) if generation_time > 0 else 0
                        },
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    error_text = await response.text()
                    return {
                        "success": False,
                        "error": f"HTTP {response.status}: {error_text}"
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def generate_stream(self, prompt: str, **kwargs: object) -> AsyncGenerator[Dict, None]:
        """Стриминговая генерация текста.

        Args:
            prompt: User input text.
            **kwargs: model (str), temperature (float), max_tokens (int).

        Yields:
            dict: success, content, model, finished on each token chunk;
                  success=False, error on failure.
        """
        try:
            session = await self._get_session()
            url = f"{self.base_url.rstrip('/')}/chat/completions"
            
            model = kwargs.get('model') or self._select_optimal_model()
            
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": kwargs.get('temperature', 0.7),
                "max_tokens": kwargs.get('max_tokens', 2048),
                "stream": True
            }
            
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    async for line in response.content:
                        line = line.decode('utf-8').strip()
                        if line.startswith('data: '):
                            data_str = line[6:]
                            if data_str == '[DONE]':
                                break
                            try:
                                data = json.loads(data_str)
                                if 'choices' in data and data['choices']:
                                    delta = data['choices'][0].get('delta', {})
                                    if 'content' in delta:
                                        yield {
                                            "success": True,
                                            "content": delta['content'],
                                            "model": model,
                                            "finished": False
                                        }
                            except json.JSONDecodeError:
                                continue
                    
                    yield {
                        "success": True,
                        "content": "",
                        "model": model,
                        "finished": True
                    }
                else:
                    yield {
                        "success": False,
                        "error": f"HTTP {response.status}"
                    }
                    
        except Exception as e:
            yield {
                "success": False,
                "error": str(e)
            }
    
    async def load_model(self, model_id: str) -> Dict:
        """Загрузить модель в память.

        Args:
            model_id: Foundry model identifier.

        Returns:
            dict: success, message on success; success=False, error on failure.
        """
        try:
            session = await self._get_session()
            url = f"{self.base_url.rstrip('/')}/models/{model_id}/load"
            
            async with session.post(url) as response:
                if response.status == 200:
                    return {
                        "success": True,
                        "message": f"Model {model_id} loaded successfully"
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Failed to load model: HTTP {response.status}"
                    }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def unload_model(self, model_id: str) -> Dict:
        """Выгрузить модель из памяти.

        Args:
            model_id: Foundry model identifier.

        Returns:
            dict: success, message on success; success=False, error on failure.
        """
        try:
            session = await self._get_session()
            url = f"{self.base_url.rstrip('/')}/models/{model_id}/unload"
            
            async with session.post(url) as response:
                if response.status == 200:
                    return {
                        "success": True,
                        "message": f"Model {model_id} unloaded successfully"
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Failed to unload model: HTTP {response.status}"
                    }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _detect_model_type(self, model_id: str) -> str:
        """Определить тип модели по ID.

        Args:
            model_id: Model identifier string.

        Returns:
            str: One of 'reasoning', 'coding', 'general'.
        """
        model_id_lower = model_id.lower()
        if 'deepseek' in model_id_lower:
            return 'reasoning'
        elif 'qwen' in model_id_lower:
            return 'general'
        elif 'llama' in model_id_lower:
            return 'general'
        elif 'mistral' in model_id_lower:
            return 'general'
        elif 'code' in model_id_lower:
            return 'coding'
        else:
            return 'general'
    
    def _estimate_model_size(self, model_id: str) -> str:
        """Оценить размер модели.

        Args:
            model_id: Model identifier string.

        Returns:
            str: Size label like '7B', '14B', '70B', or 'unknown'.
        """
        if '7b' in model_id.lower():
            return '7B'
        elif '14b' in model_id.lower():
            return '14B'
        elif '32b' in model_id.lower():
            return '32B'
        elif '70b' in model_id.lower():
            return '70B'
        else:
            return 'unknown'
    
    def _get_model_capabilities(self, model_id: str) -> List[str]:
        """Получить возможности модели.

        Args:
            model_id: Model identifier string.

        Returns:
            List[str]: Capability tags, e.g. ['text_generation', 'reasoning', 'multilingual'].
        """
        capabilities = ['text_generation']
        model_id_lower = model_id.lower()
        
        if 'code' in model_id_lower:
            capabilities.append('code_generation')
        if 'deepseek' in model_id_lower:
            capabilities.extend(['reasoning', 'math', 'analysis'])
        if 'qwen' in model_id_lower:
            capabilities.extend(['multilingual', 'reasoning'])
        
        return capabilities
    
    def _get_recommended_settings(self, model_id: str) -> Dict:
        """Получить рекомендуемые настройки для модели.

        Args:
            model_id: Model identifier string.

        Returns:
            dict: temperature, top_p, max_tokens tuned for the model type.
        """
        model_type = self._detect_model_type(model_id)
        
        if model_type == 'reasoning':
            return {
                "temperature": 0.1,
                "top_p": 0.8,
                "max_tokens": 4096
            }
        elif model_type == 'coding':
            return {
                "temperature": 0.2,
                "top_p": 0.9,
                "max_tokens": 2048
            }
        else:
            return {
                "temperature": 0.7,
                "top_p": 0.9,
                "max_tokens": 2048
            }
    
    def _select_optimal_model(self) -> str:
        """Выбрать оптимальную модель.

        Priority: DeepSeek 14B → any Qwen → first available → fallback 'deepseek-r1:14b'.

        Returns:
            str: Model ID of the best available model.
        """
        if self.available_models:
            # Приоритет: DeepSeek > Qwen > Llama > другие
            for model in self.available_models:
                model_id = model.get('id', '').lower()
                if 'deepseek' in model_id and '14b' in model_id:
                    return model.get('id')
            
            for model in self.available_models:
                model_id = model.get('id', '').lower()
                if 'qwen' in model_id:
                    return model.get('id')
            
            # Возвращаем первую доступную модель
            return self.available_models[0].get('id', 'deepseek-r1:14b')
        
        return 'deepseek-r1:14b'

# Глобальный экземпляр клиента
enhanced_foundry_client = EnhancedFoundryClient()