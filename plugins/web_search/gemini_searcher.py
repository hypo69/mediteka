# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Gemini Web Search Grounding Provider
# =============================================================================
# Описание:
#   Модуль веб-поиска через официальный SDK google-genai с поддержкой
#   встроенного поиска Google (Grounding with Google Search) и пула
#   ротации API-ключей (Round-Robin) при исчерпании лимитов (429 / ResourceExhausted).
#
# File: gemini_searcher.py
# Project: mediteka
# Package: plugins.web_search
# Class: GeminiWebSearcher, GeminiKeyPool
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

import os
import itertools
from typing import List, Dict, Any
from google import genai
from google.genai import types
from google.genai.errors import APIError

from src.logger import logger
from src.secrets.api_key_state import load_api_keys


class GeminiKeyPool:
    """Пул API-ключей Gemini с автоматической ротацией при исчерпании квот (429) или ошибках проекта."""

    def __init__(self, api_keys: List[str] = []) -> None:
        """Инициализация пула ключей.

        Args:
            api_keys: Список валидных API-ключей Gemini.
        """
        valid_keys = [k.strip() for k in api_keys if k and k.strip()]
        if not valid_keys:
            # Попытка загрузить из переменных окружения
            env_pool = os.getenv("GEMINI_KEY_POOL", "").strip()
            if env_pool:
                valid_keys = [k.strip() for k in env_pool.split(",") if k.strip()]

        if not valid_keys:
            # Попытка загрузить через secrets manager
            _names = [n.strip() for n in os.getenv("GEMINI_API_KEY_NAMES", "").split(",") if n.strip()]
            loaded, _, _ = load_api_keys(_names if len(_names) > 0 else "")
            valid_keys = [k for k in loaded if k]

        if not valid_keys:
            single_key = os.getenv("GEMINI_API_KEY", "").strip()
            if single_key:
                valid_keys = [single_key]

        if not valid_keys:
            raise ValueError("Пул API-ключей Gemini пуст. Укажите ключи в .env (GEMINI_KEY_POOL или GEMINI_API_KEY).")

        # Приоритет ключам с прямым доступом к моделям Google GenAI
        aiza_keys = [k for k in valid_keys if k.startswith("AIzaSy")]
        other_keys = [k for k in valid_keys if not k.startswith("AIzaSy")]
        self.api_keys: List[str] = aiza_keys + other_keys
        self._key_cycle = itertools.cycle(self.api_keys)
        self._current_key: str = next(self._key_cycle)
        self._client: genai.Client = genai.Client(api_key=self._current_key)

    def _rotate_key(self) -> str:
        """Переключает активный клиент на следующий ключ из пула."""
        self._current_key = next(self._key_cycle)
        masked = f"...{self._current_key[-6:]}" if len(self._current_key) >= 6 else "***"
        logger.warning(f"[GeminiKeyPool] ⚠️ Ротация на следующий ключ: {masked}")
        self._client = genai.Client(api_key=self._current_key)
        return self._current_key

    def generate_with_search(self, prompt: str, model: str = "gemini-2.5-flash") -> Dict[str, Any]:
        """Выполняет генерацию контента с поиском Google Grounding и ротацией при ошибках.

        Args:
            prompt: Текстовый поисковый запрос или инструкция.
            model: Имя модели Gemini (по умолчанию gemini-2.5-flash).

        Returns:
            Dict[str, Any]: Словарь с полями 'text', 'sources', 'search_queries'.
        """
        attempts = 0
        max_attempts = len(self.api_keys)
        last_exception = ""
        candidate_models = [model]
        if model != "gemini-2.5-flash-lite":
            candidate_models.append("gemini-2.5-flash-lite")

        while attempts < max_attempts:
            for target_model in candidate_models:
                try:
                    response = self._client.models.generate_content(
                        model=target_model,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            tools=[{"google_search": {}}],
                            temperature=0.2,
                        ),
                    )
                    return self._parse_response(response)

                except APIError as e:
                    err_msg = str(e)
                    last_exception = str(e)
                    if e.code == 503 and target_model != candidate_models[-1]:
                        logger.warning(f"[GeminiKeyPool] Модель {target_model} вернула 503, пробуем {candidate_models[-1]}...")
                        continue
                    break

                except Exception as e:
                    last_exception = str(e)
                    break

            attempts += 1
            if attempts < max_attempts:
                logger.warning(f"[GeminiKeyPool] Ошибка вызова Gemini ({last_exception[:120]}). Ротация ключа...")
                self._rotate_key()
            else:
                logger.error(f"[GeminiKeyPool] Все ключи исчерпаны. Последняя ошибка: {last_exception}")

        raise RuntimeError(f"Все {max_attempts} API-ключей Gemini из пула вернули ошибку или исчерпали лимиты. Детали: {last_exception}")

    def _parse_response(self, response: Any) -> Dict[str, Any]:
        """Парсинг ответа модели и извлечение данных Google Search Grounding."""
        result_text = getattr(response, "text", "") or ""
        sources: List[Dict[str, str]] = []
        search_queries: List[str] = []

        candidates = getattr(response, "candidates", []) or []
        if candidates:
            first_candidate = candidates[0]
            grounding = getattr(first_candidate, "grounding_metadata", "")
            if grounding:
                web_search_queries = getattr(grounding, "web_search_queries", []) or []
                search_queries = [q for q in web_search_queries if q]

                chunks = getattr(grounding, "grounding_chunks", []) or []
                for chunk in chunks:
                    web = getattr(chunk, "web", "")
                    if web:
                        title = getattr(web, "title", "") or "Источник"
                        uri = getattr(web, "uri", "") or ""
                        domain = getattr(web, "domain", "") or ""
                        if uri:
                            sources.append({
                                "title": title,
                                "url": uri,
                                "domain": domain,
                            })

        return {
            "text": result_text,
            "sources": sources,
            "search_queries": search_queries,
        }


