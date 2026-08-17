# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Web Search Plugin с поддержкой Playwright, LangChain, Gemini и AGY
# =============================================================================

import json
from pathlib import Path
from plugins.plugin import BasePlugin
from .triggers import is_web_search_query, extract_clean_query
from src.logger import logger

class WebSearchPlugin(BasePlugin):
    """Плагин для прямого веб-поиска по запросу пользователя с выбором движка."""
    name = "web_search"

    def __init__(self, ai_model):
        super().__init__(ai_model)
        self._playwright_searcher = ""
        self._gemini_searcher = ""
        self._agy_searcher = ""

    @property
    def playwright_searcher(self):
        if not self._playwright_searcher:
            try:
                from .playwright_searcher import PlaywrightWebSearcher
                self._playwright_searcher = PlaywrightWebSearcher()
            except Exception as e:
                logger.error(f"[WebSearchPlugin] Ошибка импорта Playwright: {e}")
        return self._playwright_searcher

    @property
    def gemini_searcher(self):
        if not self._gemini_searcher:
            try:
                from .gemini_searcher import GeminiWebSearcher
                self._gemini_searcher = GeminiWebSearcher()
            except Exception as e:
                logger.error(f"[WebSearchPlugin] Ошибка импорта GeminiWebSearcher: {e}")
        return self._gemini_searcher

    @property
    def agy_searcher(self):
        if not self._agy_searcher:
            try:
                from .agy_searcher import AgyWebSearcher
                self._agy_searcher = AgyWebSearcher()
            except Exception as e:
                logger.error(f"[WebSearchPlugin] Ошибка импорта AgyWebSearcher: {e}")
        return self._agy_searcher

    def _get_config(self) -> dict:
        """Получает параметры веб-поиска из config.json."""
        try:
            from header import __root__
            cfg_path = __root__ / 'config.json'
            if cfg_path.exists():
                with open(cfg_path, 'r', encoding='utf-8') as f:
                    cfg = json.load(f)
                    return cfg.get('web_search', {})
        except Exception as e:
            logger.warning(f"Не удалось прочитать web_search из config.json: {e}")
        return {}

    def _get_engine(self) -> str:
        """Получает выбранный движок поиска из config.json."""
        cfg = self._get_config()
        return cfg.get('engine', 'playwright')

    def can_handle(self, message: str) -> bool:
        return is_web_search_query(message)

    async def _handle(self, message: str, **kwargs):
        if not is_web_search_query(message):
            return

        query = extract_clean_query(message)
        if not query:
            query = message

        ws_cfg = self._get_config()
        engine = ws_cfg.get('engine', 'playwright')
        gemini_model = ws_cfg.get('gemini_model', 'gemini-2.5-flash')
        agy_model = ws_cfg.get('agy_model', 'agy-flash')
        web_context = ""

        if engine == "langchain":
            yield {"status": "🦜 Поиск в интернете через LangChain MCP..."}
            try:
                from src.ai.langchain_agent import MediaSearchAgent
                from header import __root__
                agent = MediaSearchAgent(config_path=__root__ / "config.json")
                search_res = await agent.search(query)
                web_context = json.dumps(search_res, ensure_ascii=False, indent=2)
            except Exception as ex:
                logger.error(f"[WebSearchPlugin] Ошибка поиска через LangChain: {ex}")
                web_context = f"Ошибка поиска через LangChain: {ex}"
        elif engine == "gemini":
            yield {"status": "♊ Поиск в интернете через Google Gemini (Grounding)..."}
            try:
                web_context = await self.gemini_searcher.search_and_extract(query, model=gemini_model)
            except Exception as ex:
                logger.error(f"[WebSearchPlugin] Ошибка поиска через Gemini: {ex}")
                web_context = f"Ошибка поиска через Gemini: {ex}"
        elif engine == "agy":
            yield {"status": "🚀 Поиск в интернете через Antigravity (AGY)..."}
            try:
                web_context = await self.agy_searcher.search_and_extract(query, model=agy_model)
            except Exception as ex:
                logger.error(f"[WebSearchPlugin] Ошибка поиска через Antigravity: {ex}")
                web_context = f"Ошибка поиска через Antigravity: {ex}"
        else:
            yield {"status": "🎭 Поиск в интернете через Playwright MCP..."}
            try:
                web_context = await self.playwright_searcher.search_and_extract(query)
            except Exception as ex:
                logger.error(f"[WebSearchPlugin] Ошибка поиска через Playwright: {ex}")
                web_context = f"Ошибка поиска через Playwright: {ex}"

        yield {"status": "🤖 Анализ результатов и генерация ответа..."}
        system_prompt = (
            f"Ты — полезный AI Assistant. Тебе предоставлены результаты поиска в интернете по запросу пользователя.\n"
            f"Используй этот контекст, чтобы дать максимально точный, детальный и структурированный ответ на русском языке.\n"
            f"Если речь о фильме или сериале (например, сюжет по сериям, мнения), ответь развёрнуто, без использования местоимения «это» в начале абзацев.\n\n"
            f"{web_context}"
        )

        response = await self.ai.chat(
            message,
            system_instruction=system_prompt,
            model_name=kwargs.get('model_name')
        )

        yield {"text": response}

plugin = WebSearchPlugin

