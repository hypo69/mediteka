# -*- coding: utf-8 -*-
# =============================================================================
# Process Name: Unified Chat Interface
# =============================================================================
# Description:
#   A wrapper model class that aggregates GoogleGenerativeAI and FoundryChatBase
#   under a unified interface, dynamically routing requests depending on the model selected.
#
# File: src/ai/unified_chat.py
# Project: mediateka
# =============================================================================

import os
import inspect
import asyncio
from typing import Optional, List, Dict, Any
from src.ai.gemini import GoogleGenerativeAI
from src.ai.foundry_chat import FoundryChatBase
from src.logger import logger

class UnifiedChatModel:
    """
    Класс-обертка для прозрачного роутинга между моделями Gemini и Foundry.
    """
    def __init__(
        self,
        api_key_names: list[str],
        system_instruction: str,
        foundry_model_id: str,
        use_foundry: bool = False,
    ):
        self.gemini_model = GoogleGenerativeAI(
            api_key_names=api_key_names,
            system_instruction=system_instruction,
            sleep_on_exhausted=False,
        )
        self.foundry_model = None
        self.use_foundry = use_foundry
        self.foundry_model_id = foundry_model_id
        
        if use_foundry:
            self.foundry_model = FoundryChatBase(
                model_id=foundry_model_id,
                system_prompt=system_instruction,
            )
            
        from src.ai.gemini.generative_ai import _DEFAULT_MODEL
        self.default_model = foundry_model_id if use_foundry else _DEFAULT_MODEL
        self._model_name = self.default_model
        
        if use_foundry:
            self.foundry_model = FoundryChatBase(
                model_id=foundry_model_id,
                system_prompt=system_instruction,
            )
            
        from src.ai.gemini.generative_ai import _DEFAULT_MODEL
        self.default_model = foundry_model_id if use_foundry else _DEFAULT_MODEL
        self._model_name = self.default_model
        
    @property
    def model_name(self) -> str:
        return self._model_name
        
    @model_name.setter
    def model_name(self, val: str):
        self._model_name = val
        if self.foundry_model:
            self.foundry_model.model_id = val
        if self.gemini_model:
            self.gemini_model.model_name = val
            
    @property
    def model_id(self) -> str:
        return self._model_name
        
    @model_id.setter
    def model_id(self, val: str):
        self._model_name = val
        if self.foundry_model:
            self.foundry_model.model_id = val
        if self.gemini_model:
            self.gemini_model.model_name = val

    @property
    def api_key(self) -> str:
        return getattr(self.gemini_model, 'api_key', '') or ''

    @property
    def system_instruction(self) -> Optional[str]:
        return getattr(self.gemini_model, 'system_instruction', '')

    def _get_active_model(self, model_name: Optional[str] = None):
        active_name = model_name or self._model_name
        if not self.foundry_model or active_name.startswith("gemini-"):
            return self.gemini_model, active_name
        return self.foundry_model, active_name

    async def chat(
        self,
        q: str,
        history: Optional[List[Dict]] = None,
        system_instruction: Optional[str] = None,
        attempts: int = 15,
        model_name: Optional[str] = None,
        **kwargs
    ) -> Optional[str]:
        model_instance, active_name = self._get_active_model(model_name)
        logger.info(f"[UnifiedChatModel] chat: prompt={repr(q[:100])}... using model={active_name}")
        
        sig = inspect.signature(model_instance.chat)
        call_kwargs = {
            "q": q,
            "history": history,
            "system_instruction": system_instruction,
            "attempts": attempts,
        }
        if "model_name" in sig.parameters:
            call_kwargs["model_name"] = active_name
        elif hasattr(model_instance, "model_id"):
            model_instance.model_id = active_name
            
        for k, v in kwargs.items():
            if k in sig.parameters:
                call_kwargs[k] = v
                
        try:
            res = await model_instance.chat(**call_kwargs)
            logger.info(f"[UnifiedChatModel] chat success: response={repr(res[:100]) if res else 'None'}...")
            return res
        except Exception as ex:
            logger.error(f"[UnifiedChatModel] chat error with model={active_name}", ex)
            raise

    async def ask(
        self,
        q: str,
        attempts: int = 15,
        generation_config: dict = {},
        model_name: Optional[str] = None,
        **kwargs
    ) -> Optional[str]:
        model_instance, active_name = self._get_active_model(model_name)
        logger.info(f"[UnifiedChatModel] ask: prompt={repr(q[:100])}... using model={active_name}")
        
        sig = inspect.signature(model_instance.ask)
        call_kwargs = {
            "q": q,
            "attempts": attempts,
        }
        if "model_name" in sig.parameters:
            call_kwargs["model_name"] = active_name
        elif hasattr(model_instance, "model_id"):
            model_instance.model_id = active_name
            
        if "generation_config" in sig.parameters:
            call_kwargs["generation_config"] = generation_config
            
        for k, v in kwargs.items():
            if k in sig.parameters:
                call_kwargs[k] = v
                
        try:
            res = await model_instance.ask(**call_kwargs)
            logger.info(f"[UnifiedChatModel] ask success: response={repr(res[:100]) if res else 'None'}...")
            return res
        except Exception as ex:
            logger.error(f"[UnifiedChatModel] ask error with model={active_name}", ex)
            raise

    async def chat_stream(
        self,
        q: str,
        history: Optional[List[Dict]] = None,
        system_instruction: Optional[str] = None,
        attempts: int = 15,
        model_name: Optional[str] = None,
        generation_config: dict = {},
        **kwargs
    ):
        model_instance, active_name = self._get_active_model(model_name)
        logger.info(f"[UnifiedChatModel] chat_stream: prompt={repr(q[:100])}... using model={active_name}")
        
        sig = inspect.signature(model_instance.chat_stream)
        call_kwargs = {
            "q": q,
            "history": history,
            "system_instruction": system_instruction,
            "attempts": attempts,
        }
        if "model_name" in sig.parameters:
            call_kwargs["model_name"] = active_name
        elif hasattr(model_instance, "model_id"):
            model_instance.model_id = active_name
            
        if "generation_config" in sig.parameters:
            call_kwargs["generation_config"] = generation_config
            
        for k, v in kwargs.items():
            if k in sig.parameters:
                call_kwargs[k] = v

        try:
            async for chunk in model_instance.chat_stream(**call_kwargs):
                yield chunk
        except Exception as ex:
            logger.error(f"[UnifiedChatModel] chat_stream error with model={active_name}", ex)
            raise

