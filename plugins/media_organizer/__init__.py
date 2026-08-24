# -*- coding: utf-8 -*-
# =============================================================================
# Media Organizer Plugin
# =============================================================================
# Плагин для управления медиатекой с RAG-поиском
#
# Provides:
# - MediaDatabase: SQLite-база данных медиатеки
# - GeminiRAG: Векторный поиск через Gemini Embedding API
# - RAG Functions: Gemini Function Calling инструменты
# =============================================================================

from typing import Any, Dict, List

from plugins.media_organizer.core.database import MediaDatabase
from plugins.media_organizer.core.media_rag import (
    build_media_rag,
    get_media_rag,
    rag_search_tool,
)
from plugins.media_organizer.core.media_rag_functions import (
    search_media,
    get_media_card,
    find_by_exact_title,
    get_random_media,
    rebuild_rag_index,
    get_rag_status,
    get_media_tools,
    dispatch_media_tool_call,
    ask_with_media_rag,
)
from plugins.plugin import BasePlugin
from src.logger import logger

__all__ = [
    # Database
    'MediaDatabase',
    # RAG
    'build_media_rag',
    'get_media_rag',
    'rag_search_tool',
    # Functions
    'search_media',
    'get_media_card',
    'find_by_exact_title',
    'get_random_media',
    'rebuild_rag_index',
    'get_rag_status',
    'get_media_tools',
    'dispatch_media_tool_call',
    'ask_with_media_rag',
    # Plugin
    'plugin',
]


class MediaOrganizerPlugin(BasePlugin):
    """Плагин для управления медиатекой с RAG-поиском."""

    name: str = 'media_organizer'
    title: str = 'Организатор медиатеки'
    description: str = 'Сканирование дисков, аудит файлов, категоризация, устранение дубликатов и обогащение метаданных'
    icon: str = '🎬'
    version: str = '2.1.0'
    category: str = 'media'

    def can_handle(self, message: str) -> bool:
        return False

    def get_manifest(self) -> Dict[str, Any]:
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
                    'id': 'disk',
                    'label': 'Номер или имя диска',
                    'type': 'string',
                    'default': '1',
                    'description': 'Целевой диск для сканирования и каталогизации',
                },
                {
                    'id': 'scan_paths',
                    'label': 'Пути для сканирования',
                    'type': 'list_string',
                    'default': ['E:\\', 'L:\\'],
                    'description': 'Список директорий для поиска медиафайлов',
                },
            ],
            'actions': [
                {
                    'id': 'scan',
                    'label': '🔍 Полное сканирование',
                    'description': 'Сканирует указанные пути и обогащает базу данных через TMDb',
                    'color': 'primary',
                },
                {
                    'id': 'audit',
                    'label': '🗂 Аудит БД',
                    'description': 'Сверяет таблицу media с актуальными файлами на диске',
                    'color': 'warning',
                },
                {
                    'id': 'rebuild_db',
                    'label': '🔧 Консолидация дублей',
                    'description': 'Консолидация дублирующихся записей в базе данных',
                    'color': 'success',
                },
                {
                    'id': 'rebuild_rag',
                    'label': '🧠 Перестроить RAG',
                    'description': 'Полная перегенерация векторных эмбеддингов базы медиатеки',
                    'color': 'info',
                },
                {
                    'id': 'assign_categories',
                    'label': '🏷 Категории торрентам',
                    'description': 'Синхронизирует категории в qBittorrent на основе базы данных',
                    'color': 'secondary',
                },
                {
                    'id': 'rescan_storage',
                    'label': '🔄 Пересканировать диски',
                    'description': 'Обновляет список подключённых накопителей операционной системы',
                    'color': 'dark',
                },
            ],
        }

    async def action_scan(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Запуск сканирования медиатеки."""
        disk = str(params.get('disk', '1'))
        paths = params.get('scan_paths', [])
        if isinstance(paths, str):
            paths = [paths]
        try:
            from plugins.media_organizer.core.media_organizer import MediaOrganizer
            organizer = MediaOrganizer(disk_name=disk)
            res = organizer.scan_and_process(paths=paths) if paths else organizer.scan_and_process()
            return {'success': True, 'result': str(res), 'message': f'Сканирование диска {disk} завершено'}
        except Exception as ex:
            logger.error(f"[MediaOrganizerPlugin] Ошибка сканирования: {ex}")
            return {'success': False, 'message': f'Ошибка сканирования: {ex}'}

    async def action_audit(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Аудит файлов медиатеки."""
        disk = str(params.get('disk', '1'))
        try:
            from plugins.media_organizer.core.media_auditor import MediaAuditor
            auditor = MediaAuditor(disk_name=disk)
            results = auditor.audit()
            return {'success': True, 'result': results, 'message': f'Аудит диска {disk} успешно выполнен'}
        except Exception as ex:
            logger.error(f"[MediaOrganizerPlugin] Ошибка аудита: {ex}")
            return {'success': False, 'message': f'Ошибка аудита: {ex}'}

    async def action_rebuild_db(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Консолидация дублей в базе данных."""
        try:
            from plugins.media_organizer.core.media_rebuild import consolidate_db
            res = consolidate_db()
            return {'success': True, 'result': res, 'message': 'Консолидация базы данных завершена'}
        except Exception as ex:
            logger.error(f"[MediaOrganizerPlugin] Ошибка rebuild_db: {ex}")
            return {'success': False, 'message': f'Ошибка пересборки БД: {ex}'}

    async def action_rebuild_rag(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Перестройка RAG-индекса."""
        try:
            res = rebuild_rag_index()
            return {'success': True, 'result': res, 'message': 'Перестройка RAG-индекса запущена/завершена'}
        except Exception as ex:
            logger.error(f"[MediaOrganizerPlugin] Ошибка rebuild_rag: {ex}")
            return {'success': False, 'message': f'Ошибка RAG: {ex}'}

    async def action_assign_categories(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Назначение категорий торрентам."""
        try:
            from plugins.media_organizer.core.assign_torrents_ids import assign_categories_from_db
            res = assign_categories_from_db()
            return {'success': True, 'result': res, 'message': 'Категории успешно назначены'}
        except Exception as ex:
            logger.error(f"[MediaOrganizerPlugin] Ошибка assign_categories: {ex}")
            return {'success': False, 'message': f'Ошибка назначения категорий: {ex}'}

    async def action_rescan_storage(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Пересканирование подключенных дисков."""
        try:
            from plugins.media_organizer.core.drive_scanner import update_environment_drives
            drives = update_environment_drives()
            return {'success': True, 'drives': drives, 'message': 'Диски обновлены'}
        except Exception as ex:
            logger.error(f"[MediaOrganizerPlugin] Ошибка rescan_storage: {ex}")
            return {'success': False, 'message': f'Ошибка сканирования дисков: {ex}'}

    async def _handle(self, message: str, **kwargs) -> Any:
        return ''


plugin = MediaOrganizerPlugin