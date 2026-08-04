# -*- coding: utf-8 -*-
"""Простой клиент для FastAPI Foundry API"""

import requests
import json

class FoundryClient:
    """Простой клиент для работы с FastAPI Foundry API"""
    
    def __init__(self, base_url="http://localhost:9696", timeout=30):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
        self.session.timeout = timeout
    
    def _request(self, method, endpoint, **kwargs):
        """Выполнить HTTP запрос"""
        url = f"{self.base_url}{endpoint}"
        kwargs.setdefault('timeout', self.timeout)
        
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def health(self):
        """Проверить здоровье системы"""
        return self._request("GET", "/api/v1/health")
    
    def generate(self, prompt, model=None, max_tokens=None, use_rag=True):
        """Генерировать текст"""
        data = {"prompt": prompt, "use_rag": use_rag}
        if model:
            data["model"] = model
        if max_tokens:
            data["max_tokens"] = max_tokens
        
        return self._request("POST", "/api/v1/generate", json=data)
    
    def chat(self, message, conversation_id=None, use_rag=True):
        """Отправить сообщение в чат"""
        data = {"message": message, "use_rag": use_rag}
        if conversation_id:
            data["conversation_id"] = conversation_id
        
        return self._request("POST", "/api/v1/chat", json=data)
    
    def list_models(self):
        """Получить список моделей"""
        return self._request("GET", "/api/v1/models")
    
    def rag_search(self, query, top_k=5):
        """Поиск в RAG индексе"""
        return self._request("POST", "/api/v1/rag/search", json={"query": query, "top_k": top_k})
    
    def close(self):
        """Закрыть сессию"""
        self.session.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()