# -*- coding: utf-8 -*-
from plugins.plugin import BasePlugin
from .playwright_searcher import PlaywrightWebSearcher
from src.logger import logger

class WebSearchPlugin(BasePlugin):
    """Плагин для прямого веб-поиска по запросу пользователя."""
    name = "web_search"

    def __init__(self, ai_model):
        super().__init__(ai_model)
        self.searcher = PlaywrightWebSearcher()

    def _is_web_query(self, message: str) -> bool:
        low = message.lower()
        web_keywords = [
            "поищи в интернете", "найди в интернете", "посмотри на форумах", 
            "поищи на форумах", "погугли", "найди информацию о", "интернет поиск"
        ]
        return any(kw in low for kw in web_keywords)

    def can_handle(self, message: str) -> bool:
        return self._is_web_query(message)

    async def _handle(self, message: str, **kwargs) -> str:
        if not self._is_web_query(message):
            return
        
        # Очистка запроса от вводных фраз
        query = message
        for kw in ["поищи в интернете", "найди в интернете", "посмотри на форумах", "поищи на форумах", "погугли"]:
            query = query.replace(kw, "")
        query = query.strip()
        
        yield {"status": "🌐 Поиск в интернете через Playwright..."}
        web_context = await self.searcher.search_and_extract(query)
        
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