class GeminiWebSearcher:
    """Обертка поисковика Gemini Search Grounding для интеграции в плагин и MCP."""

    def __init__(self, api_keys: List[str] = []) -> None:
        """Инициализация поисковика."""
        self._pool_instance = ""
        self._keys = api_keys

    def _get_pool(self) -> GeminiKeyPool:
        """Ленивая инициализация пула ключей."""
        if not self._pool_instance:
            self._pool_instance = GeminiKeyPool(self._keys)
        return self._pool_instance

    def _get_config_model(self) -> str:
        """Получает настроенную модель из config.json."""
        try:
            import json
            from header import __root__
            cfg_path = __root__ / 'config.json'
            if cfg_path.exists():
                with open(cfg_path, 'r', encoding='utf-8') as f:
                    cfg = json.load(f)
                    return cfg.get('web_search', {}).get('gemini_model', 'gemini-2.5-flash')
        except Exception:
            pass
        return 'gemini-2.5-flash'

    async def search_and_extract(self, query: str, model: str = "") -> str:
        """Выполняет веб-поиск через Gemini Grounding и возвращает структурированный markdown.

        Args:
            query: Поисковый запрос.
            model: Имя модели Gemini (если пусто, читается из config.json).

        Returns:
            str: Сформированный контекст поиска с текстом и источниками.
        """
        pool = self._get_pool()
        if not model or model == "gemini-flash-lite-latest":
            model = self._get_config_model()

        prompt = (
            f"Найди актуальную, достоверную информацию в интернете по следующему запросу "
            f"и составь подробную выжимку фактов с указанием деталей:\n\n"
            f"Запрос: {query}"
        )
        res = pool.generate_with_search(prompt=prompt, model=model)
        
        output_parts: List[str] = []
        if res.get("text"):
            output_parts.append(res["text"])

        sources = res.get("sources", [])
        if sources:
            output_parts.append("\n### Использованные источники:")
            seen_urls = set()
            for s in sources:
                url = s.get("url", "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    title = s.get("title") or url
                    output_parts.append(f"- [{title}]({url})")

        return "\n".join(output_parts)
