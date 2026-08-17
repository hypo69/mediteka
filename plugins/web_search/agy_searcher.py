# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Antigravity (AGY) Web Search Provider
# =============================================================================
# Описание:
#   Модуль веб-поиска через Google Antigravity SDK и инструменты
#   BuiltinTools.SEARCH_WEB / READ_URL_CONTENT. Поддерживает как выполнение
#   через SDK Agent loop, так и fallback через Antigravity CLI.
#
# File: agy_searcher.py
# Project: mediteka
# Package: plugins.web_search
# Class: AgyWebSearcher
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import os
import json
import asyncio
import subprocess
from typing import List, Dict, Any

try:
    from google.antigravity import Agent, LocalAgentConfig, CapabilitiesConfig, BuiltinTools
except ImportError:
    Agent = None
    LocalAgentConfig = None
    CapabilitiesConfig = None
    BuiltinTools = None

from src.logger import logger
from src.secrets.api_key_state import load_api_keys


class AgyWebSearcher:
    """Провайдер веб-поиска через Google Antigravity SDK и встроенные инструменты."""

    @classmethod
    def normalize_model_id(cls, model_id: str) -> str:
        """Нормализация имени модели для Antigravity SDK."""
        actual = (model_id or "").strip()
        while actual.startswith("agy-"):
            actual = actual[4:]
        if actual in ("flash", "flash-latest", "agy-flash", ""):
            return "gemini-flash-lite-latest"
        elif actual in ("pro", "pro-latest", "agy-pro"):
            return "gemini-pro-latest"
        elif not (actual.startswith("gemini-") or actual.startswith("gemma-") or actual.startswith("deep-research-") or actual.startswith("lyria-")):
            actual = f"gemini-{actual}"
        return actual

    def __init__(self, model_id: str = "agy-flash") -> None:
        """Инициализация поисковика Antigravity.

        Args:
            model_id: Идентификатор модели AGY (по умолчанию agy-flash).
        """
        self._model_id: str = self.normalize_model_id(model_id)

        valid_keys: List[str] = []
        agy_key = os.getenv("AGY_API_KEY", "").strip()
        if agy_key:
            valid_keys.append(agy_key)

        _names = [n.strip() for n in os.getenv("GEMINI_API_KEY_NAMES", "").split(",") if n.strip()]
        loaded, _, _ = load_api_keys(_names if len(_names) > 0 else "")
        for k in loaded:
            if k and k not in valid_keys:
                valid_keys.append(k)

        self.api_keys: List[str] = valid_keys
        self.api_key: str = valid_keys[0] if len(valid_keys) > 0 else ""

    @property
    def model_id(self) -> str:
        """Возвращает нормализованный идентификатор модели."""
        return self._model_id

    @model_id.setter
    def model_id(self, val: str) -> None:
        """Устанавливает и нормализует идентификатор модели."""
        self._model_id = self.normalize_model_id(val)

    def _clean_output(self, text: str) -> str:
        """Очищает ответ от технических сообщений об ошибках внутренних шагов SDK."""
        cleaned = text.strip()
        if "error executing cascade step:" in cleaned or "RESOURCE_EXHAUSTED" in cleaned or "GenerateContent failed:" in cleaned:
            # 1. Если присутствуют закрывающие скобки блока Details: [...]]]]
            if "]]]]" in cleaned:
                idx = cleaned.find("]]]]")
                cleaned = cleaned[idx + 4:].strip()
            elif "]]" in cleaned:
                idx = cleaned.rfind("]]")
                cleaned = cleaned[idx + 2:].strip()
            else:
                lines = cleaned.split("\n")
                filtered = [l for l in lines if not l.startswith("error executing cascade step:") and not l.startswith("GenerateContent failed:") and "RESOURCE_EXHAUSTED" not in l]
                cleaned = "\n".join(filtered).strip()
        return cleaned

    async def search_and_extract(self, query: str) -> str:
        """Выполняет поиск и извлечение информации по запросу.

        Args:
            query: Текстовый поисковый запрос.

        Returns:
            str: Извлеченный и структурированный контекст поиска.
        """
        if not query or not query.strip():
            return "Пустой поисковый запрос."

        # 1. Попытка через Python SDK Agent
        try:
            sdk_result = await self._search_via_sdk(query)
            if sdk_result and len(sdk_result.strip()) > 0:
                return self._clean_output(sdk_result)
        except Exception as e:
            logger.warning(f"[AgyWebSearcher] Ошибка поиска через AGY SDK: {e}. Пробуем CLI fallback...")

        # 2. Попытка через CLI subprocess
        try:
            cli_result = await self._search_via_cli(query)
            if cli_result and len(cli_result.strip()) > 0:
                return self._clean_output(cli_result)
        except Exception as e:
            logger.error(f"[AgyWebSearcher] Ошибка поиска через AGY CLI: {e}")

        return f"Не удалось получить результаты поиска Antigravity по запросу: {query}"

    async def _search_via_sdk(self, query: str) -> str:
        """Поиск через Antigravity Agent SDK с активированным SEARCH_WEB и ротацией ключей."""
        if not Agent or not LocalAgentConfig:
            raise ImportError("Google Antigravity SDK is not installed or available in this environment")

        system_instruction = (
            "Ты — модуль автономного веб-поиска. Твоя задача — использовать встроенный инструмент "
            "search_web (и read_url_content при необходимости), чтобы найти актуальные факты по "
            "запросу пользователя. Сформируй содержательный ответ на русском языке и обязательно "
            "перечисли ссылки на найденные источники."
        )

        capabilities = CapabilitiesConfig(
            enable_subagents=False,
            enabled_tools=[BuiltinTools.SEARCH_WEB, BuiltinTools.READ_URL_CONTENT]
        )

        keys_to_try = self.api_keys if self.api_keys else ([self.api_key] if self.api_key else [""])
        last_error = ""

        for idx, key in enumerate(keys_to_try):
            config = LocalAgentConfig(
                model=self.model_id,
                system_instructions=system_instruction,
                api_key=key,
                tools=[],
                policies=[],
                capabilities=capabilities,
            )

            try:
                output_tokens: List[str] = []
                async with Agent(config) as agent:
                    response_stream = await agent.chat(f"Найди в интернете и обобщи информацию: {query}")
                    async for token in response_stream:
                        output_tokens.append(token)

                full_text = "".join(output_tokens)
                cleaned = self._clean_output(full_text)
                if cleaned and len(cleaned) > 20:
                    return cleaned

                # Если текст слишком короткий или содержал только ошибку квоты
                if "Error 429" in full_text or "RESOURCE_EXHAUSTED" in full_text:
                    logger.warning(f"[AgyWebSearcher] Ключ #{idx + 1} исчерпал квоту (429). Ротация...")
                    continue

                if cleaned:
                    return cleaned
            except Exception as e:
                err_str = str(e)
                last_error = err_str
                logger.warning(f"[AgyWebSearcher] Ошибка на ключе #{idx + 1}: {err_str[:120]}")
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "quota" in err_str.lower():
                    continue
                else:
                    break

        if last_error:
            raise RuntimeError(f"Все ключи AGY исчерпали квоты: {last_error}")
        return ""

    async def _search_via_cli(self, query: str) -> str:
        """Поиск через команду CLI: agy run --tool search_web --input '...' --json."""
        cmd = [
            "agy",
            "run",
            "--tool", "search_web",
            "--input", query,
            "--json"
        ]

        def _run_sub():
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=45,
                shell=True
            )
            return proc.stdout.strip() if proc.returncode == 0 else ""

        loop = asyncio.get_running_loop()
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=1) as executor:
            raw_output = await loop.run_in_executor(executor, _run_sub)
        if not raw_output:
            return ""

        try:
            parsed = json.loads(raw_output)
            if isinstance(parsed, dict) and "output" in parsed:
                return str(parsed["output"])
            return raw_output
        except Exception:
            return raw_output
