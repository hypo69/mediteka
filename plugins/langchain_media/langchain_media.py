# -*- coding: utf-8 -*-
# =============================================================================
# Название процесса: Плагин LangChain Media
# =============================================================================
# Описание:
#   Плагин для обработки запросов, связанных с поиском медиа-контента,
#   с использованием LangChain MediaSearchAgent.
#
# File: langchain_media.py
# Project: mediteka
# Package: plugins.langchain_media
# Author: hypo69
# Copyright: © 2026 hypo69
# =============================================================================

from typing import AsyncIterator
from pathlib import Path
from plugins.plugin import BasePlugin
from src.logger import logger


class LangChainMediaPlugin(BasePlugin):
    """Плагин для поиска фильмов и сериалов через LangChain агента."""

    name = 'langchain_media'
    title = 'Автономный LangChain Агент'
    description = 'ReAct мультиагентный поиск фильмов, сериалов, торрент-раздач и стриминга'
    icon = '🦜'
    version = '1.2.0'
    category = 'ai'

    SEARCH_KEYWORDS = (
        'найди фильм', 'найди сериал', 'где посмотреть', 'скачать фильм',
        'скачать сериал', 'поиск фильм', 'поиск сериал', 'langchain поиск',
        'agent поиск', 'агент поиск', 'мультфильм', 'аниме', 'найди торрент',
    )

    def get_manifest(self) -> dict:
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
                {
                    'id': 'max_steps',
                    'label': 'Макс. число шагов агента',
                    'type': 'number',
                    'default': 15,
                    'description': 'Ограничение итераций размышления ReAct-агента'
                },
                {
                    'id': 'search_timeout_seconds',
                    'label': 'Таймаут поиска (сек)',
                    'type': 'number',
                    'default': 60,
                    'description': 'Максимальное время выполнения одного поиска'
                }
            ],
            'actions': []
        }

    def __init__(self, ai_model):
        """Инициализация плагина."""
        super().__init__(ai_model)
        self._agent = False

    @property
    def agent(self):
        if not self._agent:
            try:
                from src.ai.langchain_agent import MediaSearchAgent
                self._agent = MediaSearchAgent(
                    config_path=Path('config.json'),
                    ai_model=self.ai,
                )
            except Exception as e:
                logger.warning(f"[LangChainMediaPlugin] Ошибка инициализации MediaSearchAgent: {e}")
        return self._agent

    def can_handle(self, message: str) -> bool:
        """Проверяет, содержит ли сообщение ключевые слова для поиска."""
        if not message:
            return False
            
        message_lower = message.lower()
        for keyword in self.SEARCH_KEYWORDS:
            if keyword in message_lower:
                return True
        return False

    async def _handle(self, message: str, **kwargs) -> AsyncIterator[dict]:
        """Обрабатывает сообщение через LangChain агента."""
        logger.info(f"LangChainMediaPlugin начинает обработку сообщения: {message}")
        yield {'status': '🔍 Запуск LangChain агента...'}

        try:
            final_result = {}
            async for update in self.agent.search_stream(message):
                if 'status' in update:
                    yield {'status': update['status']}
                if 'result' in update:
                    final_result = update['result']

            if final_result:
                formatted_response = self._format_response(final_result)
                yield {'text': formatted_response}
            else:
                yield {'text': 'Не удалось найти информацию по вашему запросу.'}

        except Exception as e:
            logger.error(f"Ошибка в LangChainMediaPlugin: {e}")
            yield {'text': f'⚠️ Ошибка при выполнении поиска: {e}'}

    def _format_response(self, result: dict) -> str:
        """Форматирует результат от агента в HTML для отображения."""
        action = result.get('action', '')
        
        if action == 'player':
            title = result.get('title', 'Видео')
            source = result.get('source', '')
            url = result.get('url', '')
            
            html = f"""
            <div class="media-card">
                <h4>🍿 {title}</h4>
                <p>Источник: {source}</p>
                <button class="btn btn-primary" onclick="window.CosmicPlayer.play('{url}', '{source}', '{title}')">
                    ▶ Смотреть
                </button>
            </div>
            """
            return html
            
        elif action == 'torrent':
            title = result.get('title', 'Торренты')
            torrents = result.get('torrents', [])
            
            html = f"<h4>🧲 Торренты: {title}</h4><div class='list-group'>"
            for t in torrents:
                t_title = t.get('title', 'Торрент')
                t_url = t.get('url', '')
                t_source = t.get('source', '')
                t_size = t.get('size', 'Неизвестно')
                t_seeds = t.get('seeds', '0')
                
                html += f"""
                <div class="list-group-item d-flex justify-content-between align-items-center">
                    <div>
                        <strong>{t_title}</strong><br>
                        <small>Источник: {t_source} | Размер: {t_size} | Сиды: {t_seeds}</small>
                    </div>
                    <button class="btn btn-sm btn-outline-success download-torrent-btn" 
                            data-url="{t_url}" data-source="{t_source}" data-title="{t_title}">
                        Скачать
                    </button>
                </div>
                """
            html += "</div>"
            return html
            
        elif action == 'info':
            title = result.get('title', 'Информация')
            description = result.get('description', '')
            rating = result.get('rating', '')
            year = result.get('year', '')
            
            html = f"""
            <div class="info-card">
                <h4>ℹ️ {title} ({year})</h4>
                <p><strong>Рейтинг:</strong> {rating}</p>
                <p>{description}</p>
            </div>
            """
            return html
            
        else:
            return str(result)
