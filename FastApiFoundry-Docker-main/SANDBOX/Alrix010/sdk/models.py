# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: FastAPI Foundry SDK Models
# =============================================================================
# Описание:
#   Модели данных для SDK
#
# File: models.py
# Project: Ai Assistant (Docker)
# Version: 0.4.0
# Author: hypo69
# Copyright: © 2026 hypo69
# Copyright: © 2026 hypo69
# Date: 9 декабря 2025
# =============================================================================

from typing import Optional, List, Dict, Any
from dataclasses import dataclass

@dataclass
class GenerationRequest:
    """Запрос на генерацию текста"""
    prompt: str
    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    use_rag: bool = True
    system_prompt: Optional[str] = None
    
    def dict(self, exclude_none: bool = False) -> Dict[str, Any]:
        """Преобразовать в словарь"""
        result = {
            "prompt": self.prompt,
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "use_rag": self.use_rag,
            "system_prompt": self.system_prompt
        }
        
        if exclude_none:
            result = {k: v for k, v in result.items() if v is not None}
        
        return result

@dataclass
class GenerationResponse:
    """Ответ генерации текста"""
    success: bool
    content: Optional[str] = None
    error: Optional[str] = None
    model_used: Optional[str] = None
    tokens_used: Optional[int] = None
    rag_sources: Optional[List[str]] = None
    generation_time: Optional[float] = None
    
    def __init__(self, **kwargs):
        self.success = kwargs.get("success", False)
        self.content = kwargs.get("content") or kwargs.get("response")
        self.error = kwargs.get("error")
        self.model_used = kwargs.get("model_used")
        self.tokens_used = kwargs.get("tokens_used")
        self.rag_sources = kwargs.get("rag_sources", [])
        self.generation_time = kwargs.get("generation_time")

@dataclass
class ModelInfo:
    """Информация о модели"""
    id: str
    name: Optional[str] = None
    provider: Optional[str] = None
    status: Optional[str] = None
    max_tokens: Optional[int] = None
    
    def __init__(self, **kwargs):
        self.id = kwargs.get("id") or kwargs.get("model_id")
        self.name = kwargs.get("name") or kwargs.get("model_name")
        self.provider = kwargs.get("provider", "foundry")
        self.status = kwargs.get("status", "unknown")
        self.max_tokens = kwargs.get("max_tokens")

@dataclass
class HealthStatus:
    """Статус здоровья системы"""
    status: str
    foundry_status: Optional[str] = None
    foundry_url: Optional[str] = None
    rag_loaded: bool = False
    rag_chunks: int = 0
    models_count: int = 0
    
    def __init__(self, **kwargs):
        self.status = kwargs.get("status", "unknown")
        self.foundry_status = kwargs.get("foundry_status")
        
        # Извлекаем URL из foundry_details если есть
        foundry_details = kwargs.get("foundry_details", {})
        if foundry_details and isinstance(foundry_details, dict):
            self.foundry_url = foundry_details.get("url")
        
        self.rag_loaded = kwargs.get("rag_loaded", False)
        self.rag_chunks = kwargs.get("rag_chunks", 0)
        self.models_count = kwargs.get("models_count", 0)
    
    @property
    def is_healthy(self) -> bool:
        """Проверить, здорова ли система"""
        return self.status == "healthy"
    
    @property
    def is_foundry_connected(self) -> bool:
        """Проверить, подключен ли Foundry"""
        return self.foundry_status == "healthy"